"""Data models for the web crawler."""

from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime
import uuid


@dataclass
class CrawlMetadata:
    """Metadata about a crawled page."""
    url: str
    canonical_url: Optional[str]
    title: str
    description: Optional[str]
    crawled_at: str  # ISO 8601 timestamp
    depth: int
    status_code: int

    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Chunk:
    """A text chunk optimized for LLM consumption."""
    chunk_id: str
    content: str
    char_count: int
    estimated_tokens: int
    position: int  # Chunk position in document (0-indexed)
    heading_context: Optional[str]  # Parent heading for context
    page_metadata: CrawlMetadata

    def to_dict(self):
        """Convert to dictionary."""
        data = asdict(self)
        data['page_metadata'] = self.page_metadata.to_dict()
        return data


@dataclass
class CrawlResult:
    """Result of a crawl operation."""
    start_url: str
    crawl_started_at: str
    crawl_completed_at: str
    max_depth: int
    total_pages_crawled: int
    total_chunks: int
    crawler_version: str
    chunks: List[Chunk]

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'crawl_metadata': {
                'start_url': self.start_url,
                'crawl_started_at': self.crawl_started_at,
                'crawl_completed_at': self.crawl_completed_at,
                'max_depth': self.max_depth,
                'total_pages_crawled': self.total_pages_crawled,
                'total_chunks': self.total_chunks,
                'crawler_version': self.crawler_version,
            },
            'chunks': [chunk.to_dict() for chunk in self.chunks]
        }


def generate_chunk_id() -> str:
    """Generate a unique ID for a chunk."""
    return str(uuid.uuid4())


def get_iso_timestamp() -> str:
    """Get current timestamp in ISO 8601 format."""
    return datetime.utcnow().isoformat() + 'Z'
