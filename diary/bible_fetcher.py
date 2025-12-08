#!/usr/bin/env python3
"""Gospel-only fetcher kept inside diary package."""

import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class BibleFetcher:
    def __init__(self):
        self.base_url = "https://bible.usccb.org/bible/readings"
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}

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
