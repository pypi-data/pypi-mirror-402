"""
Roman keyboard → Hangul jamo
Based on Korean 2-set keyboard layout
"""

ROMAN_TO_JAMO = {
    # Initial consonants (Choseong)
    'r': 'ㄱ', 's': 'ㄴ', 'e': 'ㄷ', 'f': 'ㄹ',
    'a': 'ㅁ', 'q': 'ㅂ', 't': 'ㅅ', 'd': 'ㅇ',
    'w': 'ㅈ', 'c': 'ㅊ', 'z': 'ㅋ', 'x': 'ㅌ',
    'v': 'ㅍ', 'g': 'ㅎ',
    # Double initial consonants (Choseong)
    'R': 'ㄲ', 'E': 'ㄸ', 'Q': 'ㅃ', 'T': 'ㅆ', 'W': 'ㅉ',

    # Medial vowels (Jungseong)
    'k': 'ㅏ', 'o': 'ㅐ', 'i': 'ㅑ', 'O': 'ㅒ', 'j': 'ㅓ',
    'p': 'ㅔ', 'u': 'ㅕ', 'P': 'ㅖ', 'h': 'ㅗ', 'y': 'ㅛ',
    'n': 'ㅜ', 'b': 'ㅠ', 'm': 'ㅡ', 'l': 'ㅣ',
}


DOUBLE_JAMO_PAIR = {
    # Compound vowels
    'hk': 'ㅘ', 'ho': 'ㅙ', 'hl': 'ㅚ',
    'nj': 'ㅝ', 'np': 'ㅞ', 'nl': 'ㅟ',
    'ml': 'ㅢ',

    # Compound final consonants (Jongseong)
    'rt': 'ㄳ', 'sw': 'ㄵ', 'sg': 'ㄶ',
    'fr': 'ㄺ', 'fa': 'ㄻ', 'fq': 'ㄼ',
    'ft': 'ㄽ', 'fx': 'ㄾ', 'fv': 'ㄿ', 'fg': 'ㅀ',
    'qt': 'ㅄ',
}


# Hangul Jamo tables (Unicode order)
CHOSUNGS = [
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ',
    'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ',
    'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ',
]

JOONGSUNGS = [
    'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ',
    'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ',
    'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ',
    'ㅡ', 'ㅢ', 'ㅣ',
]

JONGSUNGS = [
    '_', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ',
    'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ',
    'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ',
    'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ',
    'ㅌ', 'ㅍ', 'ㅎ',
]