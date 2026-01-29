"""Robots.txt parser for respecting crawl directives."""

import urllib.robotparser
from typing import List, Optional, Set
from urllib.parse import urlparse, urljoin
import requests


class RobotsParser:
    """Parses and enforces robots.txt rules."""

    # Default user agent for the crawler
    DEFAULT_USER_AGENT = "LLMCrawler/1.0"

    def __init__(self, base_url: str, user_agent: str = None):
        """
        Initialize robots.txt parser.

        Args:
            base_url: The base URL of the site to crawl
            user_agent: User agent string to use for checking rules
        """
        self.base_url = base_url
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        
        # Parse base URL to construct robots.txt URL
        parsed = urlparse(base_url)
        self.robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        # Initialize the robot parser
        self.parser = urllib.robotparser.RobotFileParser()
        self.parser.set_url(self.robots_url)
        
        # Store raw content for additional parsing
        self.raw_content: Optional[str] = None
        self.sitemaps: List[str] = []
        self.crawl_delay: Optional[float] = None
        self.is_loaded = False

    def fetch(self, timeout: int = 10) -> bool:
        """
        Fetch and parse the robots.txt file.

        Args:
            timeout: Request timeout in seconds

        Returns:
            True if successfully fetched, False otherwise
        """
        try:
            # Fetch robots.txt manually to get raw content
            response = requests.get(
                self.robots_url,
                timeout=timeout,
                headers={"User-Agent": self.user_agent}
            )
            
            if response.status_code == 200:
                self.raw_content = response.text
                self._parse_raw_content()
                
                # Also use the standard parser
                self.parser.parse(self.raw_content.splitlines())
                self.is_loaded = True
                return True
            elif response.status_code == 404:
                # No robots.txt means everything is allowed
                self.is_loaded = True
                return True
            else:
                # Other errors - be conservative and allow crawling
                self.is_loaded = True
                return True
                
        except requests.RequestException as e:
            # On network error, allow crawling but mark as not fully loaded
            print(f"Warning: Could not fetch robots.txt from {self.robots_url}: {e}")
            self.is_loaded = True
            return False

    def _parse_raw_content(self):
        """Parse raw robots.txt content for additional directives."""
        if not self.raw_content:
            return

        current_user_agent = None
        user_agent_matches = False

        for line in self.raw_content.splitlines():
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse directive
            if ':' in line:
                directive, _, value = line.partition(':')
                directive = directive.strip().lower()
                value = value.strip()

                if directive == 'user-agent':
                    current_user_agent = value
                    # Check if this user-agent section applies to us
                    user_agent_matches = self._user_agent_matches(value)
                
                elif directive == 'sitemap':
                    # Sitemaps are global, not per user-agent
                    if value and value not in self.sitemaps:
                        self.sitemaps.append(value)
                
                elif directive == 'crawl-delay' and user_agent_matches:
                    try:
                        self.crawl_delay = float(value)
                    except ValueError:
                        pass

    def _user_agent_matches(self, ua_pattern: str) -> bool:
        """Check if a user-agent pattern matches our user agent."""
        ua_pattern = ua_pattern.lower()
        user_agent_lower = self.user_agent.lower()
        
        # Wildcard matches all
        if ua_pattern == '*':
            return True
        
        # Check if pattern is contained in our user agent
        return ua_pattern in user_agent_lower

    def is_allowed(self, url: str) -> bool:
        """
        Check if a URL is allowed to be crawled.

        Args:
            url: The URL to check

        Returns:
            True if crawling is allowed, False otherwise
        """
        if not self.is_loaded:
            # If robots.txt wasn't loaded, allow by default
            return True

        try:
            return self.parser.can_fetch(self.user_agent, url)
        except Exception:
            # On any error, allow crawling
            return True

    def get_sitemaps(self) -> List[str]:
        """
        Get list of sitemap URLs from robots.txt.

        Returns:
            List of sitemap URLs
        """
        return self.sitemaps.copy()

    def get_crawl_delay(self) -> Optional[float]:
        """
        Get the crawl delay specified in robots.txt.

        Returns:
            Crawl delay in seconds, or None if not specified
        """
        # Try the standard parser first
        try:
            delay = self.parser.crawl_delay(self.user_agent)
            if delay is not None:
                return float(delay)
        except Exception:
            pass
        
        return self.crawl_delay

    def get_disallowed_paths(self) -> List[str]:
        """
        Get list of disallowed paths for informational purposes.

        Returns:
            List of disallowed path patterns
        """
        disallowed = []
        if not self.raw_content:
            return disallowed

        current_applies = False
        
        for line in self.raw_content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if ':' in line:
                directive, _, value = line.partition(':')
                directive = directive.strip().lower()
                value = value.strip()

                if directive == 'user-agent':
                    current_applies = self._user_agent_matches(value)
                elif directive == 'disallow' and current_applies and value:
                    disallowed.append(value)

        return disallowed

    def __repr__(self) -> str:
        return f"RobotsParser(url={self.robots_url}, loaded={self.is_loaded}, sitemaps={len(self.sitemaps)})"


class SitemapParser:
    """Parses sitemap.xml files to discover URLs."""

    def __init__(self, user_agent: str = None):
        """
        Initialize sitemap parser.

        Args:
            user_agent: User agent for requests
        """
        self.user_agent = user_agent or RobotsParser.DEFAULT_USER_AGENT

    def fetch_urls(self, sitemap_url: str, timeout: int = 30) -> List[str]:
        """
        Fetch and parse URLs from a sitemap.

        Args:
            sitemap_url: URL of the sitemap
            timeout: Request timeout in seconds

        Returns:
            List of URLs found in the sitemap
        """
        urls = []
        
        try:
            response = requests.get(
                sitemap_url,
                timeout=timeout,
                headers={"User-Agent": self.user_agent}
            )
            
            if response.status_code != 200:
                return urls

            content = response.text
            
            # Check if it's a sitemap index (contains other sitemaps)
            if '<sitemapindex' in content:
                # Parse sitemap index
                sitemap_urls = self._extract_sitemap_urls(content)
                for sub_sitemap in sitemap_urls:
                    urls.extend(self.fetch_urls(sub_sitemap, timeout))
            else:
                # Parse regular sitemap
                urls = self._extract_page_urls(content)

        except requests.RequestException as e:
            print(f"Warning: Could not fetch sitemap from {sitemap_url}: {e}")

        return urls

    def _extract_sitemap_urls(self, content: str) -> List[str]:
        """Extract sitemap URLs from a sitemap index."""
        urls = []
        # Simple regex-free parsing
        for line in content.split('<loc>'):
            if '</loc>' in line:
                url = line.split('</loc>')[0].strip()
                if url:
                    urls.append(url)
        return urls

    def _extract_page_urls(self, content: str) -> List[str]:
        """Extract page URLs from a sitemap."""
        urls = []
        # Simple regex-free parsing
        for line in content.split('<loc>'):
            if '</loc>' in line:
                url = line.split('</loc>')[0].strip()
                if url:
                    urls.append(url)
        return urls
