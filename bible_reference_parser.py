#!/usr/bin/env python3
"""
Bible Reference Parser Module
Extracts and parses Bible references from text content.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple

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
            
            # New Testament (corrected for RVV.SQLite3)
            'matthew': 'Mátthêu',
            'matt': 'Mt',
            'mt': 'Mt',
            'mark': 'Máccô',
            'mk': 'Mk',
            'luke': 'Luca',
            'lk': 'Lc',
            'john': 'Gioan',
            'jn': 'Ga',
            'acts': 'Công vụ Tông đồ',
            'romans': 'Thư Rôma',
            'rom': 'Rm',
            '1 corinthians': 'Thư 1 Côrintô',
            '1 cor': '1Cr',
            '2 corinthians': 'Thư 2 Côrintô', 
            '2 cor': '2Cr',
            'galatians': 'Thư Galát',
            'gal': 'Gl',
            'ephesians': 'Thư Êphêsô',
            'eph': 'Ep',
            'philippians': 'Thư Philípphê',
            'phil': 'Pl',
            'colossians': 'Thư Côlôxê',
            'col': 'Cl',
            '1 thessalonians': 'Thư 1 Thêxalônica',
            '1 thess': '1Tx',
            '2 thessalonians': 'Thư 2 Thêxalônica',
            '2 thess': '2Tx',
            '1 timothy': 'Thư 1 Timôthê',
            '1 tim': '1Tm',
            '2 timothy': 'Thư 2 Timôthê',
            '2 tim': '2Tm',
            'titus': 'Thư Titô',
            'tt': 'Tt',
            'philemon': 'Thư Philêmon',
            'phlm': 'Plm',
            'hebrews': 'Thư Do Thái',
            'heb': 'Dt',
            'james': 'Thư Giacôbê',
            'jas': 'Gc',
            '1 peter': 'Thư 1 Phêrô',
            '1 pet': '1Pr',
            '2 peter': 'Thư 2 Phêrô',
            '2 pet': '2Pr',
            '1 john': 'Thư 1 Gioan',
            '1 jn': '1Ga',
            '2 john': 'Thư 2 Gioan',
            '2 jn': '2Ga', 
            '3 john': 'Thư 3 Gioan',
            '3 jn': '3Ga',
            'jude': 'Thư Giuđa',
            'revelation': 'Khải Huyền',
            'rev': 'Kh'
        }
    
    def extract_bible_references(self, text: str) -> List[Dict[str, any]]:
        """Extract Bible references from text.
        
        Args:
            text: Text content to parse
            
        Returns:
            List of reference dictionaries with book, chapter, verse_start, verse_end
        """
        references = []
        
        # Pattern for references like "Matthew 5:3-4", "John 3:16", "1 Cor 13:4-8"
        patterns = [
            r'(\d?\s?[A-Za-z\-]+)\s+(\d+):(\d+)(?:-(\d+))?',  # "Matthew 5:3-4" or "1 Cor 13:4"
            r'([A-Za-z\-]+)\s+(\d+),\s*(\d+)(?:-(\d+))?',     # "Matthew 5, 3-4"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                book = match.group(1).strip()
                chapter = int(match.group(2))
                verse_start = int(match.group(3))
                verse_end = int(match.group(4)) if match.group(4) else None
                
                # Normalize book name
                normalized_book = self.normalize_book_name(book)
                
                references.append({
                    'original_text': match.group(0),
                    'book': normalized_book or book,
                    'chapter': chapter,
                    'verse_start': verse_start,
                    'verse_end': verse_end
                })
        
        return references
    
    def normalize_book_name(self, book_name: str) -> Optional[str]:
        """Normalize English book names to Vietnamese equivalents."""
        book_lower = book_name.lower().strip()
        return self.book_mappings.get(book_lower)
    
    def extract_gospel_reference(self, html_content: str) -> Optional[Dict[str, str]]:
        """Extract Gospel reference specifically from USCCB HTML content.
        
        Args:
            html_content: HTML content from USCCB daily reading page
            
        Returns:
            Dictionary with gospel citation and reference info
        """
        try:
            # Look for Gospel section patterns in USCCB format
            gospel_patterns = [
                r'<h3[^>]*>\s*Gospel\s*</h3>\s*<p[^>]*>\s*([^<]+)\s*</p>',  # Gospel heading + citation
                r'Gospel[:\s]*([A-Za-z0-9\s:,-]+)',  # Simple Gospel: citation pattern
                r'<.*?>Gospel.*?<.*?>.*?([A-Za-z]+\s+\d+:\d+[-\d]*)',  # HTML with Gospel citation
            ]
            
            for pattern in gospel_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if match:
                    citation_text = match.group(1).strip()
                    
                    # Parse the citation
                    references = self.extract_bible_references(citation_text)
                    if references:
                        ref = references[0]  # Take first reference
                        return {
                            'citation': citation_text,
                            'book': ref['book'],
                            'chapter': ref['chapter'],
                            'verse_start': ref['verse_start'],
                            'verse_end': ref['verse_end']
                        }
            
            logger.warning("No Gospel reference found in HTML content")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting Gospel reference: {e}")
            return None


def test_reference_parser():
    """Test the Bible reference parser"""
    parser = BibleReferenceParser()
    
    # Test reference extraction
    test_texts = [
        "Today's Gospel reading is from Matthew 5:3-8",
        "First Reading: Genesis 1:1-5, Psalm 23:1-6",
        "Gospel: John 3:16-17",
        "1 Corinthians 13:4-8 speaks about love"
    ]
    
    print("=== Testing Bible Reference Parser ===")
    for text in test_texts:
        print(f"\nText: {text}")
        references = parser.extract_bible_references(text)
        for ref in references:
            print(f"  Found: {ref}")


if __name__ == "__main__":
    test_reference_parser()
