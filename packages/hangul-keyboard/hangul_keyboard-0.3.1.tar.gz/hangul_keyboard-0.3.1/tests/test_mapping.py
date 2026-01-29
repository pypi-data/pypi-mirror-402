import unittest
from hangul_keyboard.mapping import (
    ROMAN_TO_JAMO,
    DOUBLE_JAMO_PAIR,
    CHOSUNGS,
    JOONGSUNGS,
    JONGSUNGS,
)


class TestMapping(unittest.TestCase):
    """Mapping 데이터 테스트"""

    # ROMAN_TO_JAMO
    def test_roman_to_jamo_keys(self):
        """ROMAN_TO_JAMO 핵심 키 존재"""
        self.assertIn('r', ROMAN_TO_JAMO)
        self.assertIn('R', ROMAN_TO_JAMO)
        self.assertIn('k', ROMAN_TO_JAMO)

    def test_roman_to_jamo_values_are_single_jamo(self):
        """ROMAN_TO_JAMO 값은 단일 자모"""
        for value in ROMAN_TO_JAMO.values():
            self.assertIsInstance(value, str)
            self.assertEqual(len(value), 1)

    def test_roman_to_jamo_sample_values(self):
        """ROMAN_TO_JAMO 대표 매핑"""
        self.assertEqual(ROMAN_TO_JAMO['r'], 'ㄱ')
        self.assertEqual(ROMAN_TO_JAMO['R'], 'ㄲ')
        self.assertEqual(ROMAN_TO_JAMO['k'], 'ㅏ')

    # DOUBLE_JAMO_PAIR
    def test_double_jamo_pair_keys_are_two_chars(self):
        """DOUBLE_JAMO_PAIR 키는 2글자"""
        for key in DOUBLE_JAMO_PAIR.keys():
            self.assertEqual(len(key), 2)

    def test_double_jamo_pair_values_are_single_jamo(self):
        """DOUBLE_JAMO_PAIR 값은 단일 자모"""
        for value in DOUBLE_JAMO_PAIR.values():
            self.assertEqual(len(value), 1)

    def test_double_jamo_pair_sample(self):
        """DOUBLE_JAMO_PAIR 대표 매핑"""
        self.assertEqual(DOUBLE_JAMO_PAIR['hk'], 'ㅘ')
        self.assertEqual(DOUBLE_JAMO_PAIR['rt'], 'ㄳ')

    # JAMO TABLES
    def test_jamo_tables_not_empty(self):
        """자모 테이블 비어있지 않음"""
        self.assertGreater(len(CHOSUNGS), 0)
        self.assertGreater(len(JOONGSUNGS), 0)
        self.assertGreater(len(JONGSUNGS), 0)

    def test_jamo_tables_unique(self):
        """자모 테이블 중복 없음"""
        self.assertEqual(len(CHOSUNGS), len(set(CHOSUNGS)))
        self.assertEqual(len(JOONGSUNGS), len(set(JOONGSUNGS)))
        self.assertEqual(len(JONGSUNGS), len(set(JONGSUNGS)))

    def test_jamo_table_lengths(self):
        """유니코드 기준 자모 개수"""
        self.assertEqual(len(CHOSUNGS), 19)
        self.assertEqual(len(JOONGSUNGS), 21)
        self.assertEqual(len(JONGSUNGS), 28)


if __name__ == '__main__':
    unittest.main()