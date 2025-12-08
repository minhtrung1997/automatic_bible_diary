#!/usr/bin/env python3
"""
Bible Database Interface Module (shared)
Provides access to Vietnamese Bible verses from RVV.SQLite3 or LCCMN.SQLite3 databases.
"""

import sqlite3
import logging
import os
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)


def _resolve_db_path(default_filename: str, provided: Optional[str] = None) -> str:
    """Resolve DB path relative to repo root if not provided."""
    if provided:
        return provided
    # Try ./database/<file>
    repo_root = os.path.dirname(os.path.dirname(__file__))
    candidate = os.path.join(repo_root, 'database', default_filename)
    return candidate


class BibleDatabase:
    def __init__(self, db_path: Optional[str] = None, default_filename: str = 'RVV.SQLite3'):
        self.db_path = _resolve_db_path(default_filename, db_path)
        self._connection = None
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Bible database not found: {self.db_path}")
        self._init_connection()

    def _init_connection(self):
        try:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            logger.info(f"Connected to Bible database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to Bible database: {e}")
            raise

    def get_all_books(self) -> List[Dict[str, object]]:
        try:
            cur = self._connection.cursor()
            cur.execute("SELECT book_number, short_name, long_name FROM books ORDER BY book_number")
            return [
                {"book_number": r[0], "short_name": r[1], "long_name": r[2]}
                for r in cur.fetchall()
            ]
        except Exception as e:
            logger.error(f"Error getting all books: {e}")
            return []

    def get_book_number(self, book_name: str) -> Optional[int]:
        try:
            # English to Vietnamese short name mappings (short names work reliably with database)
            aliases = {
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
            bn = book_name.strip()
            mapped = aliases.get(bn.lower())
            if mapped:
                book_name = mapped

            cur = self._connection.cursor()
            # First try exact match on short_name (case-sensitive, works with Unicode)
            cur.execute(
                "SELECT book_number FROM books WHERE short_name = ?",
                (book_name,),
            )
            row = cur.fetchone()
            if row:
                return row[0]
            
            # Fall back to LIKE matching on long_name for Vietnamese book names
            cur.execute(
                "SELECT book_number FROM books WHERE long_name LIKE ?",
                (f"%{book_name}%",),
            )
            row = cur.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error finding book number for '{book_name}': {e}")
            return None

    def search_verse_by_reference(self, book: str, chapter: int, verse_start: int, verse_end: Optional[int] = None) -> Optional[str]:
        try:
            book_number = self.get_book_number(book)
            if not book_number:
                logger.warning(f"Book not found: {book}")
                return None
            end_verse = verse_end or verse_start
            cur = self._connection.cursor()
            cur.execute(
                """
                SELECT verse, text FROM verses 
                WHERE book_number = ? AND chapter = ? AND verse >= ? AND verse <= ?
                ORDER BY verse
                """,
                (book_number, chapter, verse_start, end_verse),
            )
            rows = cur.fetchall()
            if not rows:
                logger.warning(
                    f"No verses found for book_number={book_number}, chapter={chapter}, verses={verse_start}-{end_verse}"
                )
                return None
            return " ".join(r[1] for r in rows if r[1])
        except Exception as e:
            logger.error(f"Error searching verse: {e}")
            return None

    def search_verse_flexible(self, reference_text: str) -> Optional[str]:
        patterns = [
            r'([A-Za-z\-\s]+)\s+(\d+):(\d+)-?(\d+)?',
            r'([A-Za-z\-\s]+)\s+(\d+),\s*(\d+)-?(\d+)?',
        ]
        for p in patterns:
            m = re.search(p, reference_text.strip())
            if m:
                book = m.group(1).strip()
                chapter = int(m.group(2))
                v1 = int(m.group(3))
                v2 = int(m.group(4)) if m.group(4) else None
                return self.search_verse_by_reference(book, chapter, v1, v2)
        logger.warning(f"Could not parse reference: {reference_text}")
        return None

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
