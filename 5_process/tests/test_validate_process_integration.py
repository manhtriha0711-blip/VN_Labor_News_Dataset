import csv
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from validate_process_integration import expected_split, validate_text_output
from text_cleaning import clean_text


class TestProcessIntegrationValidation(unittest.TestCase):
    def test_temporal_split_boundaries(self):
        self.assertEqual(expected_split("2024-12-31"), "train")
        self.assertEqual(expected_split("2025-01-01"), "validation")
        self.assertEqual(expected_split("2025-12-31"), "validation")
        self.assertEqual(expected_split("2026-01-01"), "test")

    def test_text_output_checks_preserved_fields_and_clean_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_path = Path(temp_dir) / "raw.csv"
            clean_path = Path(temp_dir) / "clean.csv"
            source_row = {
                "article_id": "VNLAB-000001",
                "title": "  Người\u200blao động  ",
                "content": "Nội dung không bị sửa. " * 100,
                "source_url": "https://example.com/a",
            }
            with raw_path.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(source_row))
                writer.writeheader()
                writer.writerow(source_row)
            with clean_path.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(
                    stream, fieldnames=[*source_row, "title_clean", "content_clean"]
                )
                writer.writeheader()
                writer.writerow(
                    {
                        **source_row,
                        "title_clean": clean_text(source_row["title"]),
                        "content_clean": clean_text(source_row["content"]),
                    }
                )

            result = validate_text_output(raw_path, clean_path)

        self.assertTrue(result["passed"])
        self.assertEqual(result["rows_checked"], 1)
        self.assertTrue(result["original_fields_preserved"])

    def test_text_output_rejects_modified_raw_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_path = Path(temp_dir) / "raw.csv"
            clean_path = Path(temp_dir) / "clean.csv"
            columns = ["article_id", "title", "content"]
            with raw_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=columns)
                writer.writeheader()
                writer.writerow(
                    {"article_id": "VNLAB-000001", "title": "Title", "content": "Body"}
                )
            with clean_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream, fieldnames=[*columns, "title_clean", "content_clean"]
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "article_id": "VNLAB-000001",
                        "title": "Changed title",
                        "content": "Body",
                        "title_clean": "Changed title",
                        "content_clean": "Body",
                    }
                )

            with self.assertRaisesRegex(ValueError, "original source fields changed"):
                validate_text_output(raw_path, clean_path)


if __name__ == "__main__":
    unittest.main()
