#!/usr/bin/env python3
"""
Bible Book Mappings Module
Shared English to Vietnamese book name mappings used by both parser and database modules.
"""

# English to Vietnamese short name mappings
# Short names match the database short_name column exactly for reliable matching
BOOK_MAPPINGS = {
    # Old Testament - Pentateuch
    'genesis': 'Kn', 'gen': 'Kn',
    'exodus': 'Xh', 'exod': 'Xh', 'ex': 'Xh',
    'leviticus': 'Lv', 'lev': 'Lv',
    'numbers': 'Ds', 'num': 'Ds', 'nm': 'Ds',
    'deuteronomy': 'Tl', 'deut': 'Tl', 'dt': 'Tl',
    
    # Old Testament - Historical Books
    'joshua': 'Yôs', 'josh': 'Yôs', 'jos': 'Yôs',
    'judges': 'Tp', 'judg': 'Tp', 'jdg': 'Tp',
    'ruth': 'R', 'ru': 'R', 'rut': 'R',
    '1 samuel': '1Sm', '1 sam': '1Sm', '1sam': '1Sm', '1sm': '1Sm',
    '2 samuel': '2Sm', '2 sam': '2Sm', '2sam': '2Sm', '2sm': '2Sm',
    '1 kings': '1V', '1 kgs': '1V', '1kgs': '1V', '1ki': '1V',
    '2 kings': '2V', '2 kgs': '2V', '2kgs': '2V', '2ki': '2V',
    '1 chronicles': '1Sb', '1 chr': '1Sb', '1chr': '1Sb', '1ch': '1Sb',
    '2 chronicles': '2Sb', '2 chr': '2Sb', '2chr': '2Sb', '2ch': '2Sb',
    'ezra': 'Ezr', 'ezr': 'Ezr',
    'nehemiah': 'Nkm', 'neh': 'Nkm', 'ne': 'Nkm',
    'esther': 'Est', 'est': 'Est', 'esth': 'Est',
    
    # Old Testament - Wisdom Books
    'job': 'Yob', 'jb': 'Yob',
    'psalms': 'Tv', 'psalm': 'Tv', 'ps': 'Tv', 'pss': 'Tv',
    'proverbs': 'Cn', 'prov': 'Cn', 'pr': 'Cn',
    'ecclesiastes': 'Gv', 'eccl': 'Gv', 'ecc': 'Gv', 'eccles': 'Gv',
    'song of solomon': 'Hc', 'song of songs': 'Hc', 'song': 'Hc', 'sos': 'Hc', 'ss': 'Hc',
    
    # Old Testament - Major Prophets
    'isaiah': 'Is', 'isa': 'Is', 'is': 'Is',
    'jeremiah': 'Gr', 'jer': 'Gr', 'je': 'Gr',
    'lamentations': 'Ac', 'lam': 'Ac', 'la': 'Ac',
    'ezekiel': 'Êz', 'ezek': 'Êz', 'eze': 'Êz',
    'daniel': 'Ðn', 'dan': 'Ðn', 'da': 'Ðn',
    
    # Old Testament - Minor Prophets
    'hosea': 'Hs', 'hos': 'Hs',
    'joel': 'Ge', 'joe': 'Ge', 'jl': 'Ge',
    'amos': 'Am', 'am': 'Am',
    'obadiah': 'Ôv', 'obad': 'Ôv', 'ob': 'Ôv',
    'jonah': 'Gn', 'jon': 'Gn', 'jnh': 'Gn',
    'micah': 'Mc', 'mic': 'Mc', 'mi': 'Mc',
    'nahum': 'Nk', 'nah': 'Nk', 'na': 'Nk',
    'habakkuk': 'Kb', 'hab': 'Kb', 'hb': 'Kb',
    'zephaniah': 'Xp', 'zeph': 'Xp', 'zep': 'Xp',
    'haggai': 'Hag', 'hag': 'Hag', 'hg': 'Hag',
    'zechariah': 'Dcr', 'zech': 'Dcr', 'zec': 'Dcr',
    'malachi': 'Ml', 'mal': 'Ml',

    # New Testament - Gospels and Acts
    'matthew': 'Mt', 'matt': 'Mt', 'mt': 'Mt',
    'mark': 'Mk', 'mk': 'Mk', 'mr': 'Mk',
    'luke': 'Lc', 'lk': 'Lc', 'lu': 'Lc',
    # John-family books vary by DB schema; primary mapping stays on Ga-family,
    # and BibleDatabase applies fallback resolution when verses are not found.
    'john': 'Ga', 'jn': 'Ga', 'joh': 'Ga',
    'acts': 'Cv', 'act': 'Cv', 'ac': 'Cv',
    
    # New Testament - Pauline Epistles
    'romans': 'Rm', 'rom': 'Rm', 'ro': 'Rm',
    '1 corinthians': '1Cr', '1 cor': '1Cr', '1cor': '1Cr', '1co': '1Cr',
    '2 corinthians': '2Cr', '2 cor': '2Cr', '2cor': '2Cr', '2co': '2Cr',
    'galatians': 'Gl', 'gal': 'Gl', 'ga': 'Gl',
    'ephesians': 'Ep', 'eph': 'Ep',
    'philippians': 'Pl', 'phil': 'Pl', 'php': 'Pl',
    'colossians': 'Cl', 'col': 'Cl',
    '1 thessalonians': '1Tx', '1 thess': '1Tx', '1thess': '1Tx', '1th': '1Tx',
    '2 thessalonians': '2Tx', '2 thess': '2Tx', '2thess': '2Tx', '2th': '2Tx',
    '1 timothy': '1Tm', '1 tim': '1Tm', '1tim': '1Tm', '1ti': '1Tm',
    '2 timothy': '2Tm', '2 tim': '2Tm', '2tim': '2Tm', '2ti': '2Tm',
    'titus': 'Tt', 'tit': 'Tt', 'tt': 'Tt',
    'philemon': 'Plm', 'phlm': 'Plm', 'phm': 'Plm',
    
    # New Testament - General Epistles
    'hebrews': 'Dt', 'heb': 'Dt',
    'james': 'Gc', 'jas': 'Gc', 'jam': 'Gc',
    '1 peter': '1Pr', '1 pet': '1Pr', '1pet': '1Pr', '1pe': '1Pr',
    '2 peter': '2Pr', '2 pet': '2Pr', '2pet': '2Pr', '2pe': '2Pr',
    '1 john': '1Ga', '1 jn': '1Ga', '1jn': '1Ga', '1jo': '1Ga',
    '2 john': '2Ga', '2 jn': '2Ga', '2jn': '2Ga', '2jo': '2Ga',
    '3 john': '3Ga', '3 jn': '3Ga', '3jn': '3Ga', '3jo': '3Ga',
    'jude': 'Gđ', 'jud': 'Gđ',
    
    # New Testament - Apocalyptic
    'revelation': 'Kh', 'rev': 'Kh', 're': 'Kh',
}
