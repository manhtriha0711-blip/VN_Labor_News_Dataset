
import csv
import re
import unicodedata
from pathlib import Path


def clean_text(text):
    """Normalize and clean Vietnamese news text."""
    if text is None:
        return ""

    text = unicodedata.normalize("NFC", str(text))

    # Preserve tabs and line breaks temporarily, then normalize spaces.
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Cc"
        or char in "\n\r\t"
    )

    text = re.sub(r"[\t\r\n]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_csv(input_path, output_path):
    """Clean title and content columns, preserving other columns."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)

        if not reader.fieldnames:
            raise ValueError("CSV has no header row.")

        required = {"title", "content"}
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        fieldnames = list(reader.fieldnames)
        if "title_clean" not in fieldnames:
            fieldnames.append("title_clean")
        if "content_clean" not in fieldnames:
            fieldnames.append("content_clean")

        with output_path.open(
            "w", encoding="utf-8-sig", newline=""
        ) as target:
            writer = csv.DictWriter(
                target, fieldnames=fieldnames, extrasaction="ignore"
            )
            writer.writeheader()

            for row in reader:
                row["title_clean"] = clean_text(row.get("title", ""))
                row["content_clean"] = clean_text(row.get("content", ""))
                writer.writerow(row)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]

    input_csv = (
        project_root / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
    )
    output_csv = (
        project_root / "5_process" / "data" / "processed"
        / "articles_text_clean.csv"
    )

    clean_csv(input_csv, output_csv)
    print(f"Cleaned CSV saved to: {output_csv}")

