"""Validate that Process outputs agree with the unchanged source CSV."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from itertools import zip_longest
from pathlib import Path

import pandas as pd

from text_cleaning import clean_text

REPO = Path(__file__).resolve().parents[2]
RAW_DEFAULT = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
PROCESS_DEFAULT = REPO / "5_process"
_MISSING = object()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_ids(path: Path) -> tuple[list[str], set[str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "article_id" not in reader.fieldnames:
            raise ValueError(f"{path}: missing article_id column.")
        ids = [row["article_id"] for row in reader]
    if any(not article_id for article_id in ids):
        raise ValueError(f"{path}: blank article_id found.")
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate article_id found.")
    return ids, set(ids)


def validate_text_output(raw_path: Path, clean_path: Path) -> dict:
    checked_rows = 0
    with raw_path.open(encoding="utf-8-sig", newline="") as raw_stream, clean_path.open(
        encoding="utf-8-sig", newline=""
    ) as clean_stream:
        raw_reader = csv.DictReader(raw_stream)
        clean_reader = csv.DictReader(clean_stream)
        raw_columns = raw_reader.fieldnames or []
        clean_columns = clean_reader.fieldnames or []
        missing = set(raw_columns) - set(clean_columns)
        if missing:
            raise ValueError(
                f"{clean_path}: missing original columns: {sorted(missing)}"
            )
        if not {"title_clean", "content_clean"} <= set(clean_columns):
            raise ValueError(f"{clean_path}: cleaned text columns are missing.")

        for line_number, (source_row, output_row) in enumerate(
            zip_longest(raw_reader, clean_reader, fillvalue=_MISSING), start=2
        ):
            if source_row is _MISSING or output_row is _MISSING:
                raise ValueError(f"Raw/cleaned row counts differ at line {line_number}.")
            if any(source_row[column] != output_row[column] for column in raw_columns):
                raise ValueError(
                    f"{clean_path}: original source fields changed at line {line_number}."
                )
            if output_row["title_clean"] != clean_text(source_row["title"]):
                raise ValueError(f"Incorrect title_clean at line {line_number}.")
            if output_row["content_clean"] != clean_text(source_row["content"]):
                raise ValueError(f"Incorrect content_clean at line {line_number}.")
            checked_rows += 1
    return {"passed": True, "rows_checked": checked_rows, "original_fields_preserved": True}


def expected_split(publish_date: str) -> str:
    parsed = date.fromisoformat(publish_date)
    if parsed < date(2025, 1, 1):
        return "train"
    if parsed < date(2026, 1, 1):
        return "validation"
    return "test"


def validate_split(raw_path: Path, split_path: Path, process_dir: Path) -> dict:
    raw_splits = {}
    with raw_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            raw_splits[row["article_id"]] = expected_split(row["publish_date"])

    split_ids, split_id_set = read_csv_ids(split_path)
    counts = {"train": 0, "validation": 0, "test": 0}
    with split_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            expected = raw_splits.get(row["article_id"])
            if expected is None or row["split"] != expected:
                raise ValueError(
                    f"{split_path}: incorrect or unknown split for {row['article_id']}."
                )
            counts[row["split"]] += 1
    if split_id_set != set(raw_splits):
        raise ValueError(f"{split_path}: IDs do not match the raw dataset.")
    eligibility_path = process_dir / "splits" / "modeling_eligibility_manifest.csv"
    eligibility_ids, eligibility_id_set = read_csv_ids(eligibility_path)
    eligibility = pd.read_csv(eligibility_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    if eligibility_id_set != set(raw_splits):
        raise ValueError(f"{eligibility_path}: IDs do not match the raw dataset.")
    valid_assignments = {"train", "validation", "test", "review_hold"}
    if not set(eligibility["modeling_split"]) <= valid_assignments:
        raise ValueError(f"{eligibility_path}: contains invalid modeling_split values.")
    for row in eligibility.to_dict("records"):
        if row["split"] != raw_splits[row["article_id"]]:
            raise ValueError(f"{eligibility_path}: original split changed for {row['article_id']}.")
        is_held = row["modeling_split"] == "review_hold"
        if is_held != bool(row["hold_reason"]):
            raise ValueError(f"{eligibility_path}: hold reason/status mismatch for {row['article_id']}.")
    candidates_path = process_dir / "reports" / "near_duplicate_title_candidates.csv"
    candidates = pd.read_csv(candidates_path, dtype={"article_id_1": str, "article_id_2": str}, encoding="utf-8-sig")
    eligible_ids = set(
        eligibility.loc[eligibility["modeling_split"] != "review_hold", "article_id"]
    )
    cross_split = candidates[candidates["cross_split"].astype(bool)]
    for row in cross_split.to_dict("records"):
        if row["article_id_1"] in eligible_ids and row["article_id_2"] in eligible_ids:
            raise ValueError("Known cross-split title candidate remains eligible for modeling.")
    modeling_counts = eligibility.loc[
        eligibility["modeling_split"].isin(["train", "validation", "test"]),
        "modeling_split",
    ].value_counts().to_dict()
    return {
        "passed": True,
        "rows_checked": len(split_ids),
        "split_counts": counts,
        "modeling_eligibility_rows_checked": len(eligibility_ids),
        "modeling_review_hold_rows": int((eligibility["modeling_split"] == "review_hold").sum()),
        "modeling_eligible_split_counts": {
            key: int(modeling_counts.get(key, 0)) for key in ["train", "validation", "test"]
        },
        "known_cross_split_title_candidates_quarantined": True,
    }


def validate(raw_path: Path, process_dir: Path) -> dict:
    reports = process_dir / "reports"
    raw_hash_before = sha256_file(raw_path)
    profile = json.loads((reports / "00_input_profile.json").read_text(encoding="utf-8"))
    schema = json.loads((reports / "01_schema_validation.json").read_text(encoding="utf-8"))
    raw_ids, raw_id_set = read_csv_ids(raw_path)

    if raw_hash_before != profile["sha256"]:
        raise ValueError("Current raw SHA-256 does not match 00_input_profile.json.")
    if schema["status"] != "PASS" or schema["rows"] != len(raw_ids):
        raise ValueError("Schema validation did not pass for the current row count.")

    metadata_csv, metadata_csv_ids = read_csv_ids(
        process_dir / "data" / "interim" / "metadata_clean.csv"
    )
    metadata_parquet = pd.read_parquet(
        process_dir / "data" / "interim" / "metadata_clean.parquet",
        columns=["article_id"],
    )
    parquet_ids = metadata_parquet["article_id"].astype(str).tolist()
    if len(metadata_csv) != len(raw_ids) or metadata_csv_ids != raw_id_set:
        raise ValueError("metadata_clean.csv IDs/row count differ from raw.")
    if len(parquet_ids) != len(raw_ids) or len(set(parquet_ids)) != len(parquet_ids):
        raise ValueError("metadata_clean.parquet has missing or duplicate IDs.")
    if set(parquet_ids) != raw_id_set:
        raise ValueError("metadata_clean.parquet IDs differ from raw.")

    cleaned = validate_text_output(
        raw_path, process_dir / "data" / "processed" / "articles_text_clean.csv"
    )
    split = validate_split(raw_path, process_dir / "splits" / "split_manifest.csv", process_dir)
    raw_hash_after = sha256_file(raw_path)
    if raw_hash_before != raw_hash_after:
        raise ValueError("Raw SHA-256 changed during integration validation.")

    return {
        "status": "PASS",
        "raw_file": str(raw_path.relative_to(REPO)) if raw_path.is_relative_to(REPO) else raw_path.name,
        "raw_sha256": raw_hash_after,
        "raw_rows": len(raw_ids),
        "schema_status": schema["status"],
        "schema_issue_counts": schema["issue_counts"],
        "metadata_csv_rows": len(metadata_csv),
        "metadata_parquet_rows": len(parquet_ids),
        "clean_text": cleaned,
        "split": split,
        "raw_unchanged": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW_DEFAULT)
    parser.add_argument("--process-dir", type=Path, default=PROCESS_DEFAULT)
    args = parser.parse_args()

    result = validate(args.raw, args.process_dir)
    output = args.process_dir / "reports" / "integration_validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
