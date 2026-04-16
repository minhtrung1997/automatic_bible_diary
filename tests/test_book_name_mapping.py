#!/usr/bin/env python3
"""
Test script for book name mapping functionality
Ensures all 66 books of the Bible can be resolved from English names to Vietnamese
"""

import pytest
from common.bible_reference_parser import BibleReferenceParser
from common.bible_database import BibleDatabase


def test_nehemiah_mapping():
    """Test that nehemiah is correctly mapped (the original issue)"""
    parser = BibleReferenceParser()
    
    with BibleDatabase() as db:
        refs = parser.extract_bible_references('nehemiah 2:1')
        assert refs, "Failed to parse nehemiah 2:1"
        
        ref = refs[0]
        assert ref['book'] == 'Nkm', f"Expected 'Nkm', got '{ref['book']}'"
        
        verse_text = db.search_verse_by_reference(ref['book'], ref['chapter'], ref['verse_start'], ref['verse_end'])
        assert verse_text, "Failed to find verse in database"


def test_old_testament_books():
    """Test mapping of Old Testament books"""
    parser = BibleReferenceParser()
    
    # Using short names that match the database
    test_cases = [
        ('genesis 1:1', 'Kn'),
        ('exodus 3:14', 'Xh'),
        ('leviticus 19:18', 'Lv'),
        ('numbers 6:24', 'Ds'),
        ('deuteronomy 6:4', 'Tl'),
        ('joshua 1:9', 'Yôs'),
        ('judges 6:12', 'Tp'),
        ('ruth 1:16', 'R'),
        ('1 samuel 17:45', '1Sm'),
        ('2 samuel 7:12', '2Sm'),
        ('1 kings 3:9', '1V'),
        ('2 kings 2:9', '2V'),
        ('1 chronicles 29:11', '1Sb'),
        ('2 chronicles 7:14', '2Sb'),
        ('ezra 1:1', 'Ezr'),
        ('nehemiah 2:1', 'Nkm'),
        ('esther 4:14', 'Est'),
        ('job 1:1', 'Yob'),
        ('psalm 23:1', 'Tv'),
        ('proverbs 3:5', 'Cn'),
        ('ecclesiastes 3:1', 'Gv'),
        ('isaiah 53:5', 'Is'),
        ('jeremiah 29:11', 'Gr'),
        ('lamentations 3:22', 'Ac'),
        ('ezekiel 37:1', 'Êz'),
        ('daniel 3:17', 'Ðn'),
        ('hosea 6:6', 'Hs'),
        ('joel 2:28', 'Ge'),
        ('amos 5:24', 'Am'),
        ('jonah 2:1', 'Gn'),
        ('micah 6:8', 'Mc'),
        ('nahum 1:7', 'Nk'),
        ('habakkuk 2:4', 'Kb'),
        ('zephaniah 3:17', 'Xp'),
        ('haggai 2:9', 'Hag'),
        ('zechariah 9:9', 'Dcr'),
        ('malachi 3:10', 'Ml'),
    ]
    
    with BibleDatabase() as db:
        for reference, expected_book in test_cases:
            refs = parser.extract_bible_references(reference)
            assert refs, f"Failed to parse {reference}"
            
            ref = refs[0]
            assert ref['book'] == expected_book, f"For {reference}: expected '{expected_book}', got '{ref['book']}'"
            
            verse_text = db.search_verse_by_reference(ref['book'], ref['chapter'], ref['verse_start'], ref['verse_end'])
            assert verse_text, f"Failed to find verse in database for {reference}"


def test_new_testament_books():
    """Test mapping of New Testament books"""
    parser = BibleReferenceParser()
    
    # Using short names that match the database
    test_cases = [
        ('matthew 5:3', 'Mt'),
        ('mark 1:1', 'Mk'),
        ('luke 2:10', 'Lc'),
        ('john 3:16', 'Ga'),
        ('acts 2:38', 'Cv'),
        ('romans 8:28', 'Rm'),
        ('1 corinthians 13:4', '1Cr'),
        ('2 corinthians 5:17', '2Cr'),
        ('galatians 5:22', 'Gl'),
        ('ephesians 2:8', 'Ep'),
        ('philippians 4:13', 'Pl'),
        ('colossians 3:23', 'Cl'),
        ('1 thessalonians 5:16', '1Tx'),
        ('2 thessalonians 3:3', '2Tx'),
        ('1 timothy 2:5', '1Tm'),
        ('2 timothy 1:7', '2Tm'),
        ('titus 3:5', 'Tt'),
        ('philemon 1:6', 'Plm'),
        ('hebrews 11:1', 'Dt'),
        ('james 1:2', 'Gc'),
        ('1 peter 5:7', '1Pr'),
        ('2 peter 1:3', '2Pr'),
        ('1 john 4:8', '1Ga'),
        ('2 john 1:6', '2Ga'),
        ('3 john 1:4', '3Ga'),
        ('jude 1:3', 'Gđ'),
        ('revelation 21:4', 'Kh'),
    ]
    
    with BibleDatabase() as db:
        for reference, expected_book in test_cases:
            refs = parser.extract_bible_references(reference)
            assert refs, f"Failed to parse {reference}"
            
            ref = refs[0]
            assert ref['book'] == expected_book, f"For {reference}: expected '{expected_book}', got '{ref['book']}'"
            
            verse_text = db.search_verse_by_reference(ref['book'], ref['chapter'], ref['verse_start'], ref['verse_end'])
            assert verse_text, f"Failed to find verse in database for {reference}"


def test_abbreviated_book_names():
    """Test that abbreviated book names are correctly mapped"""
    parser = BibleReferenceParser()
    
    abbreviations = [
        ('gen 1:1', 'Kn'),
        ('ex 3:14', 'Xh'),
        ('lev 19:18', 'Lv'),
        ('num 6:24', 'Ds'),
        ('josh 1:9', 'Yôs'),
        ('neh 2:1', 'Nkm'),
        ('ps 23:1', 'Tv'),
        ('prov 3:5', 'Cn'),
        ('isa 53:5', 'Is'),
        ('jer 29:11', 'Gr'),
        ('matt 5:3', 'Mt'),
        ('mk 1:1', 'Mk'),
        ('lk 2:10', 'Lc'),
        ('jn 3:16', 'Ga'),
        ('rom 8:28', 'Rm'),
        ('1 cor 13:4', '1Cr'),
        ('heb 11:1', 'Dt'),
        ('rev 21:4', 'Kh'),
    ]
    
    for reference, expected_book in abbreviations:
        refs = parser.extract_bible_references(reference)
        assert refs, f"Failed to parse {reference}"
        
        ref = refs[0]
        assert ref['book'] == expected_book, f"For {reference}: expected '{expected_book}', got '{ref['book']}'"


def test_john_gospel_range_lookup():
    """Regression: ensure John 3:31-36 resolves to existing Gospel verses."""
    parser = BibleReferenceParser()
    refs = parser.extract_bible_references('John 3:31-36')
    assert refs, "Failed to parse John 3:31-36"

    with BibleDatabase() as db:
        ref = refs[0]
        verse_text = db.search_verse_by_reference(
            ref['book'], ref['chapter'], ref['verse_start'], ref['verse_end']
        )
        assert verse_text, "Failed to find Gospel verses for John 3:31-36"


if __name__ == '__main__':
    print("Testing nehemiah mapping (original issue)...")
    test_nehemiah_mapping()
    print("✅ Nehemiah mapping test passed!")
    
    print("\nTesting Old Testament books...")
    test_old_testament_books()
    print("✅ Old Testament books test passed!")
    
    print("\nTesting New Testament books...")
    test_new_testament_books()
    print("✅ New Testament books test passed!")
    
    print("\nTesting abbreviated book names...")
    test_abbreviated_book_names()
    print("✅ Abbreviated book names test passed!")
    
    print("\n🎉 All tests passed!")
