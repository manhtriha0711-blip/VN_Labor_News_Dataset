"""Create a reproducible human-review sample from the authoritative dataset."""

import csv
import hashlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "4_ma_nguon"))
from keywords import TOPICS

SOURCE_FIELDS = (
    "article_id",
    "title",
    "content",
    "publish_date",
    "source_name",
    "source_url",
    "topic_primary",
    "topic_secondary",
    "matched_keywords",
    "location",
    "sentiment",
    "relevance_status",
    "collection_date",
    "data_quality_note",
    "relevance_score",
    "word_count",
)
MANUAL_FIELDS = (
    "relevance_manual",
    "topic_manual",
    "review_reason",
    "reviewer_id",
    "review_date",
)
AI_FIELDS = (
    "ai_suggested_relevance",
    "ai_suggested_topic",
    "ai_suggested_reason",
    "ai_review_status",
)
TOPIC_QUOTAS = {
    f"{code} - {name}": 2 if code == "I" else 4 if code == "L" else 5
    for code, (name, _terms) in TOPICS.items()
}
PRIORITY_ARTICLE_ID = "VNLAB-000002"
OUTPUT_PATH = (
    PROJECT_ROOT / "5_process" / "data" / "processed" / "manual_label_sample.csv"
)


def _sample_rank(row):
    return hashlib.sha256(row["article_id"].encode("utf-8")).hexdigest()


def create_sample(source_rows):
    source_by_id = {}
    for row in source_rows:
        article_id = row["article_id"]
        if article_id in source_by_id:
            raise ValueError(f"Duplicate source article_id: {article_id}")
        source_by_id[article_id] = row

    if PRIORITY_ARTICLE_ID not in source_by_id:
        raise ValueError(f"Priority article is absent from source: {PRIORITY_ARTICLE_ID}")

    selected = []
    for topic, quota in TOPIC_QUOTAS.items():
        candidates = [
            row
            for row in source_rows
            if row["topic_primary"] == topic
            and row["article_id"] != PRIORITY_ARTICLE_ID
        ]
        if len(candidates) < quota:
            raise ValueError(
                f"Not enough source rows for {topic}: need {quota}, found {len(candidates)}."
            )
        selected.extend(
            (row, "topic_stratified")
            for row in sorted(candidates, key=_sample_rank)[:quota]
        )

    selected.append((source_by_id[PRIORITY_ARTICLE_ID], "priority_issue:ISS-001"))
    fields = (
        *SOURCE_FIELDS,
        "sample_reason",
        *MANUAL_FIELDS,
        *AI_FIELDS,
    )
    rows = []
    for source_row, reason in selected:
        row = {field: source_row[field] for field in SOURCE_FIELDS}
        row["sample_reason"] = reason
        row.update({field: "" for field in MANUAL_FIELDS})
        row.update({field: "" for field in AI_FIELDS})
        row["ai_review_status"] = "No AI suggestion; awaiting human review"
        rows.append(row)
    return fields, rows


def main():
    source_path = PROJECT_ROOT / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
    with source_path.open(encoding="utf-8-sig", newline="") as file:
        source_rows = list(csv.DictReader(file))

    fields, sample_rows = create_sample(source_rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sample_rows)
    print(
        f"Created {len(sample_rows)} review rows "
        f"({len(sample_rows) - 1} topic-stratified + 1 priority issue) "
        f"at {OUTPUT_PATH.relative_to(PROJECT_ROOT)}."
    )


if __name__ == "__main__":
    main()
