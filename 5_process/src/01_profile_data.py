"""Create a reproducible, content-free profile of the Collecting CSV."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW_DEFAULT = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
OUT_DEFAULT = REPO / "5_process" / "reports"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_profile(path: Path) -> dict:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    profile = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "input_file": str(path.relative_to(REPO)) if path.is_relative_to(REPO) else path.name,
        "sha256": sha256_file(path),
        "rows": int(len(frame)),
        "columns_count": int(len(frame.columns)),
        "columns": list(frame.columns),
        "blank_counts": {
            column: int(frame[column].str.strip().eq("").sum()) for column in frame.columns
        },
        "unique_counts": {
            column: int(frame[column].nunique(dropna=False))
            for column in ("article_id", "source_url")
            if column in frame.columns
        },
    }
    if "publish_date" in frame.columns:
        dates = pd.to_datetime(frame["publish_date"], format="%Y-%m-%d", errors="coerce")
        valid_dates = dates.dropna()
        profile["publish_date"] = {
            "valid": int(dates.notna().sum()),
            "invalid": int(dates.isna().sum()),
            "min": valid_dates.min().date().isoformat() if not valid_dates.empty else None,
            "max": valid_dates.max().date().isoformat() if not valid_dates.empty else None,
        }
        profile["publish_year_counts"] = {
            str(year): int(count)
            for year, count in dates.dt.year.value_counts().sort_index().items()
            if pd.notna(year)
        }
    for column in ("source_name", "topic_primary", "relevance_status"):
        if column in frame.columns:
            profile[f"{column}_counts"] = {
                str(value): int(count)
                for value, count in frame[column].value_counts(dropna=False).sort_index().items()
            }
    profile["content_characters"] = (
        {
            "min": int(frame["content"].str.len().min()),
            "median": float(frame["content"].str.len().median()),
            "max": int(frame["content"].str.len().max()),
        }
        if "content" in frame.columns and not frame.empty
        else None
    )
    if {"word_count", "content"} <= set(frame.columns):
        stored = pd.to_numeric(frame["word_count"], errors="coerce")
        recounted = frame["content"].map(lambda value: len(value.split()))
        profile["word_count_comparison"] = {
            "mismatches_vs_content_split": int(stored.ne(recounted).sum()),
            "rows": int(len(frame)),
            "note": "Comparison only; does not overwrite the Collecting word_count field.",
        }
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RAW_DEFAULT)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()

    profile = build_profile(args.input)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "00_input_profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    date_profile = profile.get("publish_date", {})
    lines = [
        "# Hồ sơ đầu vào Collecting",
        "",
        f"- File chuẩn: `{profile['input_file']}`",
        f"- Số dòng/cột: {profile['rows']:,} / {profile['columns_count']}",
        f"- SHA-256: `{profile['sha256']}`",
        f"- Python / pandas: {profile['python_version']} / {profile['pandas_version']}",
        f"- Ngày xuất bản: {date_profile.get('min')} → {date_profile.get('max')} "
        f"({date_profile.get('invalid')} ngày không hợp lệ)",
        f"- ID duy nhất: {profile.get('unique_counts', {}).get('article_id')}",
        f"- URL duy nhất: {profile.get('unique_counts', {}).get('source_url')}",
        f"- `sentiment` trống: {profile.get('blank_counts', {}).get('sentiment')}",
        f"- `topic_secondary` trống: {profile.get('blank_counts', {}).get('topic_secondary')}",
    ]
    comparison = profile.get("word_count_comparison")
    if comparison:
        lines.extend([
            "",
            "## Đối chiếu `word_count`",
            "",
            f"`word_count` khác `content.split()` ở {comparison['mismatches_vs_content_split']:,}/"
            f"{comparison['rows']:,} dòng. Đây chỉ là đối chiếu; không sửa giá trị gốc.",
        ])
    lines.extend(["", "## Schema", ""])
    lines.extend(f"- `{column}` — {profile['blank_counts'][column]:,} ô trống" for column in profile["columns"])
    (args.out / "00_input_profile.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"Profiled {profile['rows']} rows x {profile['columns_count']} columns; "
        f"sha256={profile['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
