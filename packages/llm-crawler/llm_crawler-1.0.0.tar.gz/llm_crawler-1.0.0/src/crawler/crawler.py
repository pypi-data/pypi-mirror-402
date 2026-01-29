"""Web crawler using Playwright for JavaScript rendering."""

import time
from typing import List, Optional
from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup
from .models import CrawlMetadata, get_iso_timestamp


class WebCrawler:
    """Crawls websites using Playwright for JavaScript support."""

    def __init__(self, rate_limit: float = 1.0, timeout: int = 30000):
        """
        Initialize web crawler.

        Args:
            rate_limit: Delay between requests in seconds
            timeout: Page load timeout in milliseconds
        """
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.last_request_time = 0
        self.playwright = None
        self.browser: Optional[Browser] = None

    def __enter__(self):
        """Context manager entry."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def _respect_rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last_request)

        self.last_request_time = time.time()

    def extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            # Skip empty hrefs, anchors, and javascript: links
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                links.append(href)

        return links

    def crawl_page(self, url: str, depth: int) -> tuple:
        """
        Crawl a single page.

        Args:
            url: URL to crawl
            depth: Current depth

        Returns:
            Tuple of (html_content, links, metadata, success)
        """
        self._respect_rate_limit()

        try:
            # Create a new page for each request
            page: Page = self.browser.new_page()

            # Set timeout
            page.set_default_timeout(self.timeout)

            # Navigate to URL
            response = page.goto(url, wait_until='networkidle')

            if not response:
                page.close()
                return None, [], None, False

            status_code = response.status

            # Wait for content to be visible
            page.wait_for_timeout(1000)  # Wait 1 second for any dynamic content

            # Get HTML content
            html_content = page.content()

            # Extract links
            links = self.extract_links(html_content, url)

            # Create metadata
            metadata = CrawlMetadata(
                url=url,
                canonical_url=url,  # Will be updated by content extractor
                title='',  # Will be updated by content extractor
                description=None,
                crawled_at=get_iso_timestamp(),
                depth=depth,
                status_code=status_code
            )

            page.close()

            return html_content, links, metadata, True

        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            return None, [], None, False

    def crawl(self, url: str, depth: int = 0) -> tuple:
        """
        Crawl a URL and return HTML content with metadata.

        Args:
            url: URL to crawl
            depth: Current depth level

        Returns:
            Tuple of (html_content, links, metadata, success)
        """
        return self.crawl_page(url, depth)
