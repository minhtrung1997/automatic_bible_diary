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

from common.book_mappings import BOOK_MAPPINGS

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
            bn = book_name.strip()

            # Use shared book mappings
            mapped = BOOK_MAPPINGS.get(bn.lower())
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

    def _get_verses_by_book_number(
        self, book_number: int, chapter: int, verse_start: int, verse_end: int
    ) -> List[sqlite3.Row]:
        cur = self._connection.cursor()
        cur.execute(
            """
            SELECT verse, text FROM verses
            WHERE book_number = ? AND chapter = ? AND verse >= ? AND verse <= ?
            ORDER BY verse
            """,
            (book_number, chapter, verse_start, verse_end),
        )
        return cur.fetchall()

    def _john_alias_kind(self, book: str) -> Optional[str]:
        b = (book or '').strip().lower()
        if b in {'john', 'jn', 'joh', 'ga', 'gi'}:
            return 'gospel'
        if b in {'1 john', '1 jn', '1jn', '1jo', '1ga', '1gi'}:
            return '1john'
        if b in {'2 john', '2 jn', '2jn', '2jo', '2ga', '2gi'}:
            return '2john'
        if b in {'3 john', '3 jn', '3jn', '3jo', '3ga', '3gi'}:
            return '3john'
        return None

    def _john_fallback_book_numbers(self, kind: str) -> List[int]:
        cur = self._connection.cursor()
        cur.execute("SELECT book_number, short_name, long_name FROM books ORDER BY book_number")
        rows = cur.fetchall()

        def is_same_family(short_name: str, long_name: str) -> bool:
            s = (short_name or '').lower()
            l = (long_name or '').lower()
            if 'john' in l or 'ioan' in l:
                return True
            return s in {'ga', 'gi', '1ga', '2ga', '3ga', '1gi', '2gi', '3gi'}

        def match_kind(short_name: str, long_name: str) -> bool:
            s = (short_name or '').strip().lower()
            l = (long_name or '').strip().lower()

            starts_1 = s.startswith('1') or bool(re.match(r'^1\b|^i\b', l))
            starts_2 = s.startswith('2') or bool(re.match(r'^2\b|^ii\b', l))
            starts_3 = s.startswith('3') or bool(re.match(r'^3\b|^iii\b', l))

            if kind == 'gospel':
                return not starts_1 and not starts_2 and not starts_3
            if kind == '1john':
                return starts_1
            if kind == '2john':
                return starts_2
            if kind == '3john':
                return starts_3
            return False

        candidates: List[int] = []
        for r in rows:
            bn = int(r['book_number'])
            sn = r['short_name'] or ''
            ln = r['long_name'] or ''
            if is_same_family(sn, ln) and match_kind(sn, ln):
                candidates.append(bn)
        return candidates

    def search_verse_by_reference(self, book: str, chapter: int, verse_start: int, verse_end: Optional[int] = None) -> Optional[str]:
        try:
            book_number = self.get_book_number(book)
            if not book_number:
                logger.warning(f"Book not found: {book}")
                return None
            end_verse = verse_end or verse_start
            rows = self._get_verses_by_book_number(book_number, chapter, verse_start, end_verse)

            if not rows:
                kind = self._john_alias_kind(book)
                if kind:
                    for fallback_book_number in self._john_fallback_book_numbers(kind):
                        if fallback_book_number == book_number:
                            continue
                        fallback_rows = self._get_verses_by_book_number(
                            fallback_book_number, chapter, verse_start, end_verse
                        )
                        if fallback_rows:
                            logger.info(
                                f"Resolved {book} {chapter}:{verse_start}-{end_verse} "
                                f"using fallback book_number={fallback_book_number}"
                            )
                            return " ".join(r[1] for r in fallback_rows if r[1])

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
