#!/usr/bin/env python3
"""
Test script to debug Psalm reference parsing and LCCMN text retrieval
"""

import os
import sys

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.bible_reference_parser import BibleReferenceParser
from common.bible_database import BibleDatabase


def test_psalm_parsing():
    """Test parsing of today's Psalm citation"""
    
    # Sample citation from today
    citation = "Psalm 90:3-4, 5-6, 12-13, 14 and 17"
    
    print(f"📖 Testing citation: {citation}")
    
    parser = BibleReferenceParser()
    references = parser.extract_bible_references(citation)
    
    print(f"\n🔍 Parsed {len(references)} references:")
    for i, ref in enumerate(references):
        print(f"  {i+1}. Book: {ref['book']}")
        print(f"     Chapter: {ref['chapter']}")
        print(f"     Verses: {ref['verse_start']}-{ref['verse_end']}")
        print()
    
    # Test LCCMN database lookup
    try:
        repo_root = os.path.dirname(os.path.dirname(__file__))
        db_path = os.path.join(repo_root, 'database', 'LCCMN.SQLite3')
        
        if os.path.exists(db_path):
            db = BibleDatabase(db_path=db_path, default_filename='LCCMN.SQLite3')
            
            print("📚 LCCMN Database lookup results:")
            for i, ref in enumerate(references):
                print(f"\n--- Reference {i+1}: {ref['book']} {ref['chapter']}:{ref['verse_start']}-{ref['verse_end']} ---")
                
                verse_text = db.search_verse_by_reference(
                    ref['book'], ref['chapter'], ref['verse_start'], ref['verse_end']
                )
                
                if verse_text:
                    print(f"✅ Found: {verse_text}")
                else:
                    print("❌ Not found")
            
            db.close()
        else:
            print("❌ LCCMN.SQLite3 not found")
            
    except Exception as e:
        print(f"❌ Database error: {e}")


def test_full_integration():
    """Test the full integration with MagisteriumClient"""
    
    print("\n" + "="*60)
    print("🧪 Testing full integration with MagisteriumClient")
    print("="*60)
    
    try:
        from magisterium.magisterium_client import MagisteriumClient
        
        # Don't need real API key for this test
        with MagisteriumClient(api_key="test") as client:
            psalm_content = {
                'psalm_citation': 'Psalm 90:3-4, 5-6, 12-13, 14 and 17',
                'psalm_body': 'You turn man back to dust...',
                'date': '2025-09-07'
            }
            
            vi_text = client.get_vietnamese_psalm_text(psalm_content)
            
            if vi_text:
                print(f"✅ Retrieved Vietnamese text ({len(vi_text)} chars):")
                print("-" * 40)
                print(vi_text)
                print("-" * 40)
                
                # Count sections
                sections = vi_text.split('\n\n')
                print(f"\n📊 Found {len(sections)} verse sections")
            else:
                print("❌ No Vietnamese text retrieved")
                
    except Exception as e:
        print(f"❌ Integration test error: {e}")


if __name__ == '__main__':
    test_psalm_parsing()
    test_full_integration()
