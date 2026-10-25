
import re
import unicodedata


def clean_text(text):
    """Clean Vietnamese news text while preserving its meaning."""
    if text is None:
        return ""

    text = str(text)

    # Normalize Unicode to NFC.
    text = unicodedata.normalize("NFC", text)

    # Remove unwanted control characters.
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Cc"
        or char in "\n\r\t"
    )

    # Replace tabs and line breaks with spaces.
    text = re.sub(r"[\t\r\n]+", " ", text)

    # Collapse extra whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_article(title, content):
    """Clean article title and content."""
    return {
        "title_clean": clean_text(title),
        "content_clean": clean_text(content),
    }


if __name__ == "__main__":
    samples = [
        "  Thị trường lao động Việt Nam  ",
        "Người lao động\t\tViệt Nam",
        "Chính phủ chưa công bố số liệu.",
    ]

    for sample in samples:
        print("Before:", repr(sample))
        print("After: ", repr(clean_text(sample)))
        print("-" * 40)

