"""Validate the Collecting CSV schema and write an aggregated issue report."""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW_DEFAULT = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
OUT_DEFAULT = REPO / "5_process"
EXPECTED_COLUMNS = [
    "article_id", "title", "content", "publish_date", "source_name", "source_url",
    "topic_primary", "topic_secondary", "matched_keywords", "location", "sentiment",
    "relevance_status", "collection_date", "data_quality_note", "relevance_score",
    "word_count",
]
REQUIRED_COLUMNS = [
    "article_id", "title", "content", "publish_date", "source_name", "source_url",
    "topic_primary", "relevance_status",
]
SOURCES = {
    "VnEconomy", "Thanh Niên", "VietNamNet", "Tuổi Trẻ", "Sài Gòn Giải Phóng",
    "Nhân Dân", "Tiền Phong", "Dân Trí",
}
TOPIC_RE = re.compile(r"^([A-L]) - .+$")


def valid_url(value: str) -> bool:
    try:
        parsed = urlsplit(value.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.hostname and "." in parsed.hostname)
    except ValueError:
        return False


def validate_frame(frame: pd.DataFrame) -> tuple[dict, list[dict]]:
    issues: dict[str, dict] = {}

    def record(code: str, severity: str, article_id: str, description: str) -> None:
        issue = issues.setdefault(
            code,
            {"issue_code": code, "severity": severity, "count": 0, "examples_article_ids": [], "description": description},
        )
        issue["count"] += 1
        if article_id and len(issue["examples_article_ids"]) < 5 and article_id not in issue["examples_article_ids"]:
            issue["examples_article_ids"].append(article_id)

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    unexpected_columns = [column for column in frame.columns if column not in EXPECTED_COLUMNS]
    if missing_columns:
        record("SCHEMA_REQUIRED_COLUMN_MISSING", "Critical", "", f"Missing columns: {', '.join(missing_columns)}")
    if unexpected_columns:
        record("SCHEMA_UNEXPECTED_COLUMN", "Low", "", f"Unexpected columns: {', '.join(unexpected_columns)}")
    if list(frame.columns) != EXPECTED_COLUMNS:
        record(
            "SCHEMA_COLUMN_SET_OR_ORDER",
            "High",
            "",
            "Columns differ from the expected 16-column Collecting schema or are in a different order.",
        )

    usable = [column for column in REQUIRED_COLUMNS if column in frame.columns]
    for column in usable:
        blank = frame[column].fillna("").astype(str).str.strip().eq("")
        for index in frame.index[blank]:
            row = frame.loc[index]
            record(
                "REQUIRED_VALUE_BLANK",
                "High",
                str(row.get("article_id", "")),
                f"Required field is blank: {column}",
            )

    for column in ("article_id", "source_url"):
        if column in frame.columns:
            values = frame[column].fillna("").astype(str).str.strip()
            duplicated = values.ne("") & values.duplicated(keep=False)
            for index in frame.index[duplicated]:
                record(
                    f"DUPLICATE_{column.upper()}",
                    "High",
                    str(frame.loc[index].get("article_id", "")),
                    f"Duplicate value in {column}.",
                )

    if "publish_date" in frame.columns:
        dates = pd.to_datetime(frame["publish_date"], format="%Y-%m-%d", errors="coerce")
        for index in frame.index[dates.isna()]:
            record("PUBLISH_DATE_INVALID", "High", str(frame.loc[index].get("article_id", "")), "Date must be ISO YYYY-MM-DD.")
        outside = dates.notna() & ((dates < "2022-01-01") | (dates > "2026-10-23"))
        for index in frame.index[outside]:
            record("PUBLISH_DATE_OUT_OF_RANGE", "Medium", str(frame.loc[index].get("article_id", "")), "Date is outside project range.")

    if "source_name" in frame.columns:
        invalid = ~frame["source_name"].isin(SOURCES)
        for index in frame.index[invalid]:
            record("SOURCE_UNKNOWN", "High", str(frame.loc[index].get("article_id", "")), "Source is not in the approved eight-source list.")

    if "topic_primary" in frame.columns:
        codes = frame["topic_primary"].astype(str).str.extract(TOPIC_RE)[0]
        invalid = codes.isna()
        for index in frame.index[invalid]:
            record("TOPIC_PRIMARY_INVALID", "High", str(frame.loc[index].get("article_id", "")), "Primary topic must use a code A-L.")

    if "relevance_status" in frame.columns:
        invalid = ~frame["relevance_status"].eq("relevant_auto")
        for index in frame.index[invalid]:
            record("RELEVANCE_STATUS_INVALID", "Medium", str(frame.loc[index].get("article_id", "")), "Main dataset is expected to contain relevant_auto.")

    if "source_url" in frame.columns:
        invalid = ~frame["source_url"].map(valid_url)
        for index in frame.index[invalid]:
            record("SOURCE_URL_INVALID", "High", str(frame.loc[index].get("article_id", "")), "URL must be an absolute HTTP(S) URL.")

    for column, minimum in (("word_count", 0), ("relevance_score", 0)):
        if column in frame.columns:
            values = pd.to_numeric(frame[column], errors="coerce")
            invalid = values.isna() | (values < minimum)
            for index in frame.index[invalid]:
                record(f"{column.upper()}_INVALID", "Medium", str(frame.loc[index].get("article_id", "")), f"{column} must be numeric and non-negative.")

    if {"word_count", "content"} <= set(frame.columns):
        stored = pd.to_numeric(frame["word_count"], errors="coerce")
        recounted = frame["content"].fillna("").astype(str).map(lambda value: len(value.split()))
        mismatch = stored.ne(recounted)
        if mismatch.any():
            record(
                "WORD_COUNT_DIFFERS_FROM_CONTENT_SPLIT",
                "Info",
                "",
                f"{int(mismatch.sum())}/{len(frame)} rows differ; comparison only, original values are preserved.",
            )

    summary = {
        "rows": int(len(frame)),
        "columns": list(frame.columns),
        "expected_columns": EXPECTED_COLUMNS,
        "required_columns": REQUIRED_COLUMNS,
        "accepted_missing_values": {
            "topic_secondary": int(frame["topic_secondary"].fillna("").astype(str).str.strip().eq("").sum())
            if "topic_secondary" in frame else None,
            "sentiment": int(frame["sentiment"].fillna("").astype(str).str.strip().eq("").sum())
            if "sentiment" in frame else None,
        },
        "issue_counts": {code: entry["count"] for code, entry in issues.items()},
        "critical_or_high_issues": sum(entry["count"] for entry in issues.values() if entry["severity"] in {"Critical", "High"}),
        "status": "PASS" if not any(entry["severity"] in {"Critical", "High"} for entry in issues.values()) else "FAIL",
    }
    return summary, list(issues.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RAW_DEFAULT)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    frame = pd.read_csv(args.input, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    summary, issues = validate_frame(frame)
    logs = args.out / "logs"
    reports = args.out / "reports"
    logs.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    with (logs / "schema_validation_issues.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["issue_code", "severity", "count", "examples_article_ids", "description"])
        writer.writeheader()
        for issue in issues:
            writer.writerow({**issue, "examples_article_ids": "; ".join(issue["examples_article_ids"])})
    (reports / "01_schema_validation.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
