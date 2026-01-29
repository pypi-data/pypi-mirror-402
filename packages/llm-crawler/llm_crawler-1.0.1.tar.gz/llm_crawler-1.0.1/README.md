# LLM Web Crawler

A powerful command-line tool for crawling websites and preparing content for LLM ingestion and vector databases (like pgvector).

## Features

- 🕷️ **Smart Crawling**: Configurable depth, rate limiting, same-domain restriction
- 🧹 **Content Cleaning**: Removes navigation, ads, boilerplate - keeps only main content
- ✂️ **Intelligent Chunking**: Splits text into ~1000 token chunks with sentence boundary preservation
- 📦 **LLM-Ready Output**: JSON format optimized for pgvector and other vector databases
- 🚀 **JavaScript Support**: Uses Playwright for JavaScript-heavy websites
- 📊 **Rich Metadata**: Extracts titles, descriptions, headings, and canonical URLs

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Install Dependencies

```bash
# Install the package in development mode
pip install -e .

# Install Playwright browsers
playwright install chromium
```

## Usage

### Basic Usage

```bash
# Crawl a single page
crawler https://example.com

# Crawl with depth 2
crawler https://example.com --depth 2 --output data.json
```

### Advanced Options

```bash
# Custom chunk size
crawler https://example.com --chunk-size 5000

# Rate limiting (2 seconds between requests)
crawler https://example.com --depth 3 --rate-limit 2.0

# Limit maximum pages
crawler https://example.com --depth 5 --max-pages 100

# Include subdomains
crawler https://example.com --depth 2 --include-subdomains

# Verbose output
crawler https://example.com --depth 2 --verbose

# Pretty JSON output
crawler https://example.com --output data.json --pretty
```

## Output Format

The crawler generates JSON output optimized for vector database ingestion:

```json
{
  "crawl_metadata": {
    "start_url": "https://example.com",
    "crawl_started_at": "2026-01-16T19:45:00Z",
    "crawl_completed_at": "2026-01-16T19:47:30Z",
    "max_depth": 2,
    "total_pages_crawled": 15,
    "total_chunks": 127,
    "crawler_version": "1.0.0"
  },
  "chunks": [
    {
      "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
      "content": "This is the extracted text content...",
      "char_count": 3847,
      "estimated_tokens": 962,
      "position": 0,
      "heading_context": "Introduction > Getting Started",
      "page_metadata": {
        "url": "https://example.com/docs/intro",
        "canonical_url": "https://example.com/docs/intro",
        "title": "Getting Started - Documentation",
        "description": "Learn how to get started",
        "crawled_at": "2026-01-16T19:45:23Z",
        "depth": 1,
        "status_code": 200
      }
    }
  ]
}
```

## Integration with pgvector

### Creating a Table

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),  -- For OpenAI embeddings
    url TEXT,
    title TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

### Loading Data

```python
import json
import psycopg2
from openai import OpenAI

# Load crawler output
with open('output.json') as f:
    data = json.load(f)

# Connect to database
conn = psycopg2.connect("your_connection_string")
cur = conn.cursor()

# Generate embeddings and insert
client = OpenAI()

for chunk in data['chunks']:
    # Generate embedding
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunk['content']
    )
    embedding = response.data[0].embedding

    # Insert into database
    cur.execute("""
        INSERT INTO documents (chunk_id, content, embedding, url, title, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        chunk['chunk_id'],
        chunk['content'],
        embedding,
        chunk['page_metadata']['url'],
        chunk['page_metadata']['title'],
        json.dumps(chunk['page_metadata'])
    ))

conn.commit()
```

## Command-Line Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--depth` | `-d` | 1 | Maximum crawl depth |
| `--chunk-size` | `-c` | 4000 | Target chunk size in characters |
| `--output` | `-o` | output.json | Output JSON file path |
| `--rate-limit` | `-r` | 1.0 | Delay between requests (seconds) |
| `--max-pages` | `-m` | None | Maximum pages to crawl |
| `--same-domain` | | True | Restrict to same domain |
| `--include-subdomains` | | False | Include subdomains |
| `--respect-robots` | | True | Respect robots.txt directives |
| `--use-sitemap` | | False | Use sitemap from robots.txt for URL discovery |
| `--user-agent` | | LLMCrawler/1.0 | Custom user agent for robots.txt matching |
| `--verbose` | `-v` | False | Show detailed progress |
| `--pretty` | | False | Pretty-print JSON output |

## Robots.txt Support

The crawler respects robots.txt directives by default, ensuring ethical crawling behavior.

### Features

- **Automatic Parsing**: Fetches and parses robots.txt from target domains
- **Disallow Rules**: Respects `Disallow` directives for your user agent
- **Crawl Delay**: Honors `Crawl-delay` directives (overrides `--rate-limit` if higher)
- **Sitemap Discovery**: Extracts sitemap URLs for comprehensive crawling
- **Custom User Agent**: Match specific rules with `--user-agent`

### Example: Respecting robots.txt

```bash
# Crawl while respecting robots.txt (default behavior)
crawler https://shopify.dev/docs --depth 2 --verbose

# Use sitemap for URL discovery
crawler https://shopify.dev --use-sitemap --max-pages 100

# Ignore robots.txt (use responsibly)
crawler https://example.com --ignore-robots

# Custom user agent for specific rules
crawler https://example.com --user-agent "MyBot/1.0"
```

### Example robots.txt handling

For a robots.txt like:

```
User-agent: *
Disallow: /beta/
Disallow: /api/shipping-partner-platform/
Sitemap: https://example.com/sitemap.xml
Crawl-delay: 2
```

The crawler will:
1. Skip URLs matching `/beta/` and `/api/shipping-partner-platform/`
2. Use 2-second delay between requests (if higher than `--rate-limit`)
3. Optionally fetch URLs from the sitemap with `--use-sitemap`

## How It Works

### 1. URL Management
- Maintains a queue of URLs to visit
- Tracks depth for each URL
- Deduplicates URLs (normalizes before comparison)
- Respects domain restrictions

### 2. Content Extraction
- Uses Playwright for JavaScript rendering
- Employs Trafilatura for main content extraction
- Removes navigation, ads, footers, and boilerplate
- Extracts metadata (title, description, canonical URL)
- Preserves document structure (headings)

### 3. Smart Chunking
- Splits text at sentence boundaries
- Maintains ~1000 token chunks (4000 characters)
- Adds overlap between chunks for context
- Preserves heading hierarchy
- Estimates token count (1 token ≈ 4 characters)

### 4. Rate Limiting
- Enforces delay between requests
- Prevents overloading target servers
- Configurable via `--rate-limit` option

## Architecture

```
crawler/
├── src/crawler/
│   ├── cli.py              # CLI interface
│   ├── crawler.py          # Playwright-based crawler
│   ├── content_extractor.py # Content cleaning & extraction
│   ├── chunker.py          # Smart text chunking
│   ├── url_manager.py      # URL queue management
│   └── models.py           # Data models
└── tests/                  # Test suite
```

## Examples

### Crawl Documentation Site

```bash
crawler https://docs.python.org/3/ \
    --depth 2 \
    --chunk-size 4000 \
    --output python_docs.json \
    --rate-limit 1.5 \
    --verbose
```

### Crawl Blog (Single Domain)

```bash
crawler https://blog.example.com \
    --depth 3 \
    --max-pages 50 \
    --same-domain \
    --output blog_content.json
```

### Quick Single-Page Crawl

```bash
crawler https://example.com/article \
    --depth 0 \
    --output article.json \
    --pretty
```

## Troubleshooting

### Playwright Installation Issues

```bash
# Reinstall Playwright browsers
playwright install --force chromium
```

### Rate Limit Errors

Increase the `--rate-limit` value:

```bash
crawler https://example.com --rate-limit 3.0
```

### JavaScript-Heavy Sites

The crawler uses Playwright by default, which handles JavaScript. If you encounter issues:

1. Increase timeout (modify `timeout` in `WebCrawler`)
2. Add longer wait times for dynamic content

### Memory Issues

For large crawls, limit pages:

```bash
crawler https://example.com --depth 5 --max-pages 1000
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=crawler tests/
```

### Code Formatting

```bash
# Format code
black src/

# Lint code
ruff check src/
```

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or PR.

## Support

For issues or questions, please open a GitHub issue.
