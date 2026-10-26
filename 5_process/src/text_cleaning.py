
import csv
import os
import re
import tempfile
import unicodedata
from pathlib import Path


def clean_text(text):
    """Normalize and clean Vietnamese news text."""
    if text is None:
        return ""

    text = unicodedata.normalize("NFC", str(text))
    text = text.translate(
        str.maketrans(
            {
                "\u200b": " ",
                "\ufeff": " ",
                "\u2060": " ",
            }
        )
    )

    cleaned = []
    for char in text:
        category = unicodedata.category(char)
        if category == "Cc":
            if char in "\n\r\t":
                cleaned.append(" ")
        elif category == "Cf" and char not in {"\u200c", "\u200d"}:
            continue
        else:
            cleaned.append(char)

    return re.sub(r"\s+", " ", "".join(cleaned)).strip()


def clean_csv(input_path, output_path):
    """Clean title and content columns, preserving other columns."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Input and output paths must be different.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)

        if not reader.fieldnames:
            raise ValueError("CSV has no header row.")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("CSV contains duplicate column names.")

        required = {"title", "content"}
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        fieldnames = list(reader.fieldnames)
        if "title_clean" not in fieldnames:
            fieldnames.append("title_clean")
        if "content_clean" not in fieldnames:
            fieldnames.append("content_clean")

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8-sig",
                newline="",
                dir=output_path.parent,
                delete=False,
            ) as target:
                temp_path = Path(target.name)
                writer = csv.DictWriter(
                    target, fieldnames=fieldnames, extrasaction="ignore"
                )
                writer.writeheader()

                for line_number, row in enumerate(reader, start=2):
                    if None in row:
                        raise ValueError(
                            f"CSV row {line_number} has more fields than the header."
                        )
                    if any(value is None for value in row.values()):
                        raise ValueError(
                            f"CSV row {line_number} has fewer fields than the header."
                        )
                    row["title_clean"] = clean_text(row.get("title", ""))
                    row["content_clean"] = clean_text(row.get("content", ""))
                    writer.writerow(row)

            os.replace(temp_path, output_path)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()


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
