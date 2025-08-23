#!/usr/bin/env python3
"""
Bible Fetcher Module
Scrapes daily Bible readings from USCCB website
"""

import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)

class BibleFetcher:
    def __init__(self):
        self.base_url = "https://bible.usccb.org/bible/readings"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def fetch_daily_reading(self, date: datetime) -> Optional[Dict[str, str]]:
        """
        Fetch daily Bible readings for the given date
        
        Args:
            date: datetime object for the target date
            
        Returns:
            Dictionary containing Bible readings or None if failed
        """
        try:
            # Format date as MMDDYY for USCCB URL
            date_str = date.strftime("%m%d%y")
            url = f"{self.base_url}/{date_str}.cfm"
            
            logger.info(f"Fetching Bible reading from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract readings
            readings = {
                'date': date.strftime("%A, %B %d, %Y"),
                'url': url
            }
            
            # Find content sections
            content_sections = soup.find_all('div', class_='b-verse')
            
            if not content_sections:
                # Alternative parsing method
                content_sections = soup.find_all('div', class_='content-body')
            
            # Extract different reading types
            reading_types = [
                'First Reading',
                'Responsorial Psalm', 
                'Second Reading',
                'Gospel',
                'Alleluia'
            ]
            
            # Parse readings
            for section in content_sections:
                text_content = section.get_text().strip()
                if text_content:
                    # Identify reading type
                    for reading_type in reading_types:
                        if reading_type.lower() in text_content.lower()[:100]:
                            readings[reading_type] = text_content
                            break
                    else:
                        # Generic content
                        if 'content' not in readings:
                            readings['content'] = text_content
                        else:
                            readings['content'] += f"\n\n{text_content}"
            
            # If no specific readings found, get all text content
            if len(readings) <= 2:  # Only date and url
                all_text = soup.get_text()
                readings['content'] = self._clean_text(all_text)
            
            logger.info(f"Successfully extracted {len(readings)-2} reading sections")
            return readings
            
        except requests.RequestException as e:
            logger.error(f"Network error fetching Bible reading: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Bible reading: {str(e)}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and format text content"""
        import re
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove navigation and footer content
        text = re.sub(r'(Home|Search|Contact|Privacy Policy).*$', '', text, flags=re.IGNORECASE)
        # Limit length
        if len(text) > 5000:
            text = text[:5000] + "..."
            
        return text.strip()