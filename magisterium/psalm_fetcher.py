#!/usr/bin/env python3
"""Psalm Fetcher Module (Responsorial Psalm only)."""

import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class PsalmFetcher:
    def __init__(self):
        self.base_url = "https://bible.usccb.org/bible/readings"
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}

    def fetch_daily_psalm(self, date: datetime) -> Optional[Dict[str, str]]:
        try:
            date_str = date.strftime("%m%d%y")
            url = f"{self.base_url}/{date_str}.cfm"
            logger.info(f"Fetching Responsorial Psalm from: {url}")
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')
            psalm_payload = self._extract_psalm(soup)
            if not psalm_payload:
                logger.error("Responsorial Psalm section not found.")
                return None
            combined_text, citation, link, body = psalm_payload
            return {
                'date': date.strftime("%A, %B %d, %Y"),
                'url': url,
                'Psalm': combined_text,
                'psalm_citation': citation,
                'psalm_link': link,
                'psalm_body': body,
            }
        except requests.RequestException as e:
            logger.error(f"Network error fetching Psalm: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing Psalm: {e}")
            return None

    def _extract_psalm(self, soup: BeautifulSoup) -> Optional[Tuple[str, str, str, str]]:
        verse_blocks = soup.find_all('div', class_='b-verse')
        for block in verse_blocks:
            header = block.find('h3', class_='name')
            if not header:
                continue
            header_text = header.get_text(strip=True).lower()
            if 'responsorial psalm' not in header_text and 'psalm' not in header_text:
                continue
            citation_a = block.find('div', class_='address')
            citation_text = ""; citation_link = ""
            if citation_a:
                a_tag = citation_a.find('a')
                if a_tag:
                    citation_text = a_tag.get_text(strip=True)
                    citation_link = a_tag.get('href', '')
            body_div = block.find('div', class_='content-body') or block.find('div', class_='body')
            if not body_div:
                continue
            for br in body_div.find_all('br'):
                br.replace_with('\n')
            body_text = "\n\n".join(
                p.get_text('\n', strip=True) for p in body_div.find_all(['p', 'div']) if p.get_text(strip=True)
            ) or body_div.get_text('\n', strip=True)
            body_text = body_text.replace('\xa0', '').strip()
            composed = (citation_text or 'Responsorial Psalm') + (f" ({citation_link})" if citation_link else '')
            composed += "\n\n" + body_text
            return composed, citation_text, citation_link, body_text
        return None
