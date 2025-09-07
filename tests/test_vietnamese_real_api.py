#!/usr/bin/env python3
"""
Integration test for Magisterium Vietnamese content generation
Run this with a real MAGISTERIUM_API_KEY to test actual Vietnamese output.
"""

import os
import sys

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from magisterium.magisterium_client import MagisteriumClient


def test_real_vietnamese_generation():
    """Test actual Vietnamese content generation with real API"""
    
    # Check for API key
    api_key = os.getenv('MAGISTERIUM_API_KEY')
    if not api_key:
        print("❌ MAGISTERIUM_API_KEY not found in environment")
        print("Set your API key with: export MAGISTERIUM_API_KEY=your_key_here")
        return False
    
    print("🔄 Testing real Magisterium API for Vietnamese content generation...")
    print(f"Using API key: {api_key[:8]}...")
    
    # Sample psalm content
    sample_psalm = {
        'psalm_citation': 'Psalm 23:1-3a, 3b-4, 5, 6',
        'psalm_body': '''The Lord is my shepherd, I shall not want.
    He makes me lie down in green pastures;
he leads me beside still waters;
    he restores my soul.

He leads me in right paths
    for his name's sake.
Even though I walk through the darkest valley,
    I fear no evil;
for you are with me;
    your rod and your staff—
    they comfort me.

You prepare a table before me
    in the presence of my enemies;
you anoint my head with oil;
    my cup overflows.
Surely goodness and mercy shall follow me
    all the days of my life,
and I shall dwell in the house of the Lord
    my whole life long.''',
        'psalm_link': 'https://bible.usccb.org/bible/readings/test.cfm',
        'url': 'https://bible.usccb.org/bible/readings/test.cfm',
        'date': '2025-09-07'
    }
    
    try:
        with MagisteriumClient(api_key=api_key) as client:
            print(f"📚 Testing with Psalm: {sample_psalm['psalm_citation']}")
            print("🔄 Generating reflection...")
            
            result = client.generate_psalm_reflection(sample_psalm)
            
            if not result:
                print("❌ Failed to generate reflection - API returned empty result")
                return False
            
            print("✅ Successfully generated Vietnamese reflection!")
            print(f"📄 Content length: {len(result)} characters")
            print("\n" + "="*60)
            print("GENERATED VIETNAMESE REFLECTION:")
            print("="*60)
            print(result)
            print("="*60 + "\n")
            
            # Validate Vietnamese content
            vietnamese_indicators = [
                'Suy niệm',
                'Cầu nguyện', 
                'Thiên Chúa',
                'Chúa',
                'Thánh vịnh'
            ]
            
            found_indicators = [term for term in vietnamese_indicators if term in result]
            
            print("🔍 Vietnamese content validation:")
            print(f"   Found {len(found_indicators)}/{len(vietnamese_indicators)} Vietnamese indicators:")
            for term in found_indicators:
                print(f"   ✅ {term}")
            
            missing = [term for term in vietnamese_indicators if term not in result]
            if missing:
                print("   Missing terms:")
                for term in missing:
                    print(f"   ⚠️  {term}")
            
            # Check structure
            has_meditation = 'Suy niệm' in result
            has_prayer = 'Cầu nguyện' in result
            
            print(f"\n📝 Structure validation:")
            print(f"   Meditation section: {'✅' if has_meditation else '❌'}")
            print(f"   Prayer section: {'✅' if has_prayer else '❌'}")
            
            if has_meditation and has_prayer:
                print("✅ Content follows expected Vietnamese structure!")
                return True
            else:
                print("⚠️  Content structure may need improvement")
                return False
                
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False


def test_vietnamese_bible_integration():
    """Test Vietnamese Bible text integration from LCCMN database"""
    
    api_key = os.getenv('MAGISTERIUM_API_KEY')
    if not api_key:
        print("⏭️  Skipping Vietnamese Bible integration test (no API key)")
        return
    
    print("\n🔄 Testing Vietnamese Bible text integration...")
    
    # Psalm that should be found in LCCMN database
    psalm_with_vietnamese = {
        'psalm_citation': 'Psalm 23:1-2',
        'psalm_body': 'The Lord is my shepherd...',
        'date': '2025-09-07'
    }
    
    try:
        with MagisteriumClient(api_key=api_key) as client:
            # Test Vietnamese text retrieval
            vi_text = client.get_vietnamese_psalm_text(psalm_with_vietnamese)
            
            if vi_text:
                print(f"✅ Found Vietnamese Bible text:")
                print(f"   {vi_text[:100]}...")
                print(f"   Total length: {len(vi_text)} characters")
            else:
                print("⚠️  No Vietnamese Bible text found (this is OK if LCCMN.SQLite3 not available)")
            
            # Test full generation with Vietnamese integration
            result = client.generate_psalm_reflection(psalm_with_vietnamese)
            
            if result and vi_text and vi_text[:50] in result:
                print("✅ Vietnamese Bible text successfully integrated into reflection!")
            elif result:
                print("✅ Reflection generated, but Vietnamese Bible text not detectably included")
            else:
                print("❌ Failed to generate reflection")
                
    except Exception as e:
        print(f"❌ Error during Vietnamese Bible integration test: {e}")


def main():
    """Run the integration tests"""
    print("🧪 Magisterium Vietnamese Content Integration Test")
    print("=" * 50)
    
    # Test 1: Basic Vietnamese generation
    success = test_real_vietnamese_generation()
    
    # Test 2: Vietnamese Bible integration  
    test_vietnamese_bible_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Integration test completed successfully!")
        print("💡 The Magisterium client can generate Vietnamese content.")
    else:
        print("⚠️  Integration test completed with issues.")
        print("💡 Check API key and network connection.")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
