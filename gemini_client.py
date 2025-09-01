#!/usr/bin/env python3
"""
Gemini API Client Module
Integrates with Google Gemini AI for generating Bible diary entries.

Improvements:
- Configurable model via GEMINI_MODEL env var or constructor arg (default gemini-2.5-flash)
- Robust parsing of response candidates/parts (avoids response.text accessor crash)
- Logs finish_reason & safety blocks for diagnostics
- Retry logic if first attempt yields no text or is MAX_TOKENS truncated
"""

import google.generativeai as genai
import logging
from typing import Dict, Optional, List
import os
from datetime import datetime
from google.generativeai.types import GenerationConfig
from bible_database import BibleDatabase
from bible_reference_parser import BibleReferenceParser

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiClient:
    def __init__(self, api_key: str, model: Optional[str] = None):
        """Initialize Gemini client.

        Args:
            api_key: Google Gemini API key
            model: Optional model name override (e.g. "gemini-2.5-pro")
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)

        # Determine model (env override -> param -> default)
        env_model = os.getenv("GEMINI_MODEL")
        self.model_name = model or env_model or DEFAULT_MODEL
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model '{self.model_name}': {e}")
            raise

        # Load prompt template
        self.prompt_template = self._load_prompt_template()
        
        # Initialize Bible database and reference parser
        try:
            self.bible_db = BibleDatabase()
            self.reference_parser = BibleReferenceParser()
            logger.info("Bible database initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize Bible database: {e}")
            self.bible_db = None
            self.reference_parser = None
        
    def _load_prompt_template(self) -> str:
        """Load prompt template from file"""
        try:
            template_path = os.path.join(os.path.dirname(__file__), 'template_prompt.txt')
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # Default template
                return self._get_default_template()
        except Exception as e:
            logger.warning(f"Could not load template file: {str(e)}, using default")
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Default prompt template"""
        return """
Please create a thoughtful and personal Bible diary entry based on today's readings.

Today's Bible Readings:
{bible_content}

Please write a diary entry that:
1. Reflects on the key themes and messages from today's readings
2. Connects the biblical teachings to modern daily life
3. Includes personal insights and practical applications
4. Maintains a warm, contemplative, and inspiring tone
5. Is approximately 300-500 words long

The diary entry should help the reader:
- Understand the deeper meaning of the scriptures
- Find practical ways to apply these teachings
- Feel encouraged and spiritually uplifted
- Connect with God through reflection

IMPORTANT: When Vietnamese verses (Tiếng Việt) are provided, please reference and reflect on the exact Vietnamese translation rather than paraphrasing or translating back to English. This helps maintain accuracy with the Revised Vietnamese Version (RVV) Bible text.

Please write this as a personal diary entry, using a warm and reflective tone.
"""
    
    def generate_diary_entry(self, bible_content: Dict[str, str]) -> Optional[str]:
        """Generate NKKT entry (Gospel only) using template placeholders {date} & {bible_content}."""
        formatted_content = self._format_bible_content(bible_content)
        date_token = self._format_date_for_nkkt(bible_content)
        try:
            prompt = self.prompt_template.format(bible_content=formatted_content, date=date_token)
        except KeyError as e:
            # Fallback if template still old style lacking placeholders
            logger.warning(f"Template format KeyError {e}; injecting date manually.")
            prompt = f"NKKT:{date_token}\n\n" + formatted_content

        logger.info(f"Generating diary entry with Gemini AI (model={self.model_name}) ...")

        # Determine max tokens (env override)
        max_tokens_env = os.getenv("GEMINI_MAX_OUTPUT_TOKENS")
        try:
            max_tokens_cfg = int(max_tokens_env) if max_tokens_env else 8000
        except ValueError:
            max_tokens_cfg = 8000
        logger.debug(f"Prompt chars={len(prompt)} max_output_tokens={max_tokens_cfg}")

        # First attempt
        primary_cfg = GenerationConfig(temperature=0.7, max_output_tokens=max_tokens_cfg)
        text, finish_reasons = self._generate_once(prompt, primary_cfg)
        if text:
            return text

        # Retry if empty or truncated (finish_reason=2)
        if any(fr == 2 for fr in finish_reasons) or text is None:
            logger.info("Retrying generation with higher token limit and lower temperature ...")
            retry_cfg = GenerationConfig(temperature=0.6, max_output_tokens=min(max_tokens_cfg * 2, 64000))
            text, finish_reasons2 = self._generate_once(prompt, retry_cfg)
            if text:
                return text

            # If still no text and truncated again, try shortening the prompt (remove large scripture body tail)
            if any(fr == 2 for fr in finish_reasons2):
                shortened_prompt = self._shorten_prompt(prompt)
                logger.info("Third attempt with shortened prompt to fit token budget ...")
                retry_cfg2 = GenerationConfig(temperature=0.65, max_output_tokens=min(max_tokens_cfg * 2, 64000))
                text, _ = self._generate_once(shortened_prompt, retry_cfg2)
                if text:
                    return text

        logger.error("Failed to generate diary entry after retries.")
        return None

    def _generate_once(self, prompt: str, gen_config: GenerationConfig) -> tuple[Optional[str], List[int]]:
        """Single generation attempt returning (text, finish_reasons)."""
        try:
            response = self.model.generate_content([prompt], generation_config=gen_config)
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return None, []

        finish_reasons: List[int] = []
        collected: List[str] = []

        candidates = getattr(response, "candidates", None)
        if not candidates:
            # Fallback to response.text if available
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
            logger.debug(f"Candidate {idx} finish_reason={fr}")
            content = getattr(c, 'content', None)
            parts = getattr(content, 'parts', None) if content else None
            if parts:
                for p in parts:
                    txt = getattr(p, 'text', '')
                    if txt:
                        collected.append(txt)
            # Safety blocks logging
            if fr in (3, 6, 7, 8):  # safety / blocked reasons
                logger.warning(f"Candidate {idx} blocked or filtered (finish_reason={fr}).")
            elif fr == 2:  # MAX_TOKENS
                logger.warning("Generation stopped due to max token limit (finish_reason=2).")

        if not collected:
            # Last fallback attempt
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
        """Return date in d/m/YYYY format (no leading zero) similar to sample NKKT:15/8/2025."""
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
        """Heuristically shorten prompt content while keeping instructions.

        Strategy: keep first 2500 characters, last 800 characters (instructions) if available.
        """
        if len(prompt) <= 3300:
            return prompt
        head = prompt[:2500]
        tail = prompt[-800:]
        return head + "\n\n[...truncated Bible text for brevity to allow full diary generation...]\n\n" + tail
    
    def _enrich_with_vietnamese_verses(self, bible_content: Dict[str, str]) -> Dict[str, str]:
        """Enrich Bible content with Vietnamese verses from RVV.SQLite3 database."""
        if not self.bible_db or not self.reference_parser:
            return bible_content
        
        enriched_content = bible_content.copy()
        
        try:
            # Extract Gospel reference from the content
            gospel_text = bible_content.get('Gospel', '') or bible_content.get('gospel_citation', '')
            
            if gospel_text:
                # Parse the reference 
                references = self.reference_parser.extract_bible_references(gospel_text)
                
                if references:
                    ref = references[0]  # Take the first/main reference
                    
                    # Get Vietnamese verse text
                    vietnamese_verse = self.bible_db.search_verse_by_reference(
                        ref['book'], 
                        ref['chapter'], 
                        ref['verse_start'], 
                        ref['verse_end']
                    )
                    
                    if vietnamese_verse:
                        # Add Vietnamese verse to content
                        enriched_content['vietnamese_gospel'] = vietnamese_verse
                        enriched_content['gospel_reference'] = f"{ref['book']} {ref['chapter']}:{ref['verse_start']}"
                        if ref['verse_end']:
                            enriched_content['gospel_reference'] += f"-{ref['verse_end']}"
                        
                        logger.info(f"Added Vietnamese verse for {enriched_content['gospel_reference']}")
                    else:
                        logger.warning(f"Could not find Vietnamese verse for {ref}")
                else:
                    logger.warning("No Bible references found in Gospel text")
            
        except Exception as e:
            logger.error(f"Error enriching with Vietnamese verses: {e}")
        
        return enriched_content
    
    def _format_bible_content(self, bible_content: Dict[str, str]) -> str:
        """Format Bible content for the AI prompt (Gospel only, with Vietnamese verses)."""
        # First enrich with Vietnamese verses
        enriched_content = self._enrich_with_vietnamese_verses(bible_content)
        
        parts: List[str] = []
        if 'date' in enriched_content:
            parts.append(f"Date: {enriched_content['date']}")

        # Prefer structured fields
        citation = enriched_content.get('gospel_citation')
        link = enriched_content.get('gospel_link')
        body = enriched_content.get('gospel_body')
        vietnamese_gospel = enriched_content.get('vietnamese_gospel')
        gospel_reference = enriched_content.get('gospel_reference')
        
        if citation and body:
            line = citation
            if link:
                line += f" ({link})"
            parts.append(line)
            parts.append(body)
            
            # Add Vietnamese verse if available
            if vietnamese_gospel and gospel_reference:
                parts.append(f"\nTiếng Việt ({gospel_reference}):")
                parts.append(vietnamese_gospel)
        else:
            # Fallback to combined 'Gospel' key
            gospel_text = enriched_content.get('Gospel')
            if gospel_text:
                parts.append(gospel_text)
                
                # Add Vietnamese verse if available
                if vietnamese_gospel and gospel_reference:
                    parts.append(f"\nTiếng Việt ({gospel_reference}):")
                    parts.append(vietnamese_gospel)
        
        return "\n\n".join(parts).strip()
    
    def close(self):
        """Close database connections"""
        if self.bible_db:
            self.bible_db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()