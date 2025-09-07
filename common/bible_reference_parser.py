#!/usr/bin/env python3
"""
Bible Reference Parser Module
Extracts and parses Bible references from text content.
"""

import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class BibleReferenceParser:
    def __init__(self):
        """Initialize the Bible reference parser."""
        # Common book name mappings (English to Vietnamese)
        self.book_mappings = {
            # Old Testament
            'genesis': 'Khởi Nguyên',
            'gen': 'Kn',
            'exodus': 'Xuất Hành',
            'exod': 'Xh',
            'leviticus': 'Lê Vi',
            'lev': 'Lv',
            'numbers': 'Dân Số',
            'num': 'Ds',
            'deuteronomy': 'Thứ Luật',
            'deut': 'Tl',
            'psalms': 'Thánh Vịnh',
            'psalm': 'Thánh Vịnh',
            'ps': 'Tv',

            # New Testament (common mappings)
            'matthew': 'Mátthêu', 'matt': 'Mt', 'mt': 'Mt',
            'mark': 'Máccô', 'mk': 'Mk',
            'luke': 'Luca', 'lk': 'Lc',
            'john': 'Gioan', 'jn': 'Ga',
            'acts': 'Công vụ Tông đồ',
            'romans': 'Thư Rôma', 'rom': 'Rm',
            '1 corinthians': 'Thư 1 Côrintô', '1 cor': '1Cr',
            '2 corinthians': 'Thư 2 Côrintô', '2 cor': '2Cr',
            'galatians': 'Thư Galát', 'gal': 'Gl',
            'ephesians': 'Thư Êphêsô', 'eph': 'Ep',
            'philippians': 'Thư Philípphê', 'phil': 'Pl',
            'colossians': 'Thư Côlôxê', 'col': 'Cl',
            '1 thessalonians': 'Thư 1 Thêxalônica', '1 thess': '1Tx',
            '2 thessalonians': 'Thư 2 Thêxalônica', '2 thess': '2Tx',
            '1 timothy': 'Thư 1 Timôthê', '1 tim': '1Tm',
            '2 timothy': 'Thư 2 Timôthê', '2 tim': '2Tm',
            'titus': 'Thư Titô', 'tt': 'Tt',
            'philemon': 'Thư Philêmon', 'phlm': 'Plm',
            'hebrews': 'Thư Do Thái', 'heb': 'Dt',
            'james': 'Thư Giacôbê', 'jas': 'Gc',
            '1 peter': 'Thư 1 Phêrô', '1 pet': '1Pr',
            '2 peter': 'Thư 2 Phêrô', '2 pet': '2Pr',
            '1 john': 'Thư 1 Gioan', '1 jn': '1Ga',
            '2 john': 'Thư 2 Gioan', '2 jn': '2Ga',
            '3 john': 'Thư 3 Gioan', '3 jn': '3Ga',
            'jude': 'Thư Giuđa',
            'revelation': 'Khải Huyền', 'rev': 'Kh'
        }

    def extract_bible_references(self, text: str) -> List[Dict[str, object]]:
        """Extract Bible references from text.

        Returns list of dicts: book, chapter, verse_start, verse_end, original_text
        """
        references: List[Dict[str, object]] = []

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

    def normalize_book_name(self, book_name: str) -> Optional[str]:
        book_lower = book_name.lower().strip()
        return self.book_mappings.get(book_lower)
