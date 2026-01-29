"""Checkpoint and resume functionality for the crawler."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime

from .models import Chunk, CrawlMetadata


@dataclass
class CheckpointData:
    """Data structure for checkpoint state."""
    start_url: str
    crawl_started_at: str
    max_depth: int
    chunk_size: int
    
    # Progress tracking
    visited: List[str] = field(default_factory=list)
    pending: List[Tuple[str, int]] = field(default_factory=list)  # (url, depth) tuples
    pages_crawled: int = 0
    
    # Collected data
    chunks: List[Dict] = field(default_factory=list)
    
    # Configuration
    same_domain: bool = True
    include_subdomains: bool = False
    respect_robots: bool = True
    rate_limit: float = 1.0
    concurrency: int = 5
    use_fast: bool = True
    
    # Checkpoint metadata
    last_checkpoint_at: str = ""
    checkpoint_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'start_url': self.start_url,
            'crawl_started_at': self.crawl_started_at,
            'max_depth': self.max_depth,
            'chunk_size': self.chunk_size,
            'visited': self.visited,
            'pending': self.pending,
            'pages_crawled': self.pages_crawled,
            'chunks': self.chunks,
            'same_domain': self.same_domain,
            'include_subdomains': self.include_subdomains,
            'respect_robots': self.respect_robots,
            'rate_limit': self.rate_limit,
            'concurrency': self.concurrency,
            'use_fast': self.use_fast,
            'last_checkpoint_at': self.last_checkpoint_at,
            'checkpoint_version': self.checkpoint_version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointData':
        """Create from dictionary."""
        # Handle pending as list of tuples
        pending = data.get('pending', [])
        if pending and isinstance(pending[0], list):
            pending = [tuple(p) for p in pending]
        
        return cls(
            start_url=data['start_url'],
            crawl_started_at=data['crawl_started_at'],
            max_depth=data['max_depth'],
            chunk_size=data['chunk_size'],
            visited=data.get('visited', []),
            pending=pending,
            pages_crawled=data.get('pages_crawled', 0),
            chunks=data.get('chunks', []),
            same_domain=data.get('same_domain', True),
            include_subdomains=data.get('include_subdomains', False),
            respect_robots=data.get('respect_robots', True),
            rate_limit=data.get('rate_limit', 1.0),
            concurrency=data.get('concurrency', 5),
            use_fast=data.get('use_fast', True),
            last_checkpoint_at=data.get('last_checkpoint_at', ''),
            checkpoint_version=data.get('checkpoint_version', '1.0')
        )


class CheckpointManager:
    """Manages checkpoint save/load operations."""

    DEFAULT_CHECKPOINT_INTERVAL = 50  # Save every N pages

    def __init__(
        self,
        checkpoint_file: Optional[str] = None,
        checkpoint_interval: int = DEFAULT_CHECKPOINT_INTERVAL,
        auto_detect: bool = True
    ):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_file: Path to checkpoint file
            checkpoint_interval: Save checkpoint every N pages
            auto_detect: Auto-detect checkpoint file if not specified
        """
        self.checkpoint_file = checkpoint_file
        self.checkpoint_interval = checkpoint_interval
        self.auto_detect = auto_detect
        self._checkpoint_data: Optional[CheckpointData] = None
        self._pages_since_checkpoint = 0

    def get_default_checkpoint_path(self, start_url: str) -> Path:
        """
        Get default checkpoint file path based on start URL.

        Args:
            start_url: Starting URL for the crawl

        Returns:
            Path to checkpoint file
        """
        from urllib.parse import urlparse
        parsed = urlparse(start_url)
        domain = parsed.netloc.replace('.', '_').replace(':', '_')
        path_part = parsed.path.strip('/').replace('/', '_')[:30] if parsed.path.strip('/') else ''
        
        filename = f".crawler_checkpoint_{domain}"
        if path_part:
            filename += f"_{path_part}"
        filename += ".json"
        
        return Path(filename)

    def find_existing_checkpoint(self, start_url: str) -> Optional[Path]:
        """
        Find existing checkpoint file for the given URL.

        Args:
            start_url: Starting URL

        Returns:
            Path to checkpoint file if found, None otherwise
        """
        if self.checkpoint_file:
            path = Path(self.checkpoint_file)
            if path.exists():
                return path
            return None
        
        if self.auto_detect:
            default_path = self.get_default_checkpoint_path(start_url)
            if default_path.exists():
                return default_path
        
        return None

    def load_checkpoint(self, checkpoint_path: Optional[Path] = None) -> Optional[CheckpointData]:
        """
        Load checkpoint from file.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            CheckpointData if loaded successfully, None otherwise
        """
        path = checkpoint_path or (Path(self.checkpoint_file) if self.checkpoint_file else None)
        
        if not path or not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._checkpoint_data = CheckpointData.from_dict(data)
            return self._checkpoint_data
        
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Warning: Failed to load checkpoint: {e}")
            return None

    def save_checkpoint(
        self,
        data: CheckpointData,
        force: bool = False
    ) -> bool:
        """
        Save checkpoint to file.

        Args:
            data: Checkpoint data to save
            force: Force save even if interval not reached

        Returns:
            True if saved, False otherwise
        """
        self._pages_since_checkpoint += 1
        
        if not force and self._pages_since_checkpoint < self.checkpoint_interval:
            return False
        
        # Update timestamp
        data.last_checkpoint_at = datetime.utcnow().isoformat() + 'Z'
        
        # Determine checkpoint file path
        if self.checkpoint_file:
            path = Path(self.checkpoint_file)
        else:
            path = self.get_default_checkpoint_path(data.start_url)
        
        try:
            # Write to temp file first, then rename (atomic operation)
            temp_path = path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data.to_dict(), f, ensure_ascii=False)
            
            # Rename to final path
            temp_path.rename(path)
            
            self._pages_since_checkpoint = 0
            self._checkpoint_data = data
            
            return True
        
        except Exception as e:
            print(f"Warning: Failed to save checkpoint: {e}")
            return False

    def delete_checkpoint(self, start_url: str = None):
        """
        Delete checkpoint file after successful completion.

        Args:
            start_url: Starting URL (for auto-detection)
        """
        path = None
        
        if self.checkpoint_file:
            path = Path(self.checkpoint_file)
        elif start_url:
            path = self.get_default_checkpoint_path(start_url)
        
        if path and path.exists():
            try:
                path.unlink()
            except Exception:
                pass

    def should_resume(self, start_url: str) -> bool:
        """
        Check if there's a checkpoint to resume from.

        Args:
            start_url: Starting URL

        Returns:
            True if checkpoint exists and can be resumed
        """
        checkpoint_path = self.find_existing_checkpoint(start_url)
        if not checkpoint_path:
            return False
        
        checkpoint_data = self.load_checkpoint(checkpoint_path)
        if not checkpoint_data:
            return False
        
        # Verify the checkpoint matches the current crawl
        return checkpoint_data.start_url == start_url

    def create_checkpoint_data(
        self,
        start_url: str,
        crawl_started_at: str,
        max_depth: int,
        chunk_size: int,
        **kwargs
    ) -> CheckpointData:
        """
        Create new checkpoint data structure.

        Args:
            start_url: Starting URL
            crawl_started_at: Timestamp when crawl started
            max_depth: Maximum crawl depth
            chunk_size: Target chunk size
            **kwargs: Additional configuration options

        Returns:
            New CheckpointData instance
        """
        return CheckpointData(
            start_url=start_url,
            crawl_started_at=crawl_started_at,
            max_depth=max_depth,
            chunk_size=chunk_size,
            same_domain=kwargs.get('same_domain', True),
            include_subdomains=kwargs.get('include_subdomains', False),
            respect_robots=kwargs.get('respect_robots', True),
            rate_limit=kwargs.get('rate_limit', 1.0),
            concurrency=kwargs.get('concurrency', 5),
            use_fast=kwargs.get('use_fast', True)
        )

    def update_checkpoint(
        self,
        data: CheckpointData,
        visited: Set[str] = None,
        pending: List[Tuple[str, int]] = None,
        chunks: List[Chunk] = None,
        pages_crawled: int = None
    ) -> CheckpointData:
        """
        Update checkpoint data with current progress.

        Args:
            data: Current checkpoint data
            visited: Set of visited URLs
            pending: List of pending (url, depth) tuples
            chunks: List of collected chunks
            pages_crawled: Number of pages crawled

        Returns:
            Updated checkpoint data
        """
        if visited is not None:
            data.visited = list(visited)
        
        if pending is not None:
            data.pending = list(pending)
        
        if chunks is not None:
            data.chunks = [chunk.to_dict() for chunk in chunks]
        
        if pages_crawled is not None:
            data.pages_crawled = pages_crawled
        
        return data

    def restore_chunks(self, chunk_dicts: List[Dict]) -> List[Chunk]:
        """
        Restore Chunk objects from dictionaries.

        Args:
            chunk_dicts: List of chunk dictionaries

        Returns:
            List of Chunk objects
        """
        chunks = []
        
        for chunk_dict in chunk_dicts:
            page_meta_dict = chunk_dict.get('page_metadata', {})
            
            page_metadata = CrawlMetadata(
                url=page_meta_dict.get('url', ''),
                canonical_url=page_meta_dict.get('canonical_url'),
                title=page_meta_dict.get('title', ''),
                description=page_meta_dict.get('description'),
                crawled_at=page_meta_dict.get('crawled_at', ''),
                depth=page_meta_dict.get('depth', 0),
                status_code=page_meta_dict.get('status_code', 200)
            )
            
            chunk = Chunk(
                chunk_id=chunk_dict.get('chunk_id', ''),
                content=chunk_dict.get('content', ''),
                char_count=chunk_dict.get('char_count', 0),
                estimated_tokens=chunk_dict.get('estimated_tokens', 0),
                position=chunk_dict.get('position', 0),
                heading_context=chunk_dict.get('heading_context'),
                page_metadata=page_metadata
            )
            
            chunks.append(chunk)
        
        return chunks
