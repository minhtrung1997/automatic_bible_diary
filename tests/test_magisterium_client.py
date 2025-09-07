#!/usr/bin/env python3
"""
Magisterium API Client
Generates a Catholic reflection for the Responsorial Psalm.
"""

import os
import logging
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


class MagisteriumClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "magisterium-1",
        base_url: str = "https://www.magisterium.com/api/v1/chat/completions",
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("MAGISTERIUM_API_KEY")
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def generate_psalm_reflection(self, psalm: Dict[str, str]) -> Optional[str]:
        """
        psalm dict keys expected:
          - psalm_citation (optional, str)
          - psalm_body (required, str)
          - date (optional, str)
        """
        if not self.api_key:
            logger.error("MAGISTERIUM_API_KEY is not set")
            return None

        body = (psalm or {}).get("psalm_body")
        if not body or not isinstance(body, str):
            logger.warning("No psalm_body provided")
            return None

        citation = (psalm or {}).get("psalm_citation", "").strip()
        date_str = (psalm or {}).get("date", "").strip()

        user_prompt = self._build_prompt(body, citation, date_str)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(self.base_url, headers=headers, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                logger.error(f"Magisterium API HTTP {resp.status_code}: {resp.text[:300]}")
                return None

            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                logger.warning("Magisterium API returned no choices")
                return None

            # Expected structure per docs/tests:
            # choices: [{ "message": { "content": "..." } }]
            msg = choices[0].get("message") or {}
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()

            logger.warning("Magisterium API response missing message.content")
            return None
        except requests.RequestException as e:
            logger.error(f"Magisterium API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Magisterium API parsing error: {e}")
            return None

    def _build_prompt(self, psalm_body: str, citation: str, date_str: str) -> str:
        parts = []
        if date_str:
            parts.append(f"Date: {date_str}")
        if citation:
            parts.append(f"Responsorial Psalm: {citation}")
        parts.append("Text:")
        parts.append(psalm_body.strip())
        parts.append(
            "Please write a concise Catholic reflection (150-250 words) grounded in Church teaching and the Psalm’s themes."
        )
        return "\n\n".join(parts)