"""Content extraction and cleaning from HTML pages."""

from typing import Dict, Optional, List
from bs4 import BeautifulSoup
import trafilatura
import html2text


class ContentExtractor:
    """Extracts and cleans main content from HTML pages."""

    def __init__(self):
        """Initialize content extractor."""
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = False
        self.html2text.ignore_images = True
        self.html2text.ignore_emphasis = False
        self.html2text.body_width = 0  # Don't wrap text

    def extract_metadata(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """
        Extract metadata from HTML.

        Args:
            html: HTML content
            url: Page URL

        Returns:
            Dictionary with title, description, canonical_url
        """
        soup = BeautifulSoup(html, 'lxml')
        metadata = {}

        # Extract title
        title = None
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find('meta', property='og:title'):
            title = soup.find('meta', property='og:title').get('content', '').strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()

        metadata['title'] = title or 'Untitled'

        # Extract description
        description = None
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '').strip()
        elif soup.find('meta', property='og:description'):
            description = soup.find('meta', property='og:description').get('content', '').strip()

        metadata['description'] = description

        # Extract canonical URL
        canonical = None
        canonical_tag = soup.find('link', rel='canonical')
        if canonical_tag:
            canonical = canonical_tag.get('href', '').strip()

        metadata['canonical_url'] = canonical or url

        return metadata

    def extract_headings(self, html: str) -> List[Dict[str, str]]:
        """
        Extract heading hierarchy from HTML.

        Args:
            html: HTML content

        Returns:
            List of headings with level and text
        """
        soup = BeautifulSoup(html, 'lxml')
        headings = []

        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(tag.name[1])  # Extract number from h1, h2, etc.
            text = tag.get_text().strip()
            if text:
                headings.append({'level': level, 'text': text})

        return headings

    def extract_content(self, html: str, url: str) -> Dict[str, any]:
        """
        Extract main content from HTML page.

        Args:
            html: HTML content
            url: Page URL

        Returns:
            Dictionary with text, metadata, and headings
        """
        # Extract metadata
        metadata = self.extract_metadata(html, url)

        # Extract main content using trafilatura
        # Trafilatura is excellent at identifying main content and removing boilerplate
        extracted_text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            include_formatting=True,
            output_format='txt',
            target_language='en'
        )

        # Fallback to basic extraction if trafilatura fails
        if not extracted_text or len(extracted_text.strip()) < 100:
            extracted_text = self._fallback_extraction(html)

        # Extract heading hierarchy
        headings = self.extract_headings(html)

        return {
            'text': extracted_text.strip() if extracted_text else '',
            'metadata': metadata,
            'headings': headings
        }

    def _fallback_extraction(self, html: str) -> str:
        """
        Fallback content extraction if trafilatura fails.

        Args:
            html: HTML content

        Returns:
            Extracted text
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
            tag.decompose()

        # Remove elements with common boilerplate classes/ids
        boilerplate_patterns = [
            'nav', 'menu', 'sidebar', 'ad', 'advertisement',
            'banner', 'footer', 'header', 'cookie', 'popup'
        ]

        for pattern in boilerplate_patterns:
            for tag in soup.find_all(class_=lambda x: x and pattern in x.lower()):
                tag.decompose()
            for tag in soup.find_all(id=lambda x: x and pattern in x.lower()):
                tag.decompose()

        # Get text from main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body

        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)

    def html_to_markdown(self, html: str) -> str:
        """
        Convert HTML to markdown format.

        Args:
            html: HTML content

        Returns:
            Markdown text
        """
        try:
            markdown = self.html2text.handle(html)
            return markdown
        except Exception:
            # Fallback to plain text
            soup = BeautifulSoup(html, 'lxml')
            return soup.get_text(separator='\n', strip=True)
