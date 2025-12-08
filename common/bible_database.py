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
