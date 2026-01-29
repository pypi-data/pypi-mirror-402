"""CLI interface for the web crawler."""

import asyncio
import click
import json
from pathlib import Path
from tqdm import tqdm
from typing import Optional

from .crawler import WebCrawler
from .fast_crawler import HybridCrawler, CrawlResponse
from .content_extractor import ContentExtractor
from .chunker import TextChunker
from .url_manager import URLManager, AsyncURLManager
from .checkpoint import CheckpointManager, CheckpointData
from .models import CrawlResult, Chunk, get_iso_timestamp
from . import __version__


def run_sync_crawler(
    url_manager: URLManager,
    content_extractor: ContentExtractor,
    chunker: TextChunker,
    rate_limit: float,
    max_pages: Optional[int],
    depth: int,
    verbose: bool,
    checkpoint_manager: Optional[CheckpointManager] = None,
    checkpoint_data: Optional[CheckpointData] = None
) -> tuple:
    """Run the synchronous (Playwright-only) crawler."""
    pages_crawled = checkpoint_data.pages_crawled if checkpoint_data else 0
    all_chunks = checkpoint_manager.restore_chunks(checkpoint_data.chunks) if checkpoint_data and checkpoint_data.chunks else []

    with WebCrawler(rate_limit=rate_limit) as crawler:
        total = max_pages if max_pages else None
        with tqdm(desc="Crawling pages", unit="page", total=total, initial=pages_crawled) as pbar:
            while url_manager.has_urls():
                if max_pages and pages_crawled >= max_pages:
                    if verbose:
                        click.echo(f"\n✋ Reached max pages limit ({max_pages})")
                    break

                next_url_data = url_manager.get_next_url()
                if not next_url_data:
                    break

                url, current_depth = next_url_data
                display_url = url if len(url) <= 60 else url[:57] + "..."

                if max_pages:
                    pbar.set_description(f"Crawling {display_url}")
                else:
                    pbar.set_description(f"Crawling: {display_url}")

                if verbose:
                    click.echo(f"\n🔍 Crawling: {url} (depth: {current_depth})")

                html, links, metadata, success = crawler.crawl(url, current_depth)

                if not success or not html:
                    if verbose:
                        click.echo(f"  ❌ Failed to crawl {url}")
                    continue

                try:
                    content_data = content_extractor.extract_content(html, url)
                    text = content_data['text']
                    page_metadata_dict = content_data['metadata']
                    headings = content_data['headings']

                    if not text or len(text.strip()) < 100:
                        if verbose:
                            click.echo(f"  ⚠️  Insufficient content extracted from {url}")
                        continue

                    metadata.title = page_metadata_dict['title']
                    metadata.description = page_metadata_dict['description']
                    metadata.canonical_url = page_metadata_dict['canonical_url']

                    chunks = chunker.chunk_text(text, metadata, headings)

                    if verbose:
                        click.echo(f"  ✅ Extracted {len(text)} chars, created {len(chunks)} chunks")

                    all_chunks.extend(chunks)
                    pages_crawled += 1
                    pbar.update(1)

                    if current_depth < depth:
                        url_manager.add_urls(links, url, current_depth)

                    # Save checkpoint
                    if checkpoint_manager and checkpoint_data:
                        checkpoint_data = checkpoint_manager.update_checkpoint(
                            checkpoint_data,
                            visited=url_manager.visited,
                            pending=url_manager.get_pending_urls(),
                            chunks=all_chunks,
                            pages_crawled=pages_crawled
                        )
                        checkpoint_manager.save_checkpoint(checkpoint_data)

                except Exception as e:
                    if verbose:
                        click.echo(f"  ❌ Error processing {url}: {str(e)}")

    return pages_crawled, all_chunks


async def run_async_crawler(
    url_manager: URLManager,
    content_extractor: ContentExtractor,
    chunker: TextChunker,
    rate_limit: float,
    max_pages: Optional[int],
    depth: int,
    verbose: bool,
    concurrency: int,
    use_fast: bool,
    checkpoint_manager: Optional[CheckpointManager] = None,
    checkpoint_data: Optional[CheckpointData] = None
) -> tuple:
    """Run the async (fast httpx + Playwright fallback) crawler."""
    pages_crawled = checkpoint_data.pages_crawled if checkpoint_data else 0
    all_chunks = checkpoint_manager.restore_chunks(checkpoint_data.chunks) if checkpoint_data and checkpoint_data.chunks else []

    async_url_manager = AsyncURLManager(url_manager)

    # Restore state if resuming
    if checkpoint_data and checkpoint_data.pending:
        await async_url_manager.restore_state(
            checkpoint_data.visited,
            checkpoint_data.pending
        )

    async with HybridCrawler(
        concurrency=concurrency,
        timeout=30.0,
        rate_limit=rate_limit / concurrency,  # Distribute rate limit across workers
        playwright_rate_limit=rate_limit,
        use_fast=use_fast
    ) as crawler:
        total = max_pages if max_pages else None
        with tqdm(desc="Crawling pages", unit="page", total=total, initial=pages_crawled) as pbar:
            while await async_url_manager.has_urls():
                if max_pages and pages_crawled >= max_pages:
                    if verbose:
                        click.echo(f"\n✋ Reached max pages limit ({max_pages})")
                    break

                # Get batch of URLs
                batch_size = min(concurrency, (max_pages - pages_crawled) if max_pages else concurrency)
                urls_to_crawl = await async_url_manager.get_next_urls(batch_size)
                
                if not urls_to_crawl:
                    break

                if verbose:
                    click.echo(f"\n🔍 Crawling batch of {len(urls_to_crawl)} URLs")

                # Crawl batch
                results = await crawler.crawl_batch(urls_to_crawl)

                # Process results
                url_link_pairs = []
                
                for url, current_depth, response in results:
                    if max_pages and pages_crawled >= max_pages:
                        break

                    if not response.success or not response.html:
                        if verbose:
                            click.echo(f"  ❌ Failed to crawl {url}")
                        continue

                    try:
                        content_data = content_extractor.extract_content(response.html, url)
                        text = content_data['text']
                        page_metadata_dict = content_data['metadata']
                        headings = content_data['headings']

                        if not text or len(text.strip()) < 100:
                            if verbose:
                                click.echo(f"  ⚠️  Insufficient content extracted from {url}")
                            continue

                        response.metadata.title = page_metadata_dict['title']
                        response.metadata.description = page_metadata_dict['description']
                        response.metadata.canonical_url = page_metadata_dict['canonical_url']

                        chunks = chunker.chunk_text(text, response.metadata, headings)

                        if verbose:
                            click.echo(f"  ✅ {url}: {len(text)} chars, {len(chunks)} chunks")

                        all_chunks.extend(chunks)
                        pages_crawled += 1
                        pbar.update(1)

                        # Collect links for batch adding
                        if current_depth < depth:
                            url_link_pairs.append((url, response.links, current_depth))

                    except Exception as e:
                        if verbose:
                            click.echo(f"  ❌ Error processing {url}: {str(e)}")

                # Add discovered links in batch
                if url_link_pairs:
                    await async_url_manager.add_urls_batch(url_link_pairs)

                # Save checkpoint
                if checkpoint_manager and checkpoint_data:
                    pending = await async_url_manager.get_pending_urls()
                    checkpoint_data = checkpoint_manager.update_checkpoint(
                        checkpoint_data,
                        visited=url_manager.visited,
                        pending=pending,
                        chunks=all_chunks,
                        pages_crawled=pages_crawled
                    )
                    checkpoint_manager.save_checkpoint(checkpoint_data)

    return pages_crawled, all_chunks


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
# New performance options
@click.option('--concurrency', '-j', type=int, default=5, help='Number of parallel workers (default: 5)')
@click.option('--fast/--no-fast', default=True, help='Use fast httpx crawler with Playwright fallback (default: true)')
@click.option('--resume', is_flag=True, help='Resume from checkpoint if available')
@click.option('--checkpoint-interval', type=int, default=50, help='Save checkpoint every N pages (default: 50)')
@click.option('--checkpoint-file', type=click.Path(), help='Custom checkpoint file path')
def main(
    start_url, depth, chunk_size, output, rate_limit, max_pages, same_domain,
    include_subdomains, respect_robots, use_sitemap, user_agent, verbose, pretty,
    concurrency, fast, resume, checkpoint_interval, checkpoint_file
):
    """
    Crawl a website and prepare content for LLM ingestion.

    Interactive Mode (recommended for beginners):

        crawler

    Command-line Mode:

        crawler https://example.com --depth 2 --output data.json

    Fast Mode (default):

        crawler https://example.com -j 5 --fast

    Resume from checkpoint:

        crawler https://example.com --resume

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

    # Initialize checkpoint manager
    checkpoint_manager = CheckpointManager(
        checkpoint_file=checkpoint_file,
        checkpoint_interval=checkpoint_interval
    )

    # Check for existing checkpoint if resume is enabled
    checkpoint_data = None
    if resume:
        existing_checkpoint = checkpoint_manager.find_existing_checkpoint(start_url)
        if existing_checkpoint:
            checkpoint_data = checkpoint_manager.load_checkpoint(existing_checkpoint)
            if checkpoint_data:
                click.echo(f'📋 Resuming from checkpoint:')
                click.echo(f'   • Pages already crawled: {checkpoint_data.pages_crawled}')
                click.echo(f'   • Chunks collected: {len(checkpoint_data.chunks)}')
                click.echo(f'   • Pending URLs: {len(checkpoint_data.pending)}')
                click.echo(f'   • Last checkpoint: {checkpoint_data.last_checkpoint_at}')
                click.echo()
                
                # Restore configuration from checkpoint
                depth = checkpoint_data.max_depth
                chunk_size = checkpoint_data.chunk_size
                same_domain = checkpoint_data.same_domain
                include_subdomains = checkpoint_data.include_subdomains
                respect_robots = checkpoint_data.respect_robots
                rate_limit = checkpoint_data.rate_limit
                concurrency = checkpoint_data.concurrency
                fast = checkpoint_data.use_fast
            else:
                click.echo('⚠️  Could not load checkpoint, starting fresh')
        else:
            click.echo('ℹ️  No checkpoint found, starting fresh')

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
    click.echo(f'   • Concurrency: {concurrency} workers')
    click.echo(f'   • Fast mode: {"Yes (httpx + Playwright fallback)" if fast else "No (Playwright only)"}')
    click.echo(f'   • Checkpoint interval: Every {checkpoint_interval} pages')
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

    # Restore URL manager state from checkpoint
    if checkpoint_data and checkpoint_data.visited:
        url_manager.restore_state(checkpoint_data.visited, checkpoint_data.pending)

    # Show robots.txt info if respecting it
    if respect_robots and verbose:
        disallowed = url_manager.get_disallowed_paths()
        if disallowed:
            click.echo('🤖 Robots.txt disallowed paths:')
            for path in disallowed[:10]:
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

    # Add URLs from sitemap if enabled (only if not resuming)
    if use_sitemap and not checkpoint_data:
        click.echo('🗺️  Fetching URLs from sitemap...')
        sitemap_urls_added = url_manager.add_sitemap_urls(max_urls=max_pages)
        click.echo(f'   • Added {sitemap_urls_added} URLs from sitemap')
        click.echo()

    content_extractor = ContentExtractor()
    chunker = TextChunker(target_chunk_size=chunk_size)

    # Create checkpoint data if not resuming
    crawl_started_at = checkpoint_data.crawl_started_at if checkpoint_data else get_iso_timestamp()
    
    if not checkpoint_data:
        checkpoint_data = checkpoint_manager.create_checkpoint_data(
            start_url=start_url,
            crawl_started_at=crawl_started_at,
            max_depth=depth,
            chunk_size=chunk_size,
            same_domain=same_domain,
            include_subdomains=include_subdomains,
            respect_robots=respect_robots,
            rate_limit=rate_limit,
            concurrency=concurrency,
            use_fast=fast
        )

    # Run the appropriate crawler
    if fast and concurrency > 1:
        # Use async crawler for parallel processing
        pages_crawled, all_chunks = asyncio.run(run_async_crawler(
            url_manager=url_manager,
            content_extractor=content_extractor,
            chunker=chunker,
            rate_limit=rate_limit,
            max_pages=max_pages,
            depth=depth,
            verbose=verbose,
            concurrency=concurrency,
            use_fast=fast,
            checkpoint_manager=checkpoint_manager,
            checkpoint_data=checkpoint_data
        ))
    else:
        # Use sync crawler (Playwright only, sequential)
        pages_crawled, all_chunks = run_sync_crawler(
            url_manager=url_manager,
            content_extractor=content_extractor,
            chunker=chunker,
            rate_limit=rate_limit,
            max_pages=max_pages,
            depth=depth,
            verbose=verbose,
            checkpoint_manager=checkpoint_manager,
            checkpoint_data=checkpoint_data
        )

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
        from urllib.parse import urlparse
        parsed_url = urlparse(start_url)
        domain_name = parsed_url.netloc.replace('.', '_').replace(':', '_')
        path_part = parsed_url.path.strip('/').replace('/', '_')[:50] if parsed_url.path.strip('/') else ''
        filename = f"{domain_name}_{path_part}.json" if path_part else f"{domain_name}.json"
        
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

    # Delete checkpoint on successful completion
    checkpoint_manager.delete_checkpoint(start_url)

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
