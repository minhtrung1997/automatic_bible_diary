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
        self.base_url = os.getenv(
            "MAGISTERIUM_API_BASE",
            "https://www.magisterium.com/api/v1/chat/completions",
        )

        # Load optional extra system prompt from mg_prompt.txt
        self.extra_system_prompt = self._load_extra_system_prompt()

        # Optional Catholic DB (LCCMN)
        self.catholic_db = None
        self.reference_parser = None
        try:
            # Prefer LCCMN if available at repo_root/database/LCCMN.SQLite3
            repo_root = os.path.dirname(os.path.dirname(__file__))
            candidate = os.path.join(repo_root, 'database', 'LCCMN.SQLite3')
            if os.path.exists(candidate):
                self.catholic_db = BibleDatabase(db_path=candidate, default_filename='LCCMN.SQLite3')
                self.reference_parser = BibleReferenceParser()
                logger.info("Catholic LCCMN database initialized")
            else:
                logger.warning("LCCMN.SQLite3 not found; proceeding without verse enrichment")
        except Exception as e:
            logger.warning(f"Could not initialize LCCMN database: {e}")

    def generate_psalm_reflection(self, psalm_content: Dict[str, str]) -> Optional[str]:
        # Build messages using LCCMN-only content and mg_prompt structure
        vi_text = self.get_vietnamese_psalm_text(psalm_content)
        if not vi_text:
            citation = psalm_content.get('psalm_citation') or 'Thánh Vịnh (không tìm thấy văn bản LCCMN)'
            vi_text = citation

        # Load prompts from mg_prompt.txt
        prompt_config = self._parse_mg_prompt()
        
        messages = []
        if prompt_config.get('system_prompt'):
            messages.append({"role": "system", "content": prompt_config['system_prompt']})
        else:
            # Fallback system prompt
            messages.append({
                "role": "system", 
                "content": "Bạn là một linh hướng Công Giáo trung thành. Hãy trả lời bằng tiếng Việt với cấu trúc: Suy niệm: [nội dung suy niệm] Cầu nguyện: [lời cầu nguyện]."
            })
        
        # Add extra system prompt if available
        if self.extra_system_prompt and not prompt_config.get('system_prompt'):
            messages.append({"role": "system", "content": self.extra_system_prompt})

        # Build user content using template from mg_prompt or fallback
        user_template = prompt_config.get('user_template', 
            "Thánh vịnh hôm nay:\n{bible_content}\n\nSuy niệm:\n\nCầu nguyện:\n"
        )
        user_content = user_template.format(bible_content=vi_text.strip())
        messages.append({"role": "user", "content": user_content})

        payload = {"model": self.model, "messages": messages, "stream": False}
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

    # Deprecated; mg_prompt structure now used directly
    def _build_prompt(self, formatted_psalm_block: str, date_str: Optional[str]) -> str:
        return formatted_psalm_block

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
        # Only return Vietnamese text block when available
        if enriched_vi:
            parts.append(enriched_vi.strip())
        return "\n\n".join(parts).strip()

    def get_vietnamese_psalm_text(self, psalm_content: Dict[str, str]) -> Optional[str]:
        """Return Vietnamese Psalm text from LCCMN if resolvable from psalm_citation."""
        if not (self.catholic_db and self.reference_parser):
            return None
        try:
            ref_text = psalm_content.get('psalm_citation') or ''
            references = self.reference_parser.extract_bible_references(ref_text)
            if not references:
                return None
            
            # Collect all verse texts from all references
            verse_texts = []
            for ref in references:
                verse_text = self.catholic_db.search_verse_by_reference(
                    ref['book'], ref['chapter'], ref['verse_start'], ref['verse_end']
                )
                if verse_text:
                    verse_texts.append(verse_text.strip())
            
            if verse_texts:
                # Join all verses with double newline for readability
                return '\n\n'.join(verse_texts)
            
        except Exception as e:
            logger.debug(f"get_vietnamese_psalm_text skipped: {e}")
        return None

    def close(self):
        if self.catholic_db:
            self.catholic_db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _load_extra_system_prompt(self) -> Optional[str]:
        """Load additional Vietnamese guidance from mg_prompt.txt if present."""
        try:
            base_dir = os.path.dirname(__file__)
            path = os.path.join(base_dir, 'mg_prompt.txt')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    return content or None
        except Exception as e:
            logger.debug(f"Could not load mg_prompt.txt: {e}")
        return None

    def _parse_mg_prompt(self) -> Dict[str, str]:
        """Parse mg_prompt.txt file to extract system prompt and user template."""
        try:
            base_dir = os.path.dirname(__file__)
            path = os.path.join(base_dir, 'mg_prompt.txt')
            if not os.path.exists(path):
                logger.debug("mg_prompt.txt not found, using defaults")
                return {}
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                return {}
            
            config = {}
            lines = content.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                
                # Check for section markers
                if line.startswith('[SYSTEM_PROMPT]'):
                    if current_section and current_content:
                        config[current_section] = '\n'.join(current_content).strip()
                    current_section = 'system_prompt'
                    current_content = []
                elif line.startswith('[USER_TEMPLATE]'):
                    if current_section and current_content:
                        config[current_section] = '\n'.join(current_content).strip()
                    current_section = 'user_template'
                    current_content = []
                elif line.startswith('[') and line.endswith(']'):
                    # Other section markers
                    if current_section and current_content:
                        config[current_section] = '\n'.join(current_content).strip()
                    current_section = line[1:-1].lower()
                    current_content = []
                elif current_section:
                    current_content.append(line)
                elif not current_section and line:
                    # Content before any section marker goes to system_prompt
                    if 'system_prompt' not in config:
                        config['system_prompt'] = line
                    else:
                        config['system_prompt'] += '\n' + line
            
            # Add the last section
            if current_section and current_content:
                config[current_section] = '\n'.join(current_content).strip()
            
            logger.debug(f"Parsed mg_prompt.txt: {list(config.keys())}")
            return config
            
        except Exception as e:
            logger.debug(f"Error parsing mg_prompt.txt: {e}")
            return {}
