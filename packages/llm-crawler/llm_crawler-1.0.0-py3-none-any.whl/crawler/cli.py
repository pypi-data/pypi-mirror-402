"""CLI interface for the web crawler."""

import click
import json
from pathlib import Path
from tqdm import tqdm
from .crawler import WebCrawler
from .content_extractor import ContentExtractor
from .chunker import TextChunker
from .url_manager import URLManager
from .models import CrawlResult, get_iso_timestamp
from . import __version__


@click.command()
@click.argument('start_url', required=False)
@click.option('--depth', '-d', type=int, help='Maximum crawl depth')
@click.option('--chunk-size', '-c', type=int, help='Target chunk size in characters')
@click.option('--output', '-o', type=click.Path(), help='Output JSON file')
@click.option('--rate-limit', '-r', type=float, help='Delay between requests in seconds')
@click.option('--max-pages', '-m', type=int, help='Maximum number of pages to crawl')
@click.option('--same-domain/--no-same-domain', default=None, help='Restrict to same domain and path prefix of start URL')
@click.option('--include-subdomains', is_flag=True, help='Include subdomains when same-domain is enabled')
@click.option('--respect-robots/--ignore-robots', default=None, help='Respect robots.txt directives')
@click.option('--use-sitemap', is_flag=True, default=False, help='Use sitemap from robots.txt for URL discovery')
@click.option('--user-agent', type=str, help='Custom user agent string for robots.txt matching')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--pretty', is_flag=True, help='Pretty-print JSON output')
def main(start_url, depth, chunk_size, output, rate_limit, max_pages, same_domain, include_subdomains, respect_robots, use_sitemap, user_agent, verbose, pretty):
    """
    Crawl a website and prepare content for LLM ingestion.

    Interactive Mode (recommended for beginners):

        crawler

    Command-line Mode:

        crawler https://example.com --depth 2 --output data.json

    The crawler will:

    - Navigate to the start URL and extract content
    - Follow links up to the specified depth
    - Clean and extract main content from each page
    - Split content into optimal chunks for LLM consumption
    - Output everything as JSON ready for pgvector ingestion
    """
    click.echo(f"🕷️  LLM Crawler v{__version__}")
    click.echo()

    # Interactive prompts for missing parameters
    if not start_url:
        start_url = click.prompt('🌐 Enter the URL to crawl', type=str)

    if depth is None:
        depth = click.prompt('📊 Max crawl depth (0=single page, 1=+links, 2=deeper)',
                           type=int, default=1)

    if chunk_size is None:
        chunk_size = click.prompt('📦 Chunk size in characters (~4000 = 1000 tokens)',
                                 type=int, default=4000)

    if output is None:
        output = click.prompt('💾 Output file path',
                            type=str, default='output.json')

    if rate_limit is None:
        rate_limit = click.prompt('⏱️  Rate limit (seconds between requests)',
                                type=float, default=1.0)

    if max_pages is None:
        max_pages_input = click.prompt('📄 Max pages to crawl (leave empty for no limit)',
                                      type=str, default='', show_default=False)
        max_pages = int(max_pages_input) if max_pages_input.strip() else None

    if same_domain is None:
        same_domain = click.confirm('🔒 Restrict crawling to same domain only?', default=True)

    if same_domain and not include_subdomains:
        include_subdomains = click.confirm('🌍 Include subdomains?', default=False)

    if respect_robots is None:
        respect_robots = click.confirm('🤖 Respect robots.txt directives?', default=True)

    if respect_robots and not use_sitemap:
        use_sitemap = click.confirm('🗺️  Use sitemap from robots.txt for URL discovery?', default=False)

    click.echo()
    click.echo('📋 Crawl Configuration:')
    click.echo(f'   • Starting URL: {start_url}')
    click.echo(f'   • Max depth: {depth}')
    click.echo(f'   • Chunk size: {chunk_size} characters (~{chunk_size // 4} tokens)')
    click.echo(f'   • Rate limit: {rate_limit}s between requests')
    if max_pages:
        click.echo(f'   • Max pages: {max_pages}')
    click.echo(f'   • Same domain only: {same_domain}')
    if same_domain and include_subdomains:
        click.echo(f'   • Include subdomains: Yes')
    click.echo(f'   • Respect robots.txt: {respect_robots}')
    if use_sitemap:
        click.echo(f'   • Use sitemap: Yes')
    if user_agent:
        click.echo(f'   • User agent: {user_agent}')
    click.echo(f'   • Output file: {output}')
    click.echo()

    # Initialize components
    url_manager = URLManager(
        start_url=start_url,
        max_depth=depth,
        same_domain=same_domain,
        include_subdomains=include_subdomains,
        respect_robots=respect_robots,
        user_agent=user_agent
    )

    # Show robots.txt info if respecting it
    if respect_robots and verbose:
        disallowed = url_manager.get_disallowed_paths()
        if disallowed:
            click.echo('🤖 Robots.txt disallowed paths:')
            for path in disallowed[:10]:  # Show first 10
                click.echo(f'   • {path}')
            if len(disallowed) > 10:
                click.echo(f'   • ... and {len(disallowed) - 10} more')
            click.echo()
        
        sitemaps = url_manager.get_sitemaps()
        if sitemaps:
            click.echo('🗺️  Sitemaps found:')
            for sitemap in sitemaps:
                click.echo(f'   • {sitemap}')
            click.echo()
        
        robots_delay = url_manager.get_robots_crawl_delay()
        if robots_delay:
            click.echo(f'⏱️  Robots.txt crawl-delay: {robots_delay}s')
            if robots_delay > rate_limit:
                click.echo(f'   ⚠️  Using robots.txt delay ({robots_delay}s) instead of configured rate limit ({rate_limit}s)')
                rate_limit = robots_delay
            click.echo()

    # Apply robots.txt crawl delay if higher than configured rate limit
    if respect_robots:
        robots_delay = url_manager.get_robots_crawl_delay()
        if robots_delay and robots_delay > rate_limit:
            if not verbose:
                click.echo(f'⏱️  Using robots.txt crawl-delay: {robots_delay}s')
            rate_limit = robots_delay

    # Add URLs from sitemap if enabled
    if use_sitemap:
        click.echo('🗺️  Fetching URLs from sitemap...')
        sitemap_urls_added = url_manager.add_sitemap_urls(max_urls=max_pages)
        click.echo(f'   • Added {sitemap_urls_added} URLs from sitemap')
        click.echo()

    content_extractor = ContentExtractor()
    chunker = TextChunker(target_chunk_size=chunk_size)

    # Track crawl stats
    crawl_started_at = get_iso_timestamp()
    pages_crawled = 0
    all_chunks = []

    # Start crawling
    with WebCrawler(rate_limit=rate_limit) as crawler:
        # Progress bar - set total only if max_pages is provided
        total = max_pages if max_pages else None
        with tqdm(desc="Crawling pages", unit="page", total=total) as pbar:
            while url_manager.has_urls():
                # Check max pages limit
                if max_pages and pages_crawled >= max_pages:
                    if verbose:
                        click.echo(f"\n✋ Reached max pages limit ({max_pages})")
                    break

                # Get next URL
                next_url_data = url_manager.get_next_url()
                if not next_url_data:
                    break

                url, current_depth = next_url_data

                # Truncate long URLs for display
                display_url = url if len(url) <= 60 else url[:57] + "..."

                # Update progress bar description with current URL
                if max_pages:
                    # Show just the domain/path when total is visible
                    pbar.set_description(f"Crawling {display_url}")
                else:
                    # Show more context when no total
                    pbar.set_description(f"Crawling: {display_url}")

                if verbose:
                    click.echo(f"\n🔍 Crawling: {url} (depth: {current_depth})")

                # Crawl the page
                html, links, metadata, success = crawler.crawl(url, current_depth)

                if not success or not html:
                    if verbose:
                        click.echo(f"  ❌ Failed to crawl {url}")
                    continue

                # Extract content
                try:
                    content_data = content_extractor.extract_content(html, url)
                    text = content_data['text']
                    page_metadata_dict = content_data['metadata']
                    headings = content_data['headings']

                    if not text or len(text.strip()) < 100:
                        if verbose:
                            click.echo(f"  ⚠️  Insufficient content extracted from {url}")
                        continue

                    # Update metadata with extracted info
                    metadata.title = page_metadata_dict['title']
                    metadata.description = page_metadata_dict['description']
                    metadata.canonical_url = page_metadata_dict['canonical_url']

                    # Chunk the text
                    chunks = chunker.chunk_text(text, metadata, headings)

                    if verbose:
                        click.echo(f"  ✅ Extracted {len(text)} chars, created {len(chunks)} chunks")

                    all_chunks.extend(chunks)
                    pages_crawled += 1

                    # Update progress bar only on successful crawl
                    pbar.update(1)

                    # Add discovered links to queue
                    if current_depth < depth:
                        url_manager.add_urls(links, url, current_depth)

                except Exception as e:
                    if verbose:
                        click.echo(f"  ❌ Error processing {url}: {str(e)}")

    # Create final result
    crawl_completed_at = get_iso_timestamp()

    result = CrawlResult(
        start_url=start_url,
        crawl_started_at=crawl_started_at,
        crawl_completed_at=crawl_completed_at,
        max_depth=depth,
        total_pages_crawled=pages_crawled,
        total_chunks=len(all_chunks),
        crawler_version=__version__,
        chunks=all_chunks
    )

    # Write output
    output_path = Path(output)
    
    # If output is a directory, create a filename based on the start URL
    if output_path.is_dir() or (not output_path.suffix and not output_path.exists()):
        # Parse domain from start URL for filename
        from urllib.parse import urlparse
        parsed_url = urlparse(start_url)
        domain_name = parsed_url.netloc.replace('.', '_').replace(':', '_')
        # Include path in filename if present
        path_part = parsed_url.path.strip('/').replace('/', '_')[:50] if parsed_url.path.strip('/') else ''
        filename = f"{domain_name}_{path_part}.json" if path_part else f"{domain_name}.json"
        
        # Ensure directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        output_path = output_path / filename
        click.echo(f"📁 Output directory detected, saving to: {output_path}")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        else:
            json.dump(result.to_dict(), f, ensure_ascii=False)

    click.echo()
    click.echo("✨ Crawl completed!")
    click.echo(f"📊 Statistics:")
    click.echo(f"   • Pages crawled: {pages_crawled}")
    click.echo(f"   • Total chunks: {len(all_chunks)}")
    click.echo(f"   • Output file: {output_path.absolute()}")

    # Show sample chunk
    if all_chunks and verbose:
        click.echo()
        click.echo("📝 Sample chunk:")
        sample = all_chunks[0]
        click.echo(f"   • URL: {sample.page_metadata.url}")
        click.echo(f"   • Title: {sample.page_metadata.title}")
        click.echo(f"   • Chunk size: {sample.char_count} chars ({sample.estimated_tokens} tokens)")
        click.echo(f"   • Preview: {sample.content[:200]}...")


if __name__ == '__main__':
    main()
