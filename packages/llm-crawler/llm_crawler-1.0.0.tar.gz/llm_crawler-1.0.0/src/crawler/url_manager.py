"""URL queue management with depth tracking and deduplication."""

from collections import deque
from typing import Set, Dict, Tuple, Optional, List
from urllib.parse import urlparse, urljoin, urlunparse
import validators

from .robots_parser import RobotsParser, SitemapParser


class URLManager:
    """Manages URL queue, deduplication, and depth tracking."""

    def __init__(
        self,
        start_url: str,
        max_depth: int = 1,
        same_domain: bool = True,
        include_subdomains: bool = False,
        respect_robots: bool = True,
        user_agent: str = None
    ):
        """
        Initialize URL manager.

        Args:
            start_url: Starting URL for crawling
            max_depth: Maximum crawl depth
            same_domain: Whether to restrict crawling to the same domain
            include_subdomains: Whether to include subdomains when same_domain is True
            respect_robots: Whether to respect robots.txt directives
            user_agent: User agent string for robots.txt matching
        """
        self.start_url = start_url
        self.max_depth = max_depth
        self.same_domain = same_domain
        self.include_subdomains = include_subdomains
        self.respect_robots = respect_robots
        
        # Initialize robots.txt parser
        self.robots_parser: Optional[RobotsParser] = None
        self.robots_crawl_delay: Optional[float] = None
        
        if respect_robots:
            self.robots_parser = RobotsParser(start_url, user_agent)
            self.robots_parser.fetch()
            self.robots_crawl_delay = self.robots_parser.get_crawl_delay()

        # Parse start URL to get domain
        parsed = urlparse(start_url)
        self.start_domain = parsed.netloc.lower()
        self.base_domain = self._get_base_domain(self.start_domain)

        # Extract path prefix for path-based filtering
        self.start_path = parsed.path

        # Normalize the start path (remove trailing slash unless it's root)
        if self.start_path.endswith('/') and len(self.start_path) > 1:
            self.start_path = self.start_path.rstrip('/')

        # If start_path is just '/', set to empty string to allow all paths on domain
        if self.start_path == '/':
            self.start_path = ''

        # Queue of URLs to visit: (url, depth)
        self.to_visit: deque = deque([(start_url, 0)])

        # Track visited URLs
        self.visited: Set[str] = set()

        # Track depth for each URL
        self.url_depth: Dict[str, int] = {start_url: 0}

    def _get_base_domain(self, domain: str) -> str:
        """Extract base domain (e.g., example.com from www.example.com)."""
        parts = domain.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return domain

    def normalize_url(self, url: str, base_url: str = None) -> Optional[str]:
        """
        Normalize URL for consistent comparison.

        Args:
            url: URL to normalize
            base_url: Base URL for resolving relative URLs

        Returns:
            Normalized URL or None if invalid
        """
        # Handle relative URLs
        if base_url:
            url = urljoin(base_url, url)

        # Validate URL
        if not validators.url(url):
            return None

        # Parse URL
        parsed = urlparse(url)

        # Remove fragment
        parsed = parsed._replace(fragment='')

        # Convert to lowercase (scheme and netloc only)
        parsed = parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower()
        )

        # Remove trailing slash from path (unless it's the root)
        path = parsed.path
        if path.endswith('/') and len(path) > 1:
            path = path.rstrip('/')
            parsed = parsed._replace(path=path)

        # Reconstruct URL
        normalized = urlunparse(parsed)

        return normalized

    def is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if self.include_subdomains:
            # Check if base domain matches
            url_base_domain = self._get_base_domain(domain)
            return url_base_domain == self.base_domain
        else:
            # Exact domain match
            return domain == self.start_domain

    def _is_path_prefix_match(self, url: str) -> bool:
        """Check if URL's path starts with the start_url's path prefix.

        Args:
            url: The URL to check

        Returns:
            True if the URL path matches the prefix, False otherwise

        Examples:
            Start path: '/docs/api'
            - '/docs/api' -> True (exact match)
            - '/docs/api/' -> True (same, normalized)
            - '/docs/api/graphql' -> True (subpath)
            - '/docs/other' -> False (different prefix)
            - '/documentation' -> False (partial match, not a valid prefix)
        """
        if not self.start_path:
            # If start_url has no path (root domain), allow all paths on same domain
            return True

        parsed = urlparse(url)
        url_path = parsed.path

        # Normalize url path (remove trailing slash unless root)
        if url_path.endswith('/') and len(url_path) > 1:
            url_path = url_path.rstrip('/')

        # Check if URL path starts with the prefix
        # Must be either exact match or have a '/' after prefix to avoid partial matches
        # e.g., /docs matches /docs, /docs/, /docs/api but not /documentation
        if url_path == self.start_path:
            return True

        if url_path.startswith(self.start_path + '/'):
            return True

        return False

    def should_crawl(self, url: str, current_depth: int) -> bool:
        """
        Determine if a URL should be crawled.

        Args:
            url: URL to check
            current_depth: Current crawl depth

        Returns:
            True if URL should be crawled
        """
        # Normalize URL
        normalized = self.normalize_url(url)
        if not normalized:
            return False

        # Check if already visited
        if normalized in self.visited:
            return False

        # Check depth limit
        if current_depth > self.max_depth:
            return False

        # Check same-domain restriction
        if self.same_domain and not self.is_same_domain(normalized):
            return False

        # Check path prefix restriction (when same_domain is enabled)
        if self.same_domain and not self._is_path_prefix_match(normalized):
            return False

        # Check robots.txt rules
        if self.respect_robots and self.robots_parser:
            if not self.robots_parser.is_allowed(normalized):
                return False

        return True

    def add_url(self, url: str, depth: int):
        """
        Add URL to the queue.

        Args:
            url: URL to add
            depth: Depth of the URL
        """
        normalized = self.normalize_url(url)
        if not normalized:
            return

        if normalized not in self.visited and normalized not in self.url_depth:
            self.to_visit.append((normalized, depth))
            self.url_depth[normalized] = depth

    def add_urls(self, urls: list, current_url: str, current_depth: int):
        """
        Add multiple URLs extracted from a page.

        Args:
            urls: List of URLs to add
            current_url: URL of the page these links came from
            current_depth: Current depth
        """
        new_depth = current_depth + 1

        for url in urls:
            # Normalize relative URLs
            normalized = self.normalize_url(url, base_url=current_url)
            if not normalized:
                continue

            # Check if should crawl
            if self.should_crawl(normalized, new_depth):
                self.add_url(normalized, new_depth)

    def get_next_url(self) -> Optional[Tuple[str, int]]:
        """
        Get next URL to crawl.

        Returns:
            Tuple of (url, depth) or None if queue is empty
        """
        while self.to_visit:
            url, depth = self.to_visit.popleft()
            normalized = self.normalize_url(url)

            if not normalized:
                continue

            if normalized not in self.visited:
                self.visited.add(normalized)
                return (normalized, depth)

        return None

    def has_urls(self) -> bool:
        """Check if there are URLs left to crawl."""
        return len(self.to_visit) > 0

    def get_stats(self) -> Dict[str, any]:
        """Get crawling statistics."""
        stats = {
            'visited': len(self.visited),
            'queued': len(self.to_visit),
            'max_depth': self.max_depth,
            'robots_respected': self.respect_robots
        }
        
        if self.robots_parser:
            stats['robots_crawl_delay'] = self.robots_crawl_delay
            stats['sitemaps_found'] = len(self.robots_parser.get_sitemaps())
        
        return stats

    def get_sitemaps(self) -> List[str]:
        """
        Get sitemap URLs from robots.txt.

        Returns:
            List of sitemap URLs, empty if robots.txt not loaded
        """
        if self.robots_parser:
            return self.robots_parser.get_sitemaps()
        return []

    def get_robots_crawl_delay(self) -> Optional[float]:
        """
        Get crawl delay from robots.txt.

        Returns:
            Crawl delay in seconds, or None if not specified
        """
        return self.robots_crawl_delay

    def get_disallowed_paths(self) -> List[str]:
        """
        Get disallowed paths from robots.txt for informational purposes.

        Returns:
            List of disallowed path patterns
        """
        if self.robots_parser:
            return self.robots_parser.get_disallowed_paths()
        return []

    def add_sitemap_urls(self, max_urls: int = None) -> int:
        """
        Fetch and add URLs from sitemaps to the queue.

        Args:
            max_urls: Maximum number of URLs to add (None for unlimited)

        Returns:
            Number of URLs added
        """
        if not self.robots_parser:
            return 0

        sitemaps = self.robots_parser.get_sitemaps()
        if not sitemaps:
            return 0

        sitemap_parser = SitemapParser(
            user_agent=self.robots_parser.user_agent if self.robots_parser else None
        )
        
        added_count = 0
        for sitemap_url in sitemaps:
            urls = sitemap_parser.fetch_urls(sitemap_url)
            
            for url in urls:
                if max_urls and added_count >= max_urls:
                    return added_count
                    
                normalized = self.normalize_url(url)
                if normalized and self.should_crawl(normalized, 0):
                    self.add_url(normalized, 0)  # Sitemap URLs are at depth 0
                    added_count += 1

        return added_count
