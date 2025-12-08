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
        # Common book name mappings (English to Vietnamese short names)
        # Using short names from database for reliable matching
        self.book_mappings = {
            # Old Testament - Pentateuch
            'genesis': 'Kn', 'gen': 'Kn',
            'exodus': 'Xh', 'exod': 'Xh', 'ex': 'Xh',
            'leviticus': 'Lv', 'lev': 'Lv',
            'numbers': 'Ds', 'num': 'Ds', 'nm': 'Ds',
            'deuteronomy': 'Tl', 'deut': 'Tl', 'dt': 'Tl',
            
            # Old Testament - Historical Books
            'joshua': 'Yôs', 'josh': 'Yôs', 'jos': 'Yôs',
            'judges': 'Tp', 'judg': 'Tp', 'jdg': 'Tp',
            'ruth': 'R', 'ru': 'R', 'rut': 'R',
            '1 samuel': '1Sm', '1 sam': '1Sm', '1sam': '1Sm', '1sm': '1Sm',
            '2 samuel': '2Sm', '2 sam': '2Sm', '2sam': '2Sm', '2sm': '2Sm',
            '1 kings': '1V', '1 kgs': '1V', '1kgs': '1V', '1ki': '1V',
            '2 kings': '2V', '2 kgs': '2V', '2kgs': '2V', '2ki': '2V',
            '1 chronicles': '1Sb', '1 chr': '1Sb', '1chr': '1Sb', '1ch': '1Sb',
            '2 chronicles': '2Sb', '2 chr': '2Sb', '2chr': '2Sb', '2ch': '2Sb',
            'ezra': 'Ezr', 'ezr': 'Ezr',
            'nehemiah': 'Nkm', 'neh': 'Nkm', 'ne': 'Nkm',
            'esther': 'Est', 'est': 'Est', 'esth': 'Est',
            
            # Old Testament - Wisdom Books
            'job': 'Yob', 'jb': 'Yob',
            'psalms': 'Tv', 'psalm': 'Tv', 'ps': 'Tv', 'pss': 'Tv',
            'proverbs': 'Cn', 'prov': 'Cn', 'pr': 'Cn',
            'ecclesiastes': 'Gv', 'eccl': 'Gv', 'ecc': 'Gv', 'eccles': 'Gv',
            'song of solomon': 'Hc', 'song of songs': 'Hc', 'song': 'Hc', 'sos': 'Hc', 'ss': 'Hc',
            
            # Old Testament - Major Prophets
            'isaiah': 'Is', 'isa': 'Is', 'is': 'Is',
            'jeremiah': 'Gr', 'jer': 'Gr', 'je': 'Gr',
            'lamentations': 'Ac', 'lam': 'Ac', 'la': 'Ac',
            'ezekiel': 'Êz', 'ezek': 'Êz', 'eze': 'Êz',
            'daniel': 'Ðn', 'dan': 'Ðn', 'da': 'Ðn',
            
            # Old Testament - Minor Prophets
            'hosea': 'Hs', 'hos': 'Hs',
            'joel': 'Ge', 'joe': 'Ge', 'jl': 'Ge',
            'amos': 'Am', 'am': 'Am',
            'obadiah': 'Ôv', 'obad': 'Ôv', 'ob': 'Ôv',
            'jonah': 'Gn', 'jon': 'Gn', 'jnh': 'Gn',
            'micah': 'Mc', 'mic': 'Mc', 'mi': 'Mc',
            'nahum': 'Nk', 'nah': 'Nk', 'na': 'Nk',
            'habakkuk': 'Kb', 'hab': 'Kb', 'hb': 'Kb',
            'zephaniah': 'Xp', 'zeph': 'Xp', 'zep': 'Xp',
            'haggai': 'Hag', 'hag': 'Hag', 'hg': 'Hag',
            'zechariah': 'Dcr', 'zech': 'Dcr', 'zec': 'Dcr',
            'malachi': 'Ml', 'mal': 'Ml',

            # New Testament - Gospels and Acts
            'matthew': 'Mt', 'matt': 'Mt', 'mt': 'Mt',
            'mark': 'Mk', 'mk': 'Mk', 'mr': 'Mk',
            'luke': 'Lc', 'lk': 'Lc', 'lu': 'Lc',
            'john': 'Ga', 'jn': 'Ga', 'joh': 'Ga',
            'acts': 'Cv', 'act': 'Cv', 'ac': 'Cv',
            
            # New Testament - Pauline Epistles
            'romans': 'Rm', 'rom': 'Rm', 'ro': 'Rm',
            '1 corinthians': '1Cr', '1 cor': '1Cr', '1cor': '1Cr', '1co': '1Cr',
            '2 corinthians': '2Cr', '2 cor': '2Cr', '2cor': '2Cr', '2co': '2Cr',
            'galatians': 'Gl', 'gal': 'Gl', 'ga': 'Gl',
            'ephesians': 'Ep', 'eph': 'Ep',
            'philippians': 'Pl', 'phil': 'Pl', 'php': 'Pl',
            'colossians': 'Cl', 'col': 'Cl',
            '1 thessalonians': '1Tx', '1 thess': '1Tx', '1thess': '1Tx', '1th': '1Tx',
            '2 thessalonians': '2Tx', '2 thess': '2Tx', '2thess': '2Tx', '2th': '2Tx',
            '1 timothy': '1Tm', '1 tim': '1Tm', '1tim': '1Tm', '1ti': '1Tm',
            '2 timothy': '2Tm', '2 tim': '2Tm', '2tim': '2Tm', '2ti': '2Tm',
            'titus': 'Tt', 'tit': 'Tt', 'tt': 'Tt',
            'philemon': 'Plm', 'phlm': 'Plm', 'phm': 'Plm',
            
            # New Testament - General Epistles
            'hebrews': 'Dt', 'heb': 'Dt',
            'james': 'Gc', 'jas': 'Gc', 'jam': 'Gc',
            '1 peter': '1Pr', '1 pet': '1Pr', '1pet': '1Pr', '1pe': '1Pr',
            '2 peter': '2Pr', '2 pet': '2Pr', '2pet': '2Pr', '2pe': '2Pr',
            '1 john': '1Ga', '1 jn': '1Ga', '1jn': '1Ga', '1jo': '1Ga',
            '2 john': '2Ga', '2 jn': '2Ga', '2jn': '2Ga', '2jo': '2Ga',
            '3 john': '3Ga', '3 jn': '3Ga', '3jn': '3Ga', '3jo': '3Ga',
            'jude': 'Gđ', 'jud': 'Gđ',
            
            # New Testament - Apocalyptic
            'revelation': 'Kh', 'rev': 'Kh', 're': 'Kh',
        }

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
