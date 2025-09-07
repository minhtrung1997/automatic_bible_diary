#!/usr/bin/env python3
"""
Test script for enhanced Gemini client with Vietnamese Bible verses
"""

import os
from config import Config
from gemini_client import GeminiClient

def test_vietnamese_bible_integration():
    """Test the Vietnamese Bible integration with Gemini"""
    
    # Sample bible content (like what would come from bible_fetcher.py)
    sample_bible_content = {
        'date': 'Sunday, September 1, 2025',
        'gospel_citation': 'Matthew 5:3-8',
        'gospel_body': '''Blessed are the poor in spirit, for theirs is the kingdom of heaven.
Blessed are those who mourn, for they will be comforted.
Blessed are the meek, for they will inherit the earth.
Blessed are those who hunger and thirst for righteousness, for they will be filled.
Blessed are the merciful, for they will be shown mercy.
Blessed are the pure in heart, for they will see God.''',
        'Gospel': 'Matthew 5:3-8 - The Beatitudes'
    }
    
    print("=== Testing Vietnamese Bible Integration ===")
    print("Sample Bible Content:")
    for key, value in sample_bible_content.items():
        print(f"  {key}: {value}")
    
    print("\n=== Testing Content Enrichment ===")
    
    try:
        config = Config()
        
        # Test without generating full diary entry to save tokens
        with GeminiClient(config.gemini_api_key) as gemini_client:
            # Test the enrichment process
            enriched_content = gemini_client._enrich_with_vietnamese_verses(sample_bible_content)
            
            print("Enriched Content:")
            for key, value in enriched_content.items():
                print(f"  {key}: {value}")
            
            print("\n=== Testing Formatted Content ===")
            formatted_content = gemini_client._format_bible_content(sample_bible_content)
            print("Formatted for Gemini:")
            print(formatted_content)
            
    except Exception as e:
        print(f"Error during test: {e}")


if __name__ == "__main__":
    test_vietnamese_bible_integration()
