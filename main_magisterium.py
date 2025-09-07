#!/usr/bin/env python3
"""
Daily Psalm Reflection Automation (Magisterium)
Fetches the Responsorial Psalm, generates a Catholic reflection via Magisterium API,
and sends via email.
"""

import logging
from datetime import datetime
import pytz

from magisterium.config_magisterium import MagisteriumConfig
from magisterium.psalm_fetcher import PsalmFetcher
from magisterium.magisterium_client import MagisteriumClient
from magisterium.email_sender_magisterium import EmailSenderMagisterium

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main() -> bool:
    try:
        config = MagisteriumConfig()

        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_date = datetime.now(vn_tz)
        logger.info(f"Starting Magisterium Psalm reflection for {current_date.strftime('%Y-%m-%d')}")

        fetcher = PsalmFetcher()
        psalm = fetcher.fetch_daily_psalm(current_date)
        if not psalm:
            logger.error("Failed to fetch Responsorial Psalm")
            return False

        with MagisteriumClient(api_key=config.magisterium_api_key) as mc:
            reflection = mc.generate_psalm_reflection(psalm)
        if not reflection:
            logger.error("Failed to generate reflection via Magisterium API")
            return False

        email_sender = EmailSenderMagisterium(config)
        email_payload = {
            'url': psalm.get('url'),
            'psalm_citation': psalm.get('psalm_citation'),
            'psalm_link': psalm.get('psalm_link'),
            'psalm_body': psalm.get('psalm_body'),
        }
        email_subject = f"Daily Psalm Reflection - {current_date.strftime('%B %d, %Y')}"
        ok = email_sender.send_psalm_reflection(email_payload, reflection, current_date,
                                                subject=email_subject,
                                                section_title='Responsorial Psalm')
        if ok:
            logger.info("Magisterium Psalm reflection sent successfully")
            return True
        logger.error("Email send failed")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in Magisterium main: {e}")
        return False


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
