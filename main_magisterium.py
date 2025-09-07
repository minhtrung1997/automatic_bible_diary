#!/usr/bin/env python3
"""
Daily Psalm Reflection Automation (Magisterium)
Fetches the Responsorial Psalm, generates a Catholic reflection via Magisterium API,
and sends via email.
"""

import logging
from datetime import datetime
import pytz
import os

from magisterium.config_magisterium import MagisteriumConfig
from magisterium.psalm_fetcher import PsalmFetcher
from magisterium.magisterium_client import MagisteriumClient
from magisterium.email_sender_magisterium import EmailSenderMagisterium

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main() -> bool:
    try:
        config = MagisteriumConfig()
        
        # Check for dry-run mode
        dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        if dry_run:
            logger.info("🔍 DRY RUN MODE - Email will not be sent, output will be printed")

        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_date = datetime.now(vn_tz)
        logger.info(f"Starting Magisterium Psalm reflection for {current_date.strftime('%Y-%m-%d')}")

        fetcher = PsalmFetcher()
        psalm = fetcher.fetch_daily_psalm(current_date)
        if not psalm:
            logger.error("Failed to fetch Responsorial Psalm")
            return False
        
        logger.info(f"📖 Fetched Psalm: {psalm.get('psalm_citation', 'Unknown')}")

        with MagisteriumClient(api_key=config.magisterium_api_key) as mc:
            # Get Vietnamese Bible text first
            vi_text = mc.get_vietnamese_psalm_text(psalm)
            if vi_text:
                logger.info(f"✅ Found Vietnamese LCCMN text ({len(vi_text)} chars)")
                print(f"\n📚 Vietnamese LCCMN Text:\n{vi_text}\n")
            else:
                logger.warning("⚠️  No Vietnamese LCCMN text found")
            
            reflection = mc.generate_psalm_reflection(psalm)
            
        if not reflection:
            logger.error("Failed to generate reflection via Magisterium API")
            return False
        
        logger.info(f"✅ Generated Vietnamese reflection ({len(reflection)} chars)")

        email_sender = EmailSenderMagisterium(config)
        email_payload = {
            'url': psalm.get('url'),
            'psalm_citation': psalm.get('psalm_citation'),
            'psalm_link': psalm.get('psalm_link'),
            'psalm_body': psalm.get('psalm_body'),
        }
        email_subject = f"Daily Psalm Reflection - {current_date.strftime('%B %d, %Y')}"
        
        if dry_run:
            # Generate email body but don't send
            email_body = email_sender._create_email_body(
                email_payload, reflection, current_date, 'Responsorial Psalm', vi_text
            )
            print("\n" + "="*80)
            print("📧 EMAIL PREVIEW (DRY RUN)")
            print("="*80)
            print(f"Subject: {email_subject}")
            print(f"From: {config.email_from}")
            print(f"To: {config.email_to}")
            print("\n📄 HTML Body:")
            print("-" * 40)
            print(email_body)
            print("="*80)
            logger.info("�� DRY RUN completed - Email preview generated")
            return True
        else:
            ok = email_sender.send_psalm_reflection(
                email_payload, reflection, current_date,
                subject=email_subject,
                section_title='Responsorial Psalm',
                vietnamese_text=vi_text
            )
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
