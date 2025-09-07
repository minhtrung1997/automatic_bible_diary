#!/usr/bin/env python3
"""Magisterium API client for Psalm reflection (package version)."""

from __future__ import annotations

import os
import logging
from typing import Dict, Optional
import requests
from datetime import datetime

from common.bible_database import BibleDatabase
from common.bible_reference_parser import BibleReferenceParser

logger = logging.getLogger(__name__)

DEFAULT_MAGISTERIUM_MODEL = "magisterium-1"


class MagisteriumClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("MAGISTERIUM_API_KEY")
        if not self.api_key:
            raise ValueError("MAGISTERIUM_API_KEY is required for MagisteriumClient")
        self.model = model or os.getenv("MAGISTERIUM_MODEL") or DEFAULT_MAGISTERIUM_MODEL
        self.base_url = os.getenv("MAGISTERIUM_API_BASE", "https://www.magisterium.com/api/v1/chat/completions")
        self.catholic_db: Optional[BibleDatabase] = None
        self.reference_parser: Optional[BibleReferenceParser] = None
        try:
            lccmn_path = None
            # Prefer LCCMN if available
            repo_root = os.path.dirname(os.path.dirname(__file__))
            candidate = os.path.join(repo_root, 'database', 'LCCMN.SQLite3')
            if os.path.exists(candidate):
                lccmn_path = candidate
            if lccmn_path:
                self.catholic_db = BibleDatabase(db_path=lccmn_path, default_filename='LCCMN.SQLite3')
                self.reference_parser = BibleReferenceParser()
                logger.info("Catholic LCCMN database initialized")
            else:
                logger.warning("LCCMN.SQLite3 not found; proceeding without verse enrichment")
        except Exception as e:
            logger.warning(f"Could not initialize LCCMN database: {e}")

    def generate_psalm_reflection(self, psalm_content: Dict[str, str]) -> Optional[str]:
        formatted = self._format_psalm_block(psalm_content)
        prompt = self._build_prompt(formatted, psalm_content.get('date'))
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a faithful Catholic spiritual director."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            res = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            res.raise_for_status()
            data = res.json()
            choices = (data or {}).get("choices") or []
            if not choices:
                logger.error("Magisterium API returned no choices")
                return None
            message = choices[0].get("message") or {}
            content = message.get("content")
            if not content:
                logger.error("Magisterium API returned empty content")
                return None
            return content.strip()
        except requests.RequestException as e:
            logger.error(f"Magisterium API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected Magisterium client error: {e}")
            return None

    def _build_prompt(self, formatted_psalm_block: str, date_str: Optional[str]) -> str:
        today = date_str or datetime.now().strftime('%A, %B %d, %Y')
        return (
            f"Please write a short Catholic reflection (250-400 words) based on today's Responsorial Psalm.\n"
            f"Date: {today}\n\n"
            f"Today's Psalm:\n{formatted_psalm_block}\n\n"
            "Guidance:\n"
            "- Draw out the spiritual and liturgical themes Catholics would recognize.\n"
            "- Reference lines from the Psalm respectfully (quote sparingly).\n"
            "- Offer 2-3 concrete applications for daily life.\n"
            "- Keep a pastoral, prayerful tone. End with a one-line prayer."
        )

    def _format_psalm_block(self, psalm_content: Dict[str, str]) -> str:
        enriched_vi = None
        if self.catholic_db and self.reference_parser:
            try:
                ref_text = psalm_content.get('psalm_citation') or ''
                references = self.reference_parser.extract_bible_references(ref_text)
                if references:
                    r0 = references[0]
                    vi_text = self.catholic_db.search_verse_by_reference(
                        r0['book'], r0['chapter'], r0['verse_start'], r0['verse_end']
                    )
                    if vi_text:
                        enriched_vi = vi_text
            except Exception as e:
                logger.debug(f"Verse enrichment skipped: {e}")
        parts = []
        if 'date' in psalm_content:
            parts.append(f"Date: {psalm_content['date']}")
        citation = psalm_content.get('psalm_citation')
        link = psalm_content.get('psalm_link')
        body = psalm_content.get('psalm_body') or psalm_content.get('Psalm')
        if citation:
            parts.append(f"Citation: {citation}{f' ({link})' if link else ''}")
        if body:
            parts.append("English text:\n" + body.strip())
        if enriched_vi:
            parts.append("Vietnamese (Catholic LCCMN):\n" + enriched_vi.strip())
        return "\n\n".join(parts).strip()

    def close(self):
        if self.catholic_db:
            self.catholic_db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
