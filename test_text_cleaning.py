
import sys
import unittest
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "5_process" / "src"))

from text_cleaning import clean_text


class TestTextCleaning(unittest.TestCase):

    def test_vietnamese_diacritics(self):
        text = "Người lao động tại Việt Nam"
        self.assertEqual(clean_text(text), text)

    def test_unicode_normalization(self):
        text = unicodedata.normalize("NFD", "Việt Nam")
        result = clean_text(text)
        self.assertEqual(result, "Việt Nam")
        self.assertEqual(
            unicodedata.normalize("NFC", result), result
        )

    def test_whitespace(self):
        self.assertEqual(
            clean_text("  Xin   chào\tViệt Nam \n "),
            "Xin chào Việt Nam"
        )

    def test_preserve_negation(self):
        text = "Người lao động không chưa được hỗ trợ"
        self.assertEqual(clean_text(text), text)

    def test_preserve_numbers_and_punctuation(self):
        text = "Hỗ trợ 30.000 tỷ đồng; ngày 31-12-2021."
        self.assertEqual(clean_text(text), text)

    def test_preserve_url(self):
        text = "Nguồn: https://example.com/tin-tuc?id=123"
        self.assertEqual(clean_text(text), text)

    def test_none_and_empty(self):
        self.assertEqual(clean_text(None), "")
        self.assertEqual(clean_text(""), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
