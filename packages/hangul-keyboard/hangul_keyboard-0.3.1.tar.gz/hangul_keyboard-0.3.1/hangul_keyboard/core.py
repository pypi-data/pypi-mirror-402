from .mapping import (
    ROMAN_TO_JAMO,
    DOUBLE_JAMO_PAIR,
    CHOSUNGS,
    JOONGSUNGS,
    JONGSUNGS,
)


def roman_keystrokes_to_jamo(text: str) -> str:
    """
    Convert roman keyboard input (e.g. dkssud) into Korean jamo sequence.
    """
    i = 0
    result = []

    while i < len(text):
        pair = text[i:i + 2]

        if pair in DOUBLE_JAMO_PAIR:
            result.append(DOUBLE_JAMO_PAIR[pair])
            i += 2
            continue

        result.append(ROMAN_TO_JAMO.get(text[i], text[i]))
        i += 1

    return "".join(result)

# ===== 자모 -> 한글 완성 =====
def compose_hangul(jamo_text: str) -> str:
    """
    Compose jamo sequence into complete Hangul syllables.
    """
    result = []
    i = 0
    length = len(jamo_text)

    while i < length:
        initial = jamo_text[i]

        # Not a valid initial consonant
        if initial not in CHOSUNGS:
            result.append(initial)
            i += 1
            continue

        # No valid vowel → cannot form syllable
        if i + 1 >= length or jamo_text[i + 1] not in JOONGSUNGS:
            result.append(initial)
            i += 1
            continue

        medial = jamo_text[i + 1]
        final = '_'

        # Check final consonant candidate
        if i + 2 < length and jamo_text[i + 2] in JONGSUNGS[1:]:
            # Lookahead: next char is vowel → next syllable
            if i + 3 < length and jamo_text[i + 3] in JOONGSUNGS:
                i += 2
            else:
                final = jamo_text[i + 2]
                i += 3
        else:
            i += 2

        syllable = _build_syllable(initial, medial, final)
        result.append(syllable)

    return "".join(result)


def _build_syllable(cho: str, jung: str, jong: str) -> str:
    """
    Build a Hangul syllable from jamo indices.
    """
    cho_idx = CHOSUNGS.index(cho)
    jung_idx = JOONGSUNGS.index(jung)
    jong_idx = JONGSUNGS.index(jong)

    return chr(0xAC00 + cho_idx * 21 * 28 + jung_idx * 28 + jong_idx)

def convert_roman_to_hangul(text: str) -> str:
    """
    Convert roman keystrokes into Hangul.
    If input already contains Hangul, return as-is.
    """
    if all(0xAC00 <= ord(c) <= 0xD7A3 or not c.isalpha() for c in text):
        return text

    jamo = roman_keystrokes_to_jamo(text)
    return compose_hangul(jamo)

def decompose_hangul_full(text: str) -> list[str]:
    """
    Decompose Hangul syllables into jamo sequence.
    Non-Hangul characters are returned as-is.
    """
    result = []

    for char in text:
        code = ord(char)

        if 0xAC00 <= code <= 0xD7A3:
            syllable_index = code - 0xAC00
            cho_idx = syllable_index // (21 * 28)
            jung_idx = (syllable_index % (21 * 28)) // 28
            jong_idx = syllable_index % 28

            result.append(CHOSUNGS[cho_idx])
            result.append(JOONGSUNGS[jung_idx])

            if jong_idx != 0:
                result.append(JONGSUNGS[jong_idx])

        else:
            result.append(char)

    return result

def decompose_hangul_str(text: str) -> str:
    """
    Decompose Hangul syllables into jamo sequence string.
    Non-Hangul characters are returned as-is.
    """
    return "".join(decompose_hangul_full(text))

if __name__ == "__main__":
    pass