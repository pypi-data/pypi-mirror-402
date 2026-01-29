"""Fast async HTTP crawler using httpx with Playwright fallback."""

import asyncio
from typing import List, Optional, Tuple, Set
from dataclasses import dataclass
import httpx
from bs4 import BeautifulSoup

from .models import CrawlMetadata, get_iso_timestamp


@dataclass
class CrawlResponse:
    """Response from a crawl operation."""
    html: Optional[str]
    links: List[str]
    metadata: Optional[CrawlMetadata]
    success: bool
    needs_js: bool = False


class FastCrawler:
    """Fast async HTTP crawler with automatic JS detection and Playwright fallback."""

    # Indicators that a page requires JavaScript rendering
    JS_INDICATORS = [
        'Please enable JavaScript',
        'JavaScript is required',
        'This site requires JavaScript',
        'You need to enable JavaScript',
        '<noscript>',
        'React.render',
        'Vue.createApp',
        '__NEXT_DATA__',  # Next.js apps often work without JS
        'window.__INITIAL_STATE__',
    ]

    # Minimum content length to consider a page successfully loaded
    MIN_CONTENT_LENGTH = 200

    def __init__(
        self,
        concurrency: int = 5,
        timeout: float = 30.0,
        rate_limit: float = 0.1,
        user_agent: str = None
    ):
        """
        Initialize fast crawler.

        Args:
            concurrency: Maximum number of concurrent requests
            timeout: Request timeout in seconds
            rate_limit: Minimum delay between requests in seconds
            user_agent: Custom user agent string
        """
        self.concurrency = concurrency
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.user_agent = user_agent or (
            "Mozilla/5.0 (compatible; LLM-Crawler/1.0; +https://github.com/Legolasan/llm-crawler)"
        )
        
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time: float = 0
        self._request_lock = asyncio.Lock()
        
        # Track URLs that need JavaScript rendering
        self._js_required_urls: Set[str] = set()

    async def __aenter__(self):
        """Async context manager entry."""
        self._semaphore = asyncio.Semaphore(self.concurrency)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            headers={
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            },
            limits=httpx.Limits(
                max_connections=self.concurrency * 2,
                max_keepalive_connections=self.concurrency
            )
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def _respect_rate_limit(self):
        """Enforce rate limiting between requests."""
        async with self._request_lock:
            import time
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.rate_limit:
                await asyncio.sleep(self.rate_limit - time_since_last)
            
            self._last_request_time = time.time()

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                links.append(href)

        return links

    def _needs_javascript(self, html: str) -> bool:
        """
        Detect if page requires JavaScript rendering.

        Args:
            html: HTML content

        Returns:
            True if JavaScript rendering appears needed
        """
        if not html:
            return True
        
        # Check for JS requirement indicators
        html_lower = html.lower()
        for indicator in self.JS_INDICATORS:
            if indicator.lower() in html_lower:
                # __NEXT_DATA__ presence actually means content is likely server-rendered
                if indicator == '__NEXT_DATA__':
                    return False
                return True
        
        # Check if content is too short (might be a loading page)
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script and style elements
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        
        text = soup.get_text(strip=True)
        if len(text) < self.MIN_CONTENT_LENGTH:
            return True
        
        return False

    async def crawl_url(self, url: str, depth: int) -> CrawlResponse:
        """
        Crawl a single URL.

        Args:
            url: URL to crawl
            depth: Current crawl depth

        Returns:
            CrawlResponse with results
        """
        async with self._semaphore:
            await self._respect_rate_limit()
            
            try:
                response = await self._client.get(url)
                
                if response.status_code >= 400:
                    return CrawlResponse(
                        html=None,
                        links=[],
                        metadata=None,
                        success=False
                    )
                
                html = response.text
                
                # Check if page needs JavaScript
                if self._needs_javascript(html):
                    self._js_required_urls.add(url)
                    return CrawlResponse(
                        html=html,
                        links=[],
                        metadata=None,
                        success=False,
                        needs_js=True
                    )
                
                # Extract links
                links = self._extract_links(html, url)
                
                # Create metadata
                metadata = CrawlMetadata(
                    url=url,
                    canonical_url=url,
                    title='',
                    description=None,
                    crawled_at=get_iso_timestamp(),
                    depth=depth,
                    status_code=response.status_code
                )
                
                return CrawlResponse(
                    html=html,
                    links=links,
                    metadata=metadata,
                    success=True
                )
                
            except httpx.TimeoutException:
                return CrawlResponse(
                    html=None,
                    links=[],
                    metadata=None,
                    success=False
                )
            except Exception as e:
                return CrawlResponse(
                    html=None,
                    links=[],
                    metadata=None,
                    success=False
                )

    async def crawl_batch(
        self,
        urls: List[Tuple[str, int]]
    ) -> List[Tuple[str, int, CrawlResponse]]:
        """
        Crawl a batch of URLs concurrently.

        Args:
            urls: List of (url, depth) tuples

        Returns:
            List of (url, depth, CrawlResponse) tuples
        """
        tasks = [self.crawl_url(url, depth) for url, depth in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for (url, depth), response in zip(urls, responses):
            if isinstance(response, Exception):
                response = CrawlResponse(
                    html=None,
                    links=[],
                    metadata=None,
                    success=False
                )
            results.append((url, depth, response))
        
        return results

    def get_js_required_urls(self) -> Set[str]:
        """Get URLs that require JavaScript rendering."""
        return self._js_required_urls.copy()


class PlaywrightFallback:
    """Playwright fallback for JavaScript-rendered pages."""

    def __init__(self, rate_limit: float = 1.0, timeout: int = 30000):
        """
        Initialize Playwright fallback.

        Args:
            rate_limit: Delay between requests in seconds
            timeout: Page load timeout in milliseconds
        """
        self.rate_limit = rate_limit
        self.timeout = timeout
        self._playwright = None
        self._browser = None
        self._last_request_time = 0

    async def __aenter__(self):
        """Async context manager entry."""
        from playwright.async_api import async_playwright
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _respect_rate_limit(self):
        """Enforce rate limiting between requests."""
        import time
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit:
            await asyncio.sleep(self.rate_limit - time_since_last)
        
        self._last_request_time = time.time()

    def _extract_links(self, html: str) -> List[str]:
        """Extract links from HTML."""
        soup = BeautifulSoup(html, 'lxml')
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                links.append(href)
        return links

    async def crawl_url(self, url: str, depth: int) -> CrawlResponse:
        """
        Crawl a URL using Playwright.

        Args:
            url: URL to crawl
            depth: Current crawl depth

        Returns:
            CrawlResponse with results
        """
        await self._respect_rate_limit()
        
        try:
            page = await self._browser.new_page()
            page.set_default_timeout(self.timeout)
            
            response = await page.goto(url, wait_until='networkidle')
            
            if not response:
                await page.close()
                return CrawlResponse(
                    html=None,
                    links=[],
                    metadata=None,
                    success=False
                )
            
            # Wait for dynamic content
            await page.wait_for_timeout(1000)
            
            html = await page.content()
            links = self._extract_links(html)
            
            metadata = CrawlMetadata(
                url=url,
                canonical_url=url,
                title='',
                description=None,
                crawled_at=get_iso_timestamp(),
                depth=depth,
                status_code=response.status
            )
            
            await page.close()
            
            return CrawlResponse(
                html=html,
                links=links,
                metadata=metadata,
                success=True
            )
            
        except Exception as e:
            return CrawlResponse(
                html=None,
                links=[],
                metadata=None,
                success=False
            )

    async def crawl_batch(
        self,
        urls: List[Tuple[str, int]]
    ) -> List[Tuple[str, int, CrawlResponse]]:
        """
        Crawl URLs sequentially with Playwright (no parallelism for stability).

        Args:
            urls: List of (url, depth) tuples

        Returns:
            List of (url, depth, CrawlResponse) tuples
        """
        results = []
        for url, depth in urls:
            response = await self.crawl_url(url, depth)
            results.append((url, depth, response))
        return results


class HybridCrawler:
    """Hybrid crawler that uses httpx by default with Playwright fallback."""

    def __init__(
        self,
        concurrency: int = 5,
        timeout: float = 30.0,
        rate_limit: float = 0.1,
        playwright_rate_limit: float = 1.0,
        user_agent: str = None,
        use_fast: bool = True
    ):
        """
        Initialize hybrid crawler.

        Args:
            concurrency: Maximum concurrent requests for fast crawler
            timeout: Request timeout in seconds
            rate_limit: Rate limit for fast crawler
            playwright_rate_limit: Rate limit for Playwright fallback
            user_agent: Custom user agent
            use_fast: Whether to use fast httpx crawler (False = Playwright only)
        """
        self.concurrency = concurrency
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.playwright_rate_limit = playwright_rate_limit
        self.user_agent = user_agent
        self.use_fast = use_fast
        
        self._fast_crawler: Optional[FastCrawler] = None
        self._playwright_fallback: Optional[PlaywrightFallback] = None

    async def __aenter__(self):
        """Async context manager entry."""
        if self.use_fast:
            self._fast_crawler = FastCrawler(
                concurrency=self.concurrency,
                timeout=self.timeout,
                rate_limit=self.rate_limit,
                user_agent=self.user_agent
            )
            await self._fast_crawler.__aenter__()
        
        # Playwright fallback is lazy-loaded when needed
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._fast_crawler:
            await self._fast_crawler.__aexit__(exc_type, exc_val, exc_tb)
        if self._playwright_fallback:
            await self._playwright_fallback.__aexit__(exc_type, exc_val, exc_tb)

    async def _ensure_playwright(self):
        """Ensure Playwright fallback is initialized."""
        if not self._playwright_fallback:
            self._playwright_fallback = PlaywrightFallback(
                rate_limit=self.playwright_rate_limit,
                timeout=int(self.timeout * 1000)
            )
            await self._playwright_fallback.__aenter__()

    async def crawl_url(self, url: str, depth: int) -> CrawlResponse:
        """
        Crawl a single URL with automatic fallback.

        Args:
            url: URL to crawl
            depth: Current depth

        Returns:
            CrawlResponse with results
        """
        if not self.use_fast:
            await self._ensure_playwright()
            return await self._playwright_fallback.crawl_url(url, depth)
        
        # Try fast crawler first
        response = await self._fast_crawler.crawl_url(url, depth)
        
        # Fallback to Playwright if JS is needed
        if response.needs_js:
            await self._ensure_playwright()
            return await self._playwright_fallback.crawl_url(url, depth)
        
        return response

    async def crawl_batch(
        self,
        urls: List[Tuple[str, int]]
    ) -> List[Tuple[str, int, CrawlResponse]]:
        """
        Crawl a batch of URLs with automatic fallback.

        Args:
            urls: List of (url, depth) tuples

        Returns:
            List of (url, depth, CrawlResponse) tuples
        """
        if not self.use_fast:
            await self._ensure_playwright()
            return await self._playwright_fallback.crawl_batch(urls)
        
        # Try fast crawler
        results = await self._fast_crawler.crawl_batch(urls)
        
        # Collect URLs that need JS fallback
        js_needed = [
            (url, depth) for url, depth, resp in results if resp.needs_js
        ]
        
        if js_needed:
            await self._ensure_playwright()
            fallback_results = await self._playwright_fallback.crawl_batch(js_needed)
            
            # Merge results
            fallback_map = {url: (depth, resp) for url, depth, resp in fallback_results}
            
            final_results = []
            for url, depth, resp in results:
                if resp.needs_js and url in fallback_map:
                    _, new_resp = fallback_map[url]
                    final_results.append((url, depth, new_resp))
                else:
                    final_results.append((url, depth, resp))
            
            return final_results
        
        return results
