import csv
import sys
import tempfile
import unittest
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "5_process" / "src"))

from text_cleaning import clean_csv, clean_text


class TestTextCleaning(unittest.TestCase):

    def test_vietnamese_diacritics(self):
        text = "Người lao động tại Việt Nam"
        self.assertEqual(clean_text(text), text)

    def test_unicode_normalization(self):
        text = unicodedata.normalize("NFD", "Việt Nam")
        self.assertEqual(clean_text(text), "Việt Nam")

    def test_whitespace(self):
        self.assertEqual(
            clean_text("  Xin   chào\tViệt Nam \n "),
            "Xin chào Việt Nam"
        )

    def test_removes_invisible_format_artifacts(self):
        text = "Người\u200blao\u00ad động\u200e Việt\ufeffNam\u2060"
        self.assertEqual(clean_text(text), "Người lao động Việt Nam")

    def test_preserves_joiners_and_removes_control_characters(self):
        text = "A\x00B 👩\u200d💼 क्\u200cष"
        self.assertEqual(clean_text(text), "AB 👩\u200d💼 क्\u200cष")

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


class TestCleanCsv(unittest.TestCase):

    def test_preserves_source_fields_and_cleans_long_content(self):
        rows = [
            {
                "article_id": "VNLAB-000001",
                "title": "  Người\u200blao động không tăng lương  ",
                "content": "Nội dung dài. " * 5000,
                "source_url": "https://example.com/a?id=1",
            },
            {
                "article_id": "VNLAB-000002",
                "title": "Tiêu đề thứ hai",
                "content": "Nội dung thứ hai",
                "source_url": "https://example.com/b",
            },
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.csv"
            output_path = Path(temp_dir) / "nested" / "output.csv"
            with input_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)

            clean_csv(input_path, output_path)

            with output_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                result = list(csv.DictReader(file))

        self.assertEqual(len(result), len(rows))
        for original, cleaned in zip(rows, result):
            for field, value in original.items():
                self.assertEqual(cleaned[field], value)
        self.assertEqual(
            result[0]["title_clean"], "Người lao động không tăng lương"
        )
        self.assertEqual(
            result[0]["content_clean"], clean_text(rows[0]["content"])
        )
        self.assertEqual(result[1]["title_clean"], rows[1]["title"])

    def test_rejects_malformed_csv_without_replacing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.csv"
            output_path = Path(temp_dir) / "output.csv"
            input_path.write_text("title,content\nOnly one field\n", encoding="utf-8")
            output_path.write_text("previous output", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "fewer fields"):
                clean_csv(input_path, output_path)

            self.assertEqual(
                output_path.read_text(encoding="utf-8"), "previous output"
            )

    def test_rejects_same_input_and_output_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.csv"
            input_path.write_text("title,content\nTitle,Content\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must be different"):
                clean_csv(input_path, input_path)

            self.assertEqual(
                input_path.read_text(encoding="utf-8"),
                "title,content\nTitle,Content\n",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
