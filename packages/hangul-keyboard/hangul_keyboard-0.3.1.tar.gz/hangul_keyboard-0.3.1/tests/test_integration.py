import unittest
from hangul_keyboard.core import convert_roman_to_hangul, decompose_hangul_full, decompose_hangul_str


class TestIntegration(unittest.TestCase):
    """통합 테스트: 실제 사용자 입력 시나리오"""

    def test_basic_words(self):
        """기본 단어 변환"""
        self.assertEqual(convert_roman_to_hangul("gksrmf"), "한글")
        self.assertEqual(convert_roman_to_hangul("rk"), "가")
        self.assertEqual(convert_roman_to_hangul("tks"), "산")
        self.assertEqual(convert_roman_to_hangul("whsrud"), "존경")

    def test_double_initial_consonants(self):
        """쌍초성 단어"""
        self.assertEqual(convert_roman_to_hangul("RkR"), "깎")
        self.assertEqual(convert_roman_to_hangul("Ek"), "따")
        self.assertEqual(convert_roman_to_hangul("Qk"), "빠")
        self.assertEqual(convert_roman_to_hangul("Tk"), "싸")
        self.assertEqual(convert_roman_to_hangul("Wk"), "짜")

    def test_final_consonants(self):
        """종성이 포함된 단어"""
        self.assertEqual(convert_roman_to_hangul("tks"), "산")
        self.assertEqual(convert_roman_to_hangul("rkf"), "갈")
        self.assertEqual(convert_roman_to_hangul("gkd"), "항")
        self.assertEqual(convert_roman_to_hangul("rkd"), "강")

    def test_compound_vowels(self):
        """복합 중성이 포함된 단어"""
        self.assertEqual(convert_roman_to_hangul("rhl"), "괴")
        self.assertEqual(convert_roman_to_hangul("rhk"), "과")
        self.assertEqual(convert_roman_to_hangul("rnj"), "궈")
        self.assertEqual(convert_roman_to_hangul("rnp"), "궤")

    def test_compound_finals(self):
        """복합 종성이 포함된 단어"""
        self.assertEqual(convert_roman_to_hangul("rkqt"), "값")
        self.assertEqual(convert_roman_to_hangul("rkx"), "같")
        self.assertEqual(convert_roman_to_hangul("tkfa"), "삶")

    def test_sentence(self):
        """짧은 문장"""
        self.assertEqual(convert_roman_to_hangul("gksrmfdms"), "한글은")

    def test_already_hangul(self):
        """이미 한글인 입력은 그대로 유지"""
        self.assertEqual(convert_roman_to_hangul("한글"), "한글")
        self.assertEqual(convert_roman_to_hangul("가"), "가")

    def test_special_characters_and_numbers(self):
        """특수문자와 숫자가 섞인 입력"""
        self.assertEqual(convert_roman_to_hangul("gksrmf!"), "한글!")
        self.assertEqual(convert_roman_to_hangul("gksrmf123"), "한글123")
        self.assertEqual(convert_roman_to_hangul("gksrmf?"), "한글?")
        self.assertEqual(convert_roman_to_hangul("rk!@#"), "가!@#")

    def test_spaces(self):
        """공백이 포함된 입력"""
        self.assertEqual(convert_roman_to_hangul("rk tks"), "가 산")
        self.assertEqual(convert_roman_to_hangul("rk  tks"), "가  산")

    def test_single_character(self):
        """조합되지 않는 단일 입력"""
        self.assertEqual(convert_roman_to_hangul("r"), "ㄱ")
        self.assertEqual(convert_roman_to_hangul("k"), "ㅏ")

    def test_empty_string(self):
        """빈 문자열"""
        self.assertEqual(convert_roman_to_hangul(""), "")

    def test_long_text(self):
        """상대적으로 긴 입력"""
        result = convert_roman_to_hangul("dkssudgkqwkrhtk")
        self.assertTrue(len(result) > 0)

    def test_full_list(self):
        """decompose_hangul_full: 종성 포함 리스트"""
        self.assertEqual(decompose_hangul_full("가"), ['ㄱ','ㅏ'])
        self.assertEqual(decompose_hangul_full("각"), ['ㄱ','ㅏ','ㄱ'])
        self.assertEqual(decompose_hangul_full("한글"), ['ㅎ','ㅏ','ㄴ','ㄱ','ㅡ','ㄹ'])
        self.assertEqual(decompose_hangul_full("123"), ['1','2','3'])
        self.assertEqual(decompose_hangul_full(""), [])

    def test_str_version(self):
        """decompose_hangul_str: 문자열 반환"""
        self.assertEqual(decompose_hangul_str("가"), 'ㄱㅏ')
        self.assertEqual(decompose_hangul_str("각"), 'ㄱㅏㄱ')
        self.assertEqual(decompose_hangul_str("한글"), 'ㅎㅏㄴㄱㅡㄹ')
        self.assertEqual(decompose_hangul_str("123"), '123')
        self.assertEqual(decompose_hangul_str(""), '')

if __name__ == "__main__":
    unittest.main()