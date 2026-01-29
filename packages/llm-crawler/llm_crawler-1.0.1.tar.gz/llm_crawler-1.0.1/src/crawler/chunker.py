"""Smart text chunking for LLM consumption."""

import re
from typing import List, Dict, Optional
from .models import Chunk, CrawlMetadata, generate_chunk_id


class TextChunker:
    """Intelligently chunks text for LLM consumption."""

    def __init__(self, target_chunk_size: int = 4000, overlap_size: int = 500):
        """
        Initialize text chunker.

        Args:
            target_chunk_size: Target size for each chunk in characters
            overlap_size: Number of characters to overlap between chunks
        """
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size

        # Sentence boundary regex
        self.sentence_pattern = re.compile(r'([.!?]+\s+|[.!?]+$)')

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from character count.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count (1 token ≈ 4 characters)
        """
        return len(text) // 4

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Split on sentence boundaries
        sentences = self.sentence_pattern.split(text)

        # Recombine sentences with their punctuation
        result = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and self.sentence_pattern.match(sentences[i + 1]):
                # Combine sentence with its punctuation
                result.append(sentences[i] + sentences[i + 1])
                i += 2
            else:
                if sentences[i].strip():
                    result.append(sentences[i])
                i += 1

        return [s.strip() for s in result if s.strip()]

    def get_heading_context(self, headings: List[Dict[str, any]], char_position: int, text: str) -> Optional[str]:
        """
        Get heading context for a chunk based on its position.

        Args:
            headings: List of headings with level and text
            char_position: Character position in the document
            text: Full document text

        Returns:
            Heading context string (e.g., "Introduction > Getting Started")
        """
        if not headings:
            return None

        # For simplicity, we'll use the first few headings
        # A more sophisticated approach would track heading positions
        heading_texts = [h['text'] for h in headings[:3]]
        return ' > '.join(heading_texts) if heading_texts else None

    def create_chunk_with_overlap(self, sentences: List[str], start_idx: int, target_size: int) -> tuple:
        """
        Create a chunk from sentences starting at start_idx.

        Args:
            sentences: List of sentences
            start_idx: Starting sentence index
            target_size: Target chunk size in characters

        Returns:
            Tuple of (chunk_text, end_idx, overlap_text)
        """
        chunk_sentences = []
        current_size = 0
        end_idx = start_idx

        # Add sentences until we reach target size
        while end_idx < len(sentences):
            sentence = sentences[end_idx]
            sentence_len = len(sentence)

            # If adding this sentence would exceed target by a lot, stop
            if current_size > 0 and current_size + sentence_len > target_size * 1.2:
                break

            chunk_sentences.append(sentence)
            current_size += sentence_len
            end_idx += 1

            # If we've reached a reasonable size, stop
            if current_size >= target_size * 0.8:
                break

        # Create chunk text
        chunk_text = ' '.join(chunk_sentences)

        # Calculate overlap text (last N characters)
        overlap_text = ''
        if end_idx < len(sentences) and current_size > self.overlap_size:
            # Take last few sentences for overlap
            overlap_sentences = []
            overlap_size = 0
            for i in range(len(chunk_sentences) - 1, -1, -1):
                sentence = chunk_sentences[i]
                if overlap_size + len(sentence) <= self.overlap_size:
                    overlap_sentences.insert(0, sentence)
                    overlap_size += len(sentence)
                else:
                    break
            overlap_text = ' '.join(overlap_sentences)

        return chunk_text, end_idx, overlap_text

    def chunk_text(
        self,
        text: str,
        metadata: CrawlMetadata,
        headings: List[Dict[str, any]] = None
    ) -> List[Chunk]:
        """
        Chunk text into LLM-optimized pieces.

        Args:
            text: Text to chunk
            metadata: Metadata about the source page
            headings: List of headings from the page

        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []

        # Split into sentences
        sentences = self.split_into_sentences(text)

        if not sentences:
            return []

        chunks = []
        position = 0
        sentence_idx = 0
        overlap_text = ''

        while sentence_idx < len(sentences):
            # Prepare sentences for this chunk
            chunk_sentences = []
            if overlap_text:
                # Start with overlap from previous chunk
                chunk_sentences.append(overlap_text)

            # Create chunk with target size
            chunk_text, next_idx, new_overlap = self.create_chunk_with_overlap(
                sentences, sentence_idx, self.target_chunk_size
            )

            # If we started with overlap, combine it properly
            if overlap_text:
                # Remove overlap from the beginning of chunk_text to avoid duplication
                chunk_text = overlap_text + ' ' + chunk_text

            # Get heading context
            heading_context = self.get_heading_context(headings, position * self.target_chunk_size, text)

            # Create chunk object
            chunk = Chunk(
                chunk_id=generate_chunk_id(),
                content=chunk_text.strip(),
                char_count=len(chunk_text),
                estimated_tokens=self.estimate_tokens(chunk_text),
                position=position,
                heading_context=heading_context,
                page_metadata=metadata
            )

            chunks.append(chunk)

            # Update for next iteration
            sentence_idx = next_idx
            overlap_text = new_overlap
            position += 1

            # Safety check to prevent infinite loops
            if next_idx <= sentence_idx and sentence_idx < len(sentences):
                # If we didn't advance, move at least one sentence
                sentence_idx += 1

        return chunks

    def chunk_long_text(self, text: str, max_chunk_size: int = 10000) -> List[str]:
        """
        Split very long text into manageable pieces before sentence-level chunking.

        Args:
            text: Text to split
            max_chunk_size: Maximum size for pre-chunking

        Returns:
            List of text pieces
        """
        if len(text) <= max_chunk_size:
            return [text]

        # Split on double newlines (paragraphs)
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = []
        current_size = 0

        for paragraph in paragraphs:
            para_len = len(paragraph)

            if current_size + para_len > max_chunk_size and current_chunk:
                # Save current chunk
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_size = para_len
            else:
                current_chunk.append(paragraph)
                current_size += para_len

        # Add remaining chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks
