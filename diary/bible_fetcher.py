#!/usr/bin/env python3
"""Gospel-only fetcher kept inside diary package."""

import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

try:
    from common.bible_database import BibleDatabase
    from common.bible_reference_parser import BibleReferenceParser
except ImportError:
    BibleDatabase = None
    BibleReferenceParser = None

logger = logging.getLogger(__name__)


class BibleFetcher:
    def __init__(self):
        self.base_url = "https://bible.usccb.org/bible/readings"
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        # Initialize Bible database and parser for custom verses
        try:
            if BibleDatabase and BibleReferenceParser:
                self.bible_db = BibleDatabase()
                self.reference_parser = BibleReferenceParser()
            else:
                self.bible_db = None
                self.reference_parser = None
        except Exception as e:
            logger.warning(f"Could not initialize Bible database for custom verses: {e}")
            self.bible_db = None
            self.reference_parser = None

    def fetch_daily_reading(self, date: datetime) -> Optional[Dict[str, str]]:
        try:
            date_str = date.strftime("%m%d%y")
            url = f"{self.base_url}/{date_str}.cfm"
            logger.info(f"Fetching Gospel only from: {url}")
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')
            gospel_payload = self._extract_gospel(soup)
            if not gospel_payload:
                logger.error("Gospel section not found.")
                return None
            combined_text, citation, link, body = gospel_payload
            return {
                'date': date.strftime("%A, %B %d, %Y"),
                'url': url,
                'Gospel': combined_text,
                'gospel_citation': citation,
                'gospel_link': link,
                'gospel_body': body,
            }
        except requests.RequestException as e:
            logger.error(f"Network error fetching Gospel: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing Gospel: {e}")
            return None

    def _extract_gospel(self, soup: BeautifulSoup) -> Optional[Tuple[str, str, str, str]]:
        verse_blocks = soup.find_all('div', class_='b-verse')
        for block in verse_blocks:
            header = block.find('h3', class_='name')
            if not header:
                continue
            if 'gospel' not in header.get_text(strip=True).lower():
                continue
            citation_a = block.find('div', class_='address')
            citation_text = ""; citation_link = ""
            if citation_a:
                a_tag = citation_a.find('a')
                if a_tag:
                    citation_text = a_tag.get_text(strip=True)
                    citation_link = a_tag.get('href', '')
            body_div = block.find('div', class_='content-body')
            if not body_div:
                continue
            for br in body_div.find_all('br'):
                br.replace_with('\n')
            body_text = body_div.get_text('\n', strip=True).replace('\xa0', '').strip()
            composed = citation_text
            if citation_link:
                composed += f" ({citation_link})"
            composed += "\n\n" + body_text
            return composed, citation_text, citation_link, body_text
        return None

    def fetch_custom_verse(self, verse_reference: str, date: datetime) -> Optional[Dict[str, str]]:
        """
        Fetch a custom Bible verse by reference (e.g., "Jeremiah 29:11").
        Uses the Vietnamese Bible database to retrieve the verse.
        
        Args:
            verse_reference: Bible verse reference (e.g., "Jeremiah 29:11" or "John 3:16-17")
            date: The date to associate with this reading
            
        Returns:
            Dictionary with verse information in the same format as fetch_daily_reading
        """
        if not self.bible_db or not self.reference_parser:
            logger.error("Bible database not available for custom verses. Please ensure database files are present.")
            return None
            
        try:
            logger.info(f"Fetching custom verse: {verse_reference}")
            
            # Parse the verse reference
            references = self.reference_parser.extract_bible_references(verse_reference)
            if not references:
                logger.error(f"Could not parse verse reference: {verse_reference}")
                return None
            
            # Use the first reference found
            ref = references[0]
            logger.info(f"Parsed reference: {ref}")
            
            # Fetch the verse from the database
            verse_text = self.bible_db.search_verse_by_reference(
                ref['book'], 
                ref['chapter'], 
                ref['verse_start'], 
                ref['verse_end']
            )
            
            if not verse_text:
                logger.error(f"Could not find verse in database: {verse_reference}")
                return None
            
            # Format the citation
            citation = f"{ref['book']} {ref['chapter']}:{ref['verse_start']}"
            if ref['verse_end'] and ref['verse_end'] != ref['verse_start']:
                citation += f"-{ref['verse_end']}"
            
            # Create a combined text similar to the daily reading format
            combined_text = f"{citation}\n\n{verse_text}"
            
            return {
                'date': date.strftime("%A, %B %d, %Y"),
                'url': f"Custom verse: {verse_reference}",
                'Gospel': combined_text,
                'gospel_citation': citation,
                'gospel_link': '',
                'gospel_body': verse_text,
            }
            
        except Exception as e:
            logger.error(f"Error fetching custom verse: {e}")
            return None
    
    def close(self):
        """Close the database connection if it exists."""
        if hasattr(self, 'bible_db') and self.bible_db:
            self.bible_db.close()

