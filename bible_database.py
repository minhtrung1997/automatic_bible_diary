#!/usr/bin/env python3
"""
Bible Database Interface Module
Provides access to Vietnamese Bible verses from RVV.SQLite3 database.
"""

import sqlite3
import logging
import os
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class BibleDatabase:
    def __init__(self, db_path: Optional[str] = None):
        """Initialize Bible database connection.
        
        Args:
            db_path: Path to SQLite database file. Defaults to database/RVV.SQLite3
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'database', 'RVV.SQLite3')
        
        self.db_path = db_path
        self._connection = None
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Bible database not found: {db_path}")
        
        self._init_connection()
        self._explore_schema()
    
    def _init_connection(self):
        """Initialize database connection"""
        try:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to Bible database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to Bible database: {e}")
            raise
    
    def _explore_schema(self):
        """Explore database schema to understand structure"""
        try:
            cursor = self._connection.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Available tables: {tables}")
            
            # Explore main tables structure
            for table in tables[:3]:  # Limit to first 3 tables
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                logger.info(f"Table '{table}' columns: {[col[1] for col in columns]}")
                
        except Exception as e:
            logger.warning(f"Could not explore database schema: {e}")
    
    def get_all_books(self) -> List[Dict[str, any]]:
        """Get list of all books in the database."""
        if not self._connection:
            return []
            
        try:
            cursor = self._connection.cursor()
            cursor.execute("SELECT book_number, short_name, long_name FROM books ORDER BY book_number")
            results = cursor.fetchall()
            
            return [
                {
                    'book_number': row[0],
                    'short_name': row[1], 
                    'long_name': row[2]
                } 
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting all books: {e}")
            return []
    
    def get_book_number(self, book_name: str) -> Optional[int]:
        """Get book number from book name (Vietnamese or English)."""
        if not self._connection:
            return None
            
        try:
            cursor = self._connection.cursor()
            
            # Search in both short_name and long_name fields
            cursor.execute("""
                SELECT book_number FROM books 
                WHERE LOWER(short_name) LIKE ? OR LOWER(long_name) LIKE ?
            """, (f"%{book_name.lower()}%", f"%{book_name.lower()}%"))
            
            result = cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error finding book number for '{book_name}': {e}")
            return None
    
    def search_verse_by_reference(self, book: str, chapter: int, verse_start: int, verse_end: Optional[int] = None) -> Optional[str]:
        """Search for verse(s) by book, chapter, and verse reference.
        
        Args:
            book: Book name (Vietnamese or English)
            chapter: Chapter number
            verse_start: Starting verse number
            verse_end: Ending verse number (optional, for verse ranges)
            
        Returns:
            Vietnamese verse text or None if not found
        """
        if not self._connection:
            return None
            
        try:
            # First get the book number
            book_number = self.get_book_number(book)
            if not book_number:
                logger.warning(f"Book not found: {book}")
                return None
            
            cursor = self._connection.cursor()
            end_verse = verse_end or verse_start
            
            # Query the verses table with the specific schema
            cursor.execute("""
                SELECT verse, text FROM verses 
                WHERE book_number = ? AND chapter = ? AND verse >= ? AND verse <= ?
                ORDER BY verse
            """, (book_number, chapter, verse_start, end_verse))
            
            results = cursor.fetchall()
            
            if results:
                # Format verses with verse numbers for clarity
                verses = [f"{row[1]}" for row in results if row[1]]  # Just the text
                return " ".join(verses)
            else:
                logger.warning(f"No verses found for book_number={book_number}, chapter={chapter}, verses={verse_start}-{end_verse}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching verse: {e}")
            return None
    
    def get_tables_info(self) -> Dict[str, List[str]]:
        """Get information about database tables and their columns"""
        if not self._connection:
            return {}
            
        try:
            cursor = self._connection.cursor()
            tables_info = {}
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get columns for each table
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                tables_info[table] = columns
                
            return tables_info
            
        except Exception as e:
            logger.error(f"Error getting tables info: {e}")
            return {}
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict]:
        """Get sample data from a table to understand structure"""
        if not self._connection:
            return []
            
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting sample data from {table_name}: {e}")
            return []
    
    def search_verse_flexible(self, reference_text: str) -> Optional[str]:
        """Flexible verse search using various reference formats.
        
        Args:
            reference_text: Reference like "Matthew 5:3-4", "Ma-thi-ơ 5:3", etc.
            
        Returns:
            Vietnamese verse text or None
        """
        # Parse reference using regex
        patterns = [
            r'([A-Za-z\-\s]+)\s+(\d+):(\d+)-?(\d+)?',  # "Matthew 5:3-4" or "Matthew 5:3"
            r'([A-Za-z\-\s]+)\s+(\d+),\s*(\d+)-?(\d+)?',  # "Matthew 5, 3-4"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, reference_text.strip())
            if match:
                book = match.group(1).strip()
                chapter = int(match.group(2))
                verse_start = int(match.group(3))
                verse_end = int(match.group(4)) if match.group(4) else None
                
                return self.search_verse_by_reference(book, chapter, verse_start, verse_end)
        
        logger.warning(f"Could not parse reference: {reference_text}")
        return None
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Bible database connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def test_bible_database():
    """Test function to explore the database structure"""
    try:
        with BibleDatabase() as bible_db:
            print("=== Bible Database Info ===")
            
            # Show all books
            books = bible_db.get_all_books()
            print(f"\nTotal books: {len(books)}")
            print("First 5 books:")
            for book in books[:5]:
                print(f"  {book['book_number']}: {book['short_name']} - {book['long_name']}")
            
            print("\nLast 5 books:")
            for book in books[-5:]:
                print(f"  {book['book_number']}: {book['short_name']} - {book['long_name']}")
            
            # Test verse lookup
            print("\n=== Testing Verse Lookup ===")
            
            # Test with Genesis (Vietnamese: Khởi Nguyên)
            verse = bible_db.search_verse_by_reference("Khởi Nguyên", 1, 1, 3)
            print(f"Genesis 1:1-3 (Vietnamese): {verse}")
            
            # Test with different book name format
            verse2 = bible_db.search_verse_by_reference("Kn", 1, 1)
            print(f"Genesis 1:1 (short name): {verse2}")
            
            # Test flexible search
            verse3 = bible_db.search_verse_flexible("Khởi Nguyên 1:1-2")
            print(f"Flexible search result: {verse3}")
                        
    except Exception as e:
        print(f"Error testing database: {e}")


if __name__ == "__main__":
    test_bible_database()
