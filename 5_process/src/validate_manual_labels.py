"""Validate the human-reviewed label sample without modifying any files."""

import argparse
import csv
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "4_ma_nguon"))
from keywords import TOPICS

MANUAL_FIELDS = (
    "relevance_manual",
    "topic_manual",
    "review_reason",
    "reviewer_id",
    "review_date",
)
RELEVANCE_LABELS = {"Relevant", "Borderline", "Not relevant", "Uncertain"}
TOPIC_LABELS = {f"{code} - {name}" for code, (name, _terms) in TOPICS.items()}
PRIORITY_SAMPLE_ISSUES = {"VNLAB-000002": "ISS-001"}
TOPIC_SAMPLE_QUOTAS = {
    f"{code} - {name}": 2 if code == "I" else 4 if code == "L" else 5
    for code, (name, _terms) in TOPICS.items()
}
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


def _read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError(f"{path}: CSV has no header row.")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"{path}: CSV has duplicate column names.")

        rows = []
        for line_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path}: malformed CSV row {line_number}.")
            rows.append(row)
        return reader.fieldnames, rows


def _normalize_newlines(value):
    return value.replace("\r\n", "\n").replace("\r", "\n")


def validate_records(sample_rows, source_rows):
    errors = []
    pending = 0
    label_counts = Counter()

    source_by_id = {}
    for row in source_rows:
        article_id = row["article_id"]
        if article_id in source_by_id:
            errors.append(f"Duplicate article_id in source: {article_id}")
        source_by_id[article_id] = row

    seen_ids = set()
    for row in sample_rows:
        article_id = row["article_id"].strip()
        if not article_id:
            errors.append("Sample row has an empty article_id.")
            continue
        if article_id in seen_ids:
            errors.append(f"Duplicate article_id in sample: {article_id}")
        seen_ids.add(article_id)

        original = source_by_id.get(article_id)
        if original is None:
            errors.append(f"{article_id}: not found in the authoritative source.")
        else:
            for field in SOURCE_FIELDS:
                if _normalize_newlines(row[field]) != _normalize_newlines(
                    original[field]
                ):
                    errors.append(f"{article_id}: source field changed: {field}")
        sample_reason = row.get("sample_reason", "").strip()
        if sample_reason == "topic_stratified":
            pass
        elif sample_reason.startswith("priority_issue:"):
            expected_issue = PRIORITY_SAMPLE_ISSUES.get(article_id)
            if expected_issue is None or sample_reason != f"priority_issue:{expected_issue}":
                errors.append(
                    f"{article_id}: priority sample reason is not backed by a registered issue."
                )
        else:
            errors.append(f"{article_id}: invalid or missing sample_reason.")

        values = {field: row[field].strip() for field in MANUAL_FIELDS}
        populated = [bool(value) for value in values.values()]
        if not any(populated):
            pending += 1
            continue
        if not all(populated):
            missing = [
                field for field, value in values.items() if not value
            ]
            errors.append(
                f"{article_id}: incomplete manual review fields: "
                + ", ".join(missing)
            )
            continue

        relevance = values["relevance_manual"]
        topic = values["topic_manual"]
        if relevance not in RELEVANCE_LABELS:
            errors.append(
                f"{article_id}: invalid relevance_manual: {relevance}"
            )
        elif relevance in {"Relevant", "Borderline"} and topic not in TOPIC_LABELS:
            errors.append(f"{article_id}: valid A-L topic is required.")
        elif relevance in {"Not relevant", "Uncertain"} and topic:
            errors.append(
                f"{article_id}: topic_manual must be blank for {relevance}."
            )

        try:
            parsed_date = datetime.strptime(values["review_date"], "%Y-%m-%d")
            if parsed_date.strftime("%Y-%m-%d") != values["review_date"]:
                raise ValueError
        except ValueError:
            errors.append(
                f"{article_id}: review_date must use YYYY-MM-DD."
            )

        label_counts[relevance] += 1

    return errors, pending, label_counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sample",
        nargs="?",
        type=Path,
        default=PROJECT_ROOT
        / "5_process"
        / "data"
        / "processed"
        / "manual_label_sample.csv",
        help="CSV to validate (defaults to the project review sample).",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Return failure while any rows are still awaiting human review.",
    )
    args = parser.parse_args()

    source_path = PROJECT_ROOT / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
    sample_fields, sample_rows = _read_csv(args.sample)
    source_fields, source_rows = _read_csv(source_path)

    required_fields = set(SOURCE_FIELDS) | set(MANUAL_FIELDS)
    required_fields.add("sample_reason")
    missing_sample_fields = required_fields - set(sample_fields)
    missing_source_fields = set(SOURCE_FIELDS) - set(source_fields)
    if missing_sample_fields:
        raise ValueError(
            "Sample is missing columns: " + ", ".join(sorted(missing_sample_fields))
        )
    if missing_source_fields:
        raise ValueError(
            "Source is missing columns: " + ", ".join(sorted(missing_source_fields))
        )
    source_by_id = {row["article_id"]: row for row in source_rows}
    topic_sample_counts = Counter(
        source_by_id[row["article_id"].strip()]["topic_primary"]
        for row in sample_rows
        if row["sample_reason"].strip() == "topic_stratified"
        and row["article_id"].strip() in source_by_id
    )
    for topic, expected_count in TOPIC_SAMPLE_QUOTAS.items():
        if topic_sample_counts[topic] != expected_count:
            raise ValueError(
                f"Topic-stratified sample count for {topic} must be "
                f"{expected_count}, found {topic_sample_counts[topic]}."
            )
    expected_sample_size = sum(TOPIC_SAMPLE_QUOTAS.values()) + len(
        PRIORITY_SAMPLE_ISSUES
    )
    if len(sample_rows) != expected_sample_size:
        raise ValueError(
            f"Sample must contain {expected_sample_size} rows, found {len(sample_rows)}."
        )
    for article_id, issue_id in PRIORITY_SAMPLE_ISSUES.items():
        matching_priority = [
            row
            for row in sample_rows
            if row["article_id"].strip() == article_id
            and row["sample_reason"].strip() == f"priority_issue:{issue_id}"
        ]
        if len(matching_priority) != 1:
            raise ValueError(
                f"Expected exactly one registered priority row for {article_id}."
            )

    errors, pending, label_counts = validate_records(
        sample_rows, source_rows
    )
    for error in errors:
        print(f"ERROR: {error}")
    print(
        f"Rows: {len(sample_rows)}; manually reviewed: "
        f"{len(sample_rows) - pending}; pending: {pending}"
    )
    if label_counts:
        print("Manual relevance labels:", dict(sorted(label_counts.items())))

    if errors or (args.require_complete and pending):
        return 1
    if pending:
        print("Review status: pending human review; no labels were fabricated.")
    else:
        print("Review status: complete and valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
