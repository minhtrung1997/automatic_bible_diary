#!/usr/bin/env python3
"""Quick diagnostic to verify LCCMN loads and mapping works for today's Psalm reference.
Run with: python -m tests.test_lccmn_mapping
"""

import os
from datetime import datetime
import pytz

from magisterium.magisterium_client import MagisteriumClient
from magisterium.psalm_fetcher import PsalmFetcher


def main():
    os.environ.setdefault('MAGISTERIUM_API_KEY', 'dev-dummy')  # avoids init error

    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    today = datetime.now(vn_tz)
    print(f"Date: {today:%Y-%m-%d}")

    fetcher = PsalmFetcher()
    psalm = fetcher.fetch_daily_psalm(today)
    if not psalm:
        print("Fetch failed.")
        return

    print("Psalm citation:", psalm.get('psalm_citation'))

    mc = MagisteriumClient()
    vi = mc.get_vietnamese_psalm_text(psalm)
    if vi:
        print("VN verses (first 200 chars):", vi[:200].replace('\n', ' '))
    else:
        print("VN verses: NOT FOUND (check LCCMN, parser mapping)")

    # show tokens used by parser
    ref_text = psalm.get('psalm_citation') or ''
    if mc.reference_parser:
        refs = mc.reference_parser.extract_bible_references(ref_text)
        print("Parsed refs:", refs)


if __name__ == '__main__':
    main()
