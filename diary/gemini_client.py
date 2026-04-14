#!/usr/bin/env python3
"""Gemini API client for the diary workflow (Gospel)."""

import google.generativeai as genai
import logging
from typing import Dict, Optional, List
import os
from datetime import datetime
from google.generativeai.types import GenerationConfig

from common.bible_database import BibleDatabase
from common.bible_reference_parser import BibleReferenceParser

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3-flash-preview"


class GeminiClient:
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        env_model = os.getenv("GEMINI_MODEL")
        self.model_name = model or env_model or DEFAULT_MODEL
        self.model = genai.GenerativeModel(self.model_name)
        self.prompt_template = self._load_prompt_template()
        try:
            self.bible_db = BibleDatabase()
            self.reference_parser = BibleReferenceParser()
        except Exception as e:
            logger.warning(f"Could not initialize Bible database: {e}")
            self.bible_db = None
            self.reference_parser = None

    def _load_prompt_template(self) -> str:
        try:
            template_path = os.path.join(os.path.dirname(__file__), 'template_prompt.txt')
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"Could not load template file: {str(e)}, using default")
        return self._get_default_template()

    def _get_default_template(self) -> str:
        return (
            "Please create a thoughtful and personal Bible diary entry based on today's readings.\n\n"
            "Today's Bible Readings:\n{bible_content}\n\n"
            "Please write a diary entry that:\n"
            "1. Reflects on the key themes and messages from today's readings\n"
            "2. Connects the biblical teachings to modern daily life\n"
            "3. Includes personal insights and practical applications\n"
            "4. Maintains a warm, contemplative, and inspiring tone\n"
            "5. Is approximately 300-500 words long\n\n"
            "The diary entry should help the reader:\n"
            "- Understand the deeper meaning of the scriptures\n"
            "- Find practical ways to apply these teachings\n"
            "- Feel encouraged and spiritually uplifted\n"
            "- Connect with God through reflection\n\n"
            "IMPORTANT: When Vietnamese verses (Tiếng Việt) are provided, please reference and reflect on the exact Vietnamese translation rather than paraphrasing or translating back to English.\n"
        )

    def generate_diary_entry(self, bible_content: Dict[str, str]) -> Optional[str]:
        formatted_content = self._format_bible_content(bible_content)
        date_token = self._format_date_for_nkkt(bible_content)
        try:
            prompt = self.prompt_template.format(bible_content=formatted_content, date=date_token)
        except KeyError:
            prompt = f"NKKT:{date_token}\n\n" + formatted_content

        max_tokens_env = os.getenv("GEMINI_MAX_OUTPUT_TOKENS")
        try:
            max_tokens_cfg = int(max_tokens_env) if max_tokens_env else 8000
        except ValueError:
            max_tokens_cfg = 8000

        primary_cfg = GenerationConfig(temperature=0.7, max_output_tokens=max_tokens_cfg)
        text, finish_reasons = self._generate_once(prompt, primary_cfg)
        if text:
            return text
        if any(fr == 2 for fr in finish_reasons) or text is None:
            retry_cfg = GenerationConfig(temperature=0.6, max_output_tokens=min(max_tokens_cfg * 2, 64000))
            text, finish_reasons2 = self._generate_once(prompt, retry_cfg)
            if text:
                return text
            if any(fr == 2 for fr in finish_reasons2):
                shortened_prompt = self._shorten_prompt(prompt)
                retry_cfg2 = GenerationConfig(temperature=0.65, max_output_tokens=min(max_tokens_cfg * 2, 64000))
                text, _ = self._generate_once(shortened_prompt, retry_cfg2)
                if text:
                    return text
        logger.error("Failed to generate diary entry after retries.")
        return None

    def _generate_once(self, prompt: str, gen_config: GenerationConfig) -> tuple[Optional[str], List[int]]:
        try:
            response = self.model.generate_content([prompt], generation_config=gen_config)
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return None, []
        finish_reasons: List[int] = []
        collected: List[str] = []
        candidates = getattr(response, "candidates", None)
        if not candidates:
            try:
                fallback = getattr(response, 'text', None)
                if fallback:
                    return fallback.strip(), finish_reasons
            except Exception:
                pass
            logger.warning("No candidates returned by Gemini API.")
            return None, finish_reasons
        for idx, c in enumerate(candidates):
            fr = getattr(c, 'finish_reason', None)
            if fr is not None:
                finish_reasons.append(fr)
            content = getattr(c, 'content', None)
            parts = getattr(content, 'parts', None) if content else None
            if parts:
                for p in parts:
                    txt = getattr(p, 'text', '')
                    if txt:
                        collected.append(txt)
        if not collected:
            try:
                fallback = response.text
                if fallback:
                    return fallback.strip(), finish_reasons
            except Exception:
                pass
            return None, finish_reasons
        merged = "\n".join(collected).strip()
        return (merged if merged else None), finish_reasons

    def _format_date_for_nkkt(self, bible_content: Dict[str, str]) -> str:
        raw = bible_content.get('date')
        if raw:
            for fmt in ("%A, %B %d, %Y", "%Y-%m-%d", "%d/%m/%Y"):
                try:
                    dt = datetime.strptime(raw, fmt)
                    return f"{dt.day}/{dt.month}/{dt.year}"
                except Exception:
                    continue
        now = datetime.now()
        return f"{now.day}/{now.month}/{now.year}"

    def _shorten_prompt(self, prompt: str) -> str:
        if len(prompt) <= 3300:
            return prompt
        head = prompt[:2500]
        tail = prompt[-800:]
        return head + "\n\n[...truncated Bible text for brevity to allow full diary generation...]\n\n" + tail

    def _enrich_with_vietnamese_verses(self, bible_content: Dict[str, str]) -> Dict[str, str]:
        if not self.bible_db or not self.reference_parser:
            return bible_content
        enriched_content = bible_content.copy()
        try:
            gospel_text = bible_content.get('Gospel', '') or bible_content.get('gospel_citation', '')
            if gospel_text:
                references = self.reference_parser.extract_bible_references(gospel_text)
                if references:
                    ref = references[0]
                    vietnamese_verse = self.bible_db.search_verse_by_reference(
                        ref['book'], ref['chapter'], ref['verse_start'], ref['verse_end']
                    )
                    if vietnamese_verse:
                        enriched_content['vietnamese_gospel'] = vietnamese_verse
                        enriched_content['gospel_reference'] = f"{ref['book']} {ref['chapter']}:{ref['verse_start']}" + (
                            f"-{ref['verse_end']}" if ref['verse_end'] else ""
                        )
        except Exception as e:
            logger.error(f"Error enriching with Vietnamese verses: {e}")
        return enriched_content

    def _format_bible_content(self, bible_content: Dict[str, str]) -> str:
        enriched_content = self._enrich_with_vietnamese_verses(bible_content)
        parts: List[str] = []
        if 'date' in enriched_content:
            parts.append(f"Date: {enriched_content['date']}")
        citation = enriched_content.get('gospel_citation')
        link = enriched_content.get('gospel_link')
        body = enriched_content.get('gospel_body')
        vietnamese_gospel = enriched_content.get('vietnamese_gospel')
        gospel_reference = enriched_content.get('gospel_reference')
        if citation and body:
            line = citation + (f" ({link})" if link else "")
            parts.append(line)
            parts.append(body)
            if vietnamese_gospel and gospel_reference:
                parts.append(f"\nTiếng Việt ({gospel_reference}):")
                parts.append(vietnamese_gospel)
        else:
            gospel_text = enriched_content.get('Gospel')
            if gospel_text:
                parts.append(gospel_text)
                if vietnamese_gospel and gospel_reference:
                    parts.append(f"\nTiếng Việt ({gospel_reference}):")
                    parts.append(vietnamese_gospel)
        return "\n\n".join(parts).strip()

    def close(self):
        if hasattr(self, 'bible_db') and self.bible_db:
            self.bible_db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
