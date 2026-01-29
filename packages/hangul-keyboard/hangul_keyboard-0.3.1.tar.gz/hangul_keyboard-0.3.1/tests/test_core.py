import unittest
from hangul_keyboard.core import (
    decompose_hangul_full,
    decompose_hangul_str,
    roman_keystrokes_to_jamo,
    compose_hangul,
    convert_roman_to_hangul,
)


class TestRomanKeystrokesToJamo(unittest.TestCase):
    """로마자 키 입력 → 자모 시퀀스"""

    """단일 문자"""
    def test_single_consonant(self):
        self.assertEqual(roman_keystrokes_to_jamo("r"), "ㄱ")
        self.assertEqual(roman_keystrokes_to_jamo("s"), "ㄴ")
        self.assertEqual(roman_keystrokes_to_jamo("e"), "ㄷ")
        self.assertEqual(roman_keystrokes_to_jamo("t"), "ㅅ")

    def test_single_vowel(self):
        self.assertEqual(roman_keystrokes_to_jamo("k"), "ㅏ")
        self.assertEqual(roman_keystrokes_to_jamo("o"), "ㅐ")
        self.assertEqual(roman_keystrokes_to_jamo("i"), "ㅑ")

    """쌍자모 (단독)"""
    def test_double_initial(self):
        self.assertEqual(roman_keystrokes_to_jamo("R"), "ㄲ")
        self.assertEqual(roman_keystrokes_to_jamo("E"), "ㄸ")
        self.assertEqual(roman_keystrokes_to_jamo("Q"), "ㅃ")
        self.assertEqual(roman_keystrokes_to_jamo("T"), "ㅆ")
        self.assertEqual(roman_keystrokes_to_jamo("W"), "ㅉ")

    """2글자 복합 자모"""
    def test_compound_medial_vowel(self):
        self.assertEqual(roman_keystrokes_to_jamo("hk"), "ㅘ")
        self.assertEqual(roman_keystrokes_to_jamo("ho"), "ㅙ")
        self.assertEqual(roman_keystrokes_to_jamo("hl"), "ㅚ")
        self.assertEqual(roman_keystrokes_to_jamo("nj"), "ㅝ")
        self.assertEqual(roman_keystrokes_to_jamo("ml"), "ㅢ")

    def test_compound_final_consonant(self):
        self.assertEqual(roman_keystrokes_to_jamo("rt"), "ㄳ")
        self.assertEqual(roman_keystrokes_to_jamo("sw"), "ㄵ")
        self.assertEqual(roman_keystrokes_to_jamo("qt"), "ㅄ")

    """시퀀스"""
    def test_sequence(self):
        self.assertEqual(roman_keystrokes_to_jamo("rk"), "ㄱㅏ")
        self.assertEqual(roman_keystrokes_to_jamo("rko"), "ㄱㅏㅐ")
        self.assertEqual(roman_keystrokes_to_jamo("rkrt"), "ㄱㅏㄳ")

    """엣지 케이스"""
    def test_empty_string(self):
        self.assertEqual(roman_keystrokes_to_jamo(""), "")

    def test_unmapped_character(self):
        self.assertEqual(roman_keystrokes_to_jamo("1"), "1")
        self.assertEqual(roman_keystrokes_to_jamo("!"), "!")


class TestComposeHangul(unittest.TestCase):
    """자모 시퀀스 → 한글 음절"""

    """기본 조합"""
    def test_simple_syllable(self):
        self.assertEqual(compose_hangul("ㄱㅏ"), "가")
        self.assertEqual(compose_hangul("ㄴㅡ"), "느")
        self.assertEqual(compose_hangul("ㅅㅏ"), "사")
        self.assertEqual(compose_hangul("ㄹㅏ"), "라")

    """종성"""
    def test_single_final(self):
        self.assertEqual(compose_hangul("ㄱㅏㄱ"), "각")
        self.assertEqual(compose_hangul("ㄷㅏㄹ"), "달")
        self.assertEqual(compose_hangul("ㄹㅏㄴ"), "란")

    def test_double_final(self):
        """유니코드상 유효하지만 실사용은 드묾"""
        self.assertEqual(compose_hangul("ㄱㅏㄲ"), "갂")
        self.assertEqual(compose_hangul("ㄱㅏㅆ"), "갔")

    """쌍초성"""
    def test_double_initial(self):
        self.assertEqual(compose_hangul("ㄲㅏ"), "까")
        self.assertEqual(compose_hangul("ㄸㅏ"), "따")
        self.assertEqual(compose_hangul("ㅃㅏ"), "빠")

    """복합 중성"""
    def test_compound_vowel(self):
        self.assertEqual(compose_hangul("ㄱㅘ"), "과")
        self.assertEqual(compose_hangul("ㄴㅝ"), "눠")
        self.assertEqual(compose_hangul("ㄹㅢ"), "릐")

    """엣지 케이스"""
    def test_empty_string(self):
        self.assertEqual(compose_hangul(""), "")

    def test_only_consonant(self):
        self.assertEqual(compose_hangul("ㄱ"), "ㄱ")

    def test_unmapped_character(self):
        self.assertEqual(compose_hangul("1ㄱㅏ"), "1가")

    """다중 음절"""
    def test_multiple_syllables(self):
        self.assertEqual(compose_hangul("ㄱㅏㄱㄴㅡㄴ"), "각는")


class TestConvertRomanToHangul(unittest.TestCase):
    """로마자 입력 → 최종 한글"""

    """기본"""  
    def test_basic_word(self):
        self.assertEqual(convert_roman_to_hangul("rk"), "가")
        self.assertEqual(convert_roman_to_hangul("tks"), "산")

    """실제 입력"""
    def test_real_sentence(self):
        self.assertEqual(convert_roman_to_hangul("gksrmf"), "한글")
        self.assertEqual(convert_roman_to_hangul("dkssudgktpdy"), "안녕하세요")

    """한글 입력"""
    def test_hangul_input(self):
        self.assertEqual(convert_roman_to_hangul("한글"), "한글")
        self.assertEqual(convert_roman_to_hangul("가"), "가")

    """특수문자"""    
    def test_with_numbers(self):
        self.assertEqual(convert_roman_to_hangul("rk123"), "가123")

    def test_with_special_chars(self):
        self.assertEqual(convert_roman_to_hangul("rk!"), "가!")
        self.assertEqual(convert_roman_to_hangul("tks?"), "산?")

    def test_with_spaces(self):
        self.assertEqual(convert_roman_to_hangul("rk tks"), "가 산")

    # 엣지 케이스
    def test_empty_string(self):
        self.assertEqual(convert_roman_to_hangul(""), "")

class TestDecomposeHangul(unittest.TestCase):
    """한글 음절 → 자모 분해"""

    def test_full_list(self):
        """종성 포함 리스트"""
        self.assertEqual(decompose_hangul_full("가"), ['ㄱ','ㅏ'])
        self.assertEqual(decompose_hangul_full("각"), ['ㄱ','ㅏ','ㄱ'])
        self.assertEqual(decompose_hangul_full("한글"), ['ㅎ','ㅏ','ㄴ','ㄱ','ㅡ','ㄹ'])
        self.assertEqual(decompose_hangul_full("123"), ['1','2','3'])
        self.assertEqual(decompose_hangul_full(""), [])

    def test_str_version(self):
        """문자열 버전"""
        self.assertEqual(decompose_hangul_str("가"), 'ㄱㅏ')
        self.assertEqual(decompose_hangul_str("각"), 'ㄱㅏㄱ')
        self.assertEqual(decompose_hangul_str("한글"), 'ㅎㅏㄴㄱㅡㄹ')
        self.assertEqual(decompose_hangul_str("123"), '123')
        self.assertEqual(decompose_hangul_str(""), '')


if __name__ == "__main__":
    unittest.main()