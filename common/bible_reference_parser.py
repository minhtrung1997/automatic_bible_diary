#!/usr/bin/env python3
"""
Bible Reference Parser Module
Extracts and parses Bible references from text content.
"""

import re
import logging
from typing import List, Dict, Optional

from common.book_mappings import BOOK_MAPPINGS

logger = logging.getLogger(__name__)


class BibleReferenceParser:
    def __init__(self):
        """Initialize the Bible reference parser."""
        # Use shared book mappings
        self.book_mappings = BOOK_MAPPINGS

    def extract_bible_references(self, text: str) -> List[Dict[str, object]]:
        """Extract Bible references from text.

        Returns list of dicts: book, chapter, verse_start, verse_end, original_text
        """
        references: List[Dict[str, object]] = []

        # Pattern for complex citations like "Psalm 90:3-4, 5-6, 12-13, 14 and 17"
        complex_pattern = r'(\d?\s?[A-Za-z\-]+)\s+(\d+):([\d\-,\s]+(?:and\s+\d+)?)'
        complex_match = re.search(complex_pattern, text, re.IGNORECASE)
        
        if complex_match:
            book = complex_match.group(1).strip()
            chapter = int(complex_match.group(2))
            verse_ranges_text = complex_match.group(3)
            
            normalized_book = self.normalize_book_name(book)
            book_name = normalized_book or book
            
            # Parse multiple verse ranges: "3-4, 5-6, 12-13, 14 and 17"
            verse_ranges = self._parse_verse_ranges(verse_ranges_text)
            
            for verse_start, verse_end in verse_ranges:
                references.append({
                    'original_text': f"{book} {chapter}:{verse_start}" + (f"-{verse_end}" if verse_end else ""),
                    'book': book_name,
                    'chapter': chapter,
                    'verse_start': verse_start,
                    'verse_end': verse_end,
                })
        else:
            # Fallback to simple patterns
            patterns = [
                r'(\d?\s?[A-Za-z\-]+)\s+(\d+):(\d+)(?:-(\d+))?',  # "Matthew 5:3-4" or "1 Cor 13:4"
                r'([A-Za-z\-]+)\s+(\d+),\s*(\d+)(?:-(\d+))?',     # "Matthew 5, 3-4"
            ]

            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    book = match.group(1).strip()
                    chapter = int(match.group(2))
                    verse_start = int(match.group(3))
                    verse_end = int(match.group(4)) if match.group(4) else None

                    normalized_book = self.normalize_book_name(book)

                    references.append({
                        'original_text': match.group(0),
                        'book': normalized_book or book,
                        'chapter': chapter,
                        'verse_start': verse_start,
                        'verse_end': verse_end,
                    })

        return references

    def _parse_verse_ranges(self, verse_ranges_text: str) -> List[tuple]:
        """Parse verse ranges like '3-4, 5-6, 12-13, 14 and 17' into list of (start, end) tuples."""
        ranges = []
        
        # Clean up the text and split by comma and 'and'
        cleaned = verse_ranges_text.replace(' and ', ', ')
        parts = [part.strip() for part in cleaned.split(',')]
        
        for part in parts:
            if not part:
                continue
                
            if '-' in part:
                # Range like "3-4" or "12-13"
                try:
                    start, end = part.split('-')
                    ranges.append((int(start.strip()), int(end.strip())))
                except ValueError:
                    logger.debug(f"Could not parse verse range: {part}")
            else:
                # Single verse like "14" or "17"
                try:
                    verse = int(part.strip())
                    ranges.append((verse, verse))
                except ValueError:
                    logger.debug(f"Could not parse single verse: {part}")
        
        return ranges

    def normalize_book_name(self, book_name: str) -> Optional[str]:
        book_lower = book_name.lower().strip()
        return self.book_mappings.get(book_lower)
