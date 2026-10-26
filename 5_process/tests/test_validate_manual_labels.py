import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from validate_manual_labels import SOURCE_FIELDS, validate_records


def _source_row():
    return {field: f"value-{field}" for field in SOURCE_FIELDS} | {
        "article_id": "VNLAB-000001",
        "topic_primary": "A - Thị trường lao động Việt Nam",
        "relevance_status": "relevant_auto",
        "sample_reason": "topic_stratified",
    }


def _review_row():
    row = _source_row()
    row.update(
        relevance_manual="Relevant",
        topic_manual="A - Thị trường lao động Việt Nam",
        review_reason="Nội dung trực tiếp nói về nhu cầu nhân lực.",
        reviewer_id="reviewer-01",
        review_date="2026-10-26",
    )
    return row


class TestValidateManualLabels(unittest.TestCase):
    def test_pending_review_is_reported_without_fabricating_labels(self):
        row = _source_row()
        row.update(
            relevance_manual="",
            topic_manual="",
            review_reason="",
            reviewer_id="",
            review_date="",
        )

        errors, pending, counts = validate_records([row], [_source_row()])

        self.assertEqual(errors, [])
        self.assertEqual(pending, 1)
        self.assertEqual(counts, {})

    def test_accepts_complete_manual_review(self):
        errors, pending, counts = validate_records(
            [_review_row()], [_source_row()]
        )

        self.assertEqual(errors, [])
        self.assertEqual(pending, 0)
        self.assertEqual(counts, {"Relevant": 1})

    def test_rejects_topic_outside_project_taxonomy(self):
        row = _review_row()
        row["topic_manual"] = "Topic invented"

        errors, pending, _ = validate_records([row], [_source_row()])

        self.assertTrue(any("valid A-L topic is required" in e for e in errors))
        self.assertEqual(pending, 0)

    def test_rejects_modified_source_and_invalid_date(self):
        row = _review_row()
        row["title"] = "changed title"
        row["review_date"] = "yesterday"

        errors, _, _ = validate_records([row], [_source_row()])

        self.assertTrue(any("source field changed: title" in e for e in errors))
        self.assertTrue(any("review_date must use YYYY-MM-DD" in e for e in errors))

    def test_allows_registered_priority_issue_record_while_pending(self):
        row = _source_row()
        row.update(
            article_id="VNLAB-000002",
            relevance_status="relevant_auto",
            sample_reason="priority_issue:ISS-001",
            relevance_manual="",
            topic_manual="",
            review_reason="",
            reviewer_id="",
            review_date="",
        )
        source = _source_row()
        source.update(article_id="VNLAB-000002", relevance_status="relevant_auto")

        errors, pending, counts = validate_records([row], [source])

        self.assertEqual(errors, [])
        self.assertEqual(pending, 1)
        self.assertEqual(counts, {})


if __name__ == "__main__":
    unittest.main()
