#!/usr/bin/env python3
"""
Daily Bible Diary Automation System
Fetches daily Bible readings, generates AI diary entries, and sends via email
"""

import os
import sys
import logging
from datetime import datetime
import pytz

from bible_fetcher import BibleFetcher
from gemini_client import GeminiClient  
from email_sender import EmailSender
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize configuration
        config = Config()
        
        # Get current date in Vietnam timezone (GMT+7)
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_date = datetime.now(vn_tz)
        
        logger.info(f"Starting daily Bible diary generation for {current_date.strftime('%Y-%m-%d')}")
        
        # Fetch daily Bible reading
        bible_fetcher = BibleFetcher()
        bible_content = bible_fetcher.fetch_daily_reading(current_date)
        
        if not bible_content:
            logger.error("Failed to fetch Bible content")
            return False
            
        logger.info("Successfully fetched Bible readings")
        
        # Generate diary entry using Gemini
        gemini_client = GeminiClient(config.gemini_api_key)
        diary_entry = gemini_client.generate_diary_entry(bible_content)
        
        if not diary_entry:
            logger.error("Failed to generate diary entry")
            return False
            
        logger.info("Successfully generated diary entry")
        
        # Send email
        email_sender = EmailSender(config)
        success = email_sender.send_daily_diary(
            bible_content=bible_content,
            diary_entry=diary_entry,
            date=current_date
        )
        
        if success:
            logger.info("Daily Bible diary sent successfully!")
            return True
        else:
            logger.error("Failed to send email")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error in main process: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)