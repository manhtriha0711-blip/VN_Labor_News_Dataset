import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from create_manual_label_sample import (
    AI_FIELDS,
    MANUAL_FIELDS,
    PRIORITY_ARTICLE_ID,
    SOURCE_FIELDS,
    TOPIC_QUOTAS,
    create_sample,
)
from keywords import TOPICS


def _source_row(article_id, topic):
    return {
        **{field: f"value-{field}" for field in SOURCE_FIELDS},
        "article_id": article_id,
        "topic_primary": topic,
    }


class TestCreateManualLabelSample(unittest.TestCase):
    def test_sample_is_reproducible_stratified_and_unlabeled(self):
        source_rows = []
        next_id = 1
        priority_topic = f"D - {TOPICS['D'][0]}"
        for topic, quota in TOPIC_QUOTAS.items():
            for _ in range(quota + 1):
                article_id = f"VNLAB-{next_id:06d}"
                if article_id == PRIORITY_ARTICLE_ID:
                    next_id += 1
                    article_id = f"VNLAB-{next_id:06d}"
                source_rows.append(_source_row(article_id, topic))
                next_id += 1
        source_rows.append(_source_row(PRIORITY_ARTICLE_ID, priority_topic))

        fields, sample = create_sample(source_rows)
        _, repeated_sample = create_sample(source_rows)

        self.assertEqual(sample, repeated_sample)
        self.assertEqual(len(sample), sum(TOPIC_QUOTAS.values()) + 1)
        self.assertTrue(set(MANUAL_FIELDS + AI_FIELDS).issubset(fields))
        self.assertEqual(
            sum(row["sample_reason"] == "topic_stratified" for row in sample),
            sum(TOPIC_QUOTAS.values()),
        )
        priority = next(row for row in sample if row["article_id"] == PRIORITY_ARTICLE_ID)
        self.assertEqual(priority["sample_reason"], "priority_issue:ISS-001")
        for row in sample:
            self.assertTrue(all(not row[field] for field in MANUAL_FIELDS))
            self.assertTrue(all(not row[field] for field in AI_FIELDS[:-1]))
            self.assertEqual(
                row["ai_review_status"],
                "No AI suggestion; awaiting human review",
            )


if __name__ == "__main__":
    unittest.main()
