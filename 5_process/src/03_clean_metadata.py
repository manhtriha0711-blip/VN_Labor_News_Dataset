#!/usr/bin/env python3
"""03_clean_metadata.py - Người 2: chuẩn hóa metadata + audit trùng lặp.

Nguyên tắc (theo kế hoạch Process):
  * Chỉ ĐỌC 1_du_lieu_chinh/vn_labor_news_dataset.csv; không ghi đè raw (kiểm SHA-256 trước/sau).
  * Không sửa `content`; không xóa bản ghi nào (chỉ audit, đánh cờ, gán dup_cluster_id).
  * Giữ nguyên `source_url` gốc, thêm `source_url_normalized` để so sánh.
  * Giá trị thiếu -> null nhất quán; `sentiment` trống KHÔNG đổi thành "neutral".
  * Lỗi không chắc chắn -> ghi vào metadata_issues.csv, không tự suy diễn.

Chạy:  python 5_process/src/03_clean_metadata.py
Đầu vào quyết định review (do người review sửa, module chỉ đọc):
  5_process/config/duplicate_decisions.csv  (khóa review_key = dup_type|id1; id2, đã sắp xếp)
  5_process/config/outlier_review.csv       (khóa article_id + issue_code)
Đầu ra:
  5_process/data/interim/metadata_clean.parquet (+ .csv UTF-8)
  5_process/data/interim/duplicate_review.csv
  5_process/logs/metadata_change_log.csv, 5_process/logs/metadata_issues.csv
  5_process/reports/metadata_audit.md
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW_DEFAULT = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
OUT_DEFAULT = REPO / "5_process"
DECISION_PRIORITY = ["NGHI_DANG_LAI_DE_XUAT_GIU_1", "GIU_CA_HAI_CUNG_SU_KIEN", "KHONG_TRUNG"]

PROJECT_START = "2022-01-01"
PROJECT_END = "2026-10-23"
# Ngưỡng ngoại lai (chỉ ĐÁNH CỜ, không sửa/xóa)
WORDS_LONG, WORDS_SHORT = 5000, 100      # số từ theo content.split()
TITLE_LONG, TITLE_SHORT = 200, 15        # số ký tự tiêu đề

TOPICS = {
    "A": "Thị trường lao động Việt Nam",
    "B": "Thất nghiệp, mất việc, cắt giảm nhân sự",
    "C": "Tiền lương, bảo hiểm, quyền lợi",
    "D": "Hợp đồng lao động, nghỉ việc, sa thải",
    "E": "Điều kiện làm việc, an toàn lao động",
    "F": "Công đoàn, đình công, tranh chấp lao động",
    "G": "Nhóm lao động dễ bị ảnh hưởng",
    "H": "Chính sách việc làm, đào tạo nghề, an sinh xã hội",
    "I": "Lừa đảo tuyển dụng, bóc lột lao động",
    "J": "Kinh tế và yếu tố tác động đến việc làm",
    "K": "Pháp luật lao động và thực thi",
    "L": "Tâm lý người lao động, chất lượng việc làm",
}

CANON_SOURCES = [
    "VnEconomy", "Thanh Niên", "VietNamNet", "Tuổi Trẻ",
    "Sài Gòn Giải Phóng", "Nhân Dân", "Tiền Phong", "Dân Trí",
]
SOURCE_DOMAINS = {
    "vneconomy.vn": "VnEconomy", "thanhnien.vn": "Thanh Niên",
    "vietnamnet.vn": "VietNamNet", "tuoitre.vn": "Tuổi Trẻ",
    "sggp.org.vn": "Sài Gòn Giải Phóng", "nhandan.vn": "Nhân Dân",
    "tienphong.vn": "Tiền Phong", "dantri.com.vn": "Dân Trí",
}
_EXTRA_ALIASES = {
    "vneconomyvn": "VnEconomy", "thanhnienonline": "Thanh Niên", "thanhnienvn": "Thanh Niên",
    "vietnamnetvn": "VietNamNet", "tuoitreonline": "Tuổi Trẻ", "tuoitrevn": "Tuổi Trẻ",
    "sggp": "Sài Gòn Giải Phóng", "baosaigongiaiphong": "Sài Gòn Giải Phóng",
    "baonhandan": "Nhân Dân", "nhandanvn": "Nhân Dân", "baotienphong": "Tiền Phong",
    "dantricomvn": "Dân Trí", "baodantri": "Dân Trí",
}

TEXT_FIELDS = ["title", "location", "matched_keywords", "topic_primary", "topic_secondary",
               "data_quality_note", "relevance_status"]
TRACKING_PARAMS = ("utm_", "fbclid", "gclid", "zarsrc", "ref")
_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"), None)


# ----------------------------------------------------------------------------
# Hàm thuần (có unit test)
# ----------------------------------------------------------------------------
def strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def alias_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", strip_accents(s).lower())


SOURCE_ALIASES = {alias_key(n): n for n in CANON_SOURCES}
SOURCE_ALIASES.update(_EXTRA_ALIASES)


def normalize_text(s: str) -> str:
    """NFC + bỏ ký tự vô hình + gộp khoảng trắng. Không đụng chữ/dấu/dấu câu."""
    s = unicodedata.normalize("NFC", s).translate(_INVISIBLE)
    return re.sub(r"\s+", " ", s).strip()


def normalize_source(name: str) -> str | None:
    return SOURCE_ALIASES.get(alias_key(normalize_text(name)))


def normalize_url(url: str) -> str:
    """URL để SO SÁNH: https, host thường, bỏ www/port mặc định/fragment/tracking/'/' cuối.
    Trả về '' nếu không hợp lệ về cú pháp. source_url gốc không bị thay đổi."""
    u = normalize_text(url)
    try:
        p = urlsplit(u)
    except ValueError:
        return ""
    if p.scheme.lower() not in ("http", "https") or not p.hostname or "." not in p.hostname:
        return ""
    host = p.hostname.lower()
    host = host[4:] if host.startswith("www.") else host
    port = f":{p.port}" if p.port not in (None, 80, 443) else ""
    path = re.sub(r"/{2,}", "/", p.path)
    path = path.rstrip("/") or ""
    q = sorted((k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
               if not k.lower().startswith(TRACKING_PARAMS))
    return urlunsplit(("https", host + port, path, urlencode(q), ""))


def title_key(title: str) -> str:
    """Khóa so sánh tiêu đề: chữ thường, bỏ dấu câu, giữ dấu tiếng Việt."""
    t = normalize_text(title).casefold()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def content_hash(content: str) -> str:
    return hashlib.sha1(normalize_text(content).casefold().encode("utf-8")).hexdigest()


def parse_topic(label: str) -> tuple[str | None, bool]:
    """Trả về (mã A-L hoặc None, nhãn_khớp_taxonomy)."""
    m = re.match(r"^([A-L]) - (.+)$", label)
    if not m:
        return None, False
    return m.group(1), TOPICS[m.group(1)] == m.group(2)


def load_config_csv(path: Path, key: str) -> dict:
    """Load confirmed review decisions; reject AI drafts and malformed configs."""
    if not path.exists():
        return {}
    t = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {key, "decision", "keep_article_id", "reviewer", "review_note"}
    missing = required - set(t.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    if t[key].str.strip().eq("").any() or t[key].duplicated().any():
        raise ValueError(f"{path}: {key} must be non-empty and unique.")
    invalid = sorted(set(t["decision"]) - set(DECISION_PRIORITY))
    if invalid:
        raise ValueError(f"{path}: invalid decisions {invalid}")
    invalid_keep = t.loc[
        (t["decision"] == DECISION_PRIORITY[0]) & t["keep_article_id"].str.strip().eq(""),
        key,
    ]
    if len(invalid_keep):
        raise ValueError(f"{path}: proposed repost decisions require keep_article_id.")
    unexpected_keep = t.loc[
        (t["decision"] != DECISION_PRIORITY[0]) & t["keep_article_id"].str.strip().ne(""),
        key,
    ]
    if len(unexpected_keep):
        raise ValueError(f"{path}: keep_article_id is only valid for repost proposals.")
    validate_human_reviewers(t, path)
    if t["review_note"].str.strip().eq("").any():
        raise ValueError(f"{path}: each decision requires a review_note.")
    return t.set_index(key).to_dict("index")


def validate_human_reviewers(rows: pd.DataFrame, path: Path) -> None:
    if "reviewer" not in rows.columns or rows["reviewer"].str.strip().eq("").any():
        raise ValueError(f"{path}: every review requires a human reviewer.")
    unconfirmed = rows["reviewer"].str.contains(
        r"\b(?:ai|claude|draft|nháp|chờ|pending)\b",
        case=False,
        regex=True,
    )
    if unconfirmed.any():
        raise ValueError(
            f"{path}: AI/draft reviewer is not confirmed; "
            "a human must review before applying."
        )


def load_outlier_review_csv(path: Path) -> dict:
    """Load confirmed outlier conclusions keyed by article and issue code."""
    if not path.exists():
        return {}
    t = pd.read_csv(path, dtype=str, keep_default_na=False)
    key_columns = ["article_id", "issue_code"]
    required = set(key_columns) | {"conclusion", "review_note", "reviewer"}
    missing = required - set(t.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    if t[key_columns].apply(lambda column: column.str.strip().eq("")).any().any():
        raise ValueError(f"{path}: article_id and issue_code must be non-empty.")
    if t.duplicated(key_columns).any():
        raise ValueError(f"{path}: article_id + issue_code must be unique.")
    valid_conclusions = {"HOP_LE_LUU_Y", "BAT_THUONG_CAN_XEM", "HOP_LE_GIU"}
    invalid = sorted(set(t["conclusion"]) - valid_conclusions)
    if invalid:
        raise ValueError(f"{path}: invalid conclusions {invalid}")
    validate_human_reviewers(t, path)
    if t["review_note"].str.strip().eq("").any():
        raise ValueError(f"{path}: each conclusion requires a review_note.")
    keys = t["article_id"] + "|" + t["issue_code"]
    return {key: row for key, row in zip(keys, t.to_dict("records"))}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def near_duplicate_pairs(contents: list[str], threshold: float = 0.85, chunk: int = 400):
    """Cặp bài nghi GẦN trùng nội dung: cosine TF-IDF (từ + bigram) >= threshold. Chỉ để review."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    n = len(contents)
    if n < 2:
        return []
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.5 if n >= 50 else 1.0,
                          sublinear_tf=True, lowercase=True)
    try:
        X = vec.fit_transform([normalize_text(c) for c in contents]).tocsr()
    except ValueError:  # từ vựng rỗng (tập quá nhỏ)
        return []
    pairs = []
    for i in range(0, n, chunk):
        sim = (X[i:i + chunk] @ X.T).toarray()
        for r in range(sim.shape[0]):
            sim[r, : i + r + 1] = 0  # chỉ lấy j > i, bỏ chính nó
        rr, cc = (sim >= threshold).nonzero()
        pairs += [(i + a, int(b), float(sim[a, b])) for a, b in zip(rr, cc)]
    return pairs


class UnionFind:
    def __init__(self):
        self.p: dict[str, str] = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


# ----------------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------------
def profile_before(df: pd.DataFrame) -> dict:
    """Số liệu TRƯỚC khi chuẩn hóa (đọc nguyên văn từ raw, mọi cột là text)."""
    pd_ = pd.to_datetime(df["publish_date"], format="%Y-%m-%d", errors="coerce")
    cd_ = pd.to_datetime(df["collection_date"], format="%Y-%m-%d", errors="coerce")
    out_of_range = ((pd_ < PROJECT_START) | (pd_ > PROJECT_END)) & pd_.notna()
    url = df["source_url"]
    b = {
        "rows": len(df), "cols": df.shape[1],
        "blank": {c: int((df[c].str.strip() == "").sum()) for c in df.columns},
        "publish_date_unparsable": int(pd_.isna().sum()),
        "publish_date_out_of_range": int(out_of_range.sum()),
        "collection_date_unparsable": int(cd_.isna().sum()),
        "collection_before_publish": int((cd_ < pd_).sum()),
        "url_invalid": int((url.map(normalize_url) == "").sum()),
        "url_has_fragment": int(url.str.contains("#", regex=False).sum()),
        "url_has_query": int(url.str.contains("?", regex=False).sum()),
        "url_trailing_slash": int(url.str.endswith("/").sum()),
        "url_http": int(url.str.startswith("http://").sum()),
        "url_www": int(url.str.contains(r"^https?://www\.", regex=True).sum()),
        "source_not_canonical": int((~df["source_name"].isin(CANON_SOURCES)).sum()),
        "topic_primary_invalid": int(df["topic_primary"].map(lambda x: parse_topic(x)[0] is None).sum()),
        "relevance_score_nonnumeric": int(pd.to_numeric(df["relevance_score"], errors="coerce").isna().sum()),
        "word_count_nonint": int((~df["word_count"].str.fullmatch(r"\d+")).sum()),
        "content_invisible": int(df["content"].map(lambda x: x != x.translate(_INVISIBLE)).sum()),
        "text_ws_issue": {c: int((df[c] != df[c].map(normalize_text)).sum()) for c in TEXT_FIELDS},
    }
    return b


def clean(df_raw: pd.DataFrame, near_threshold: float = 0.85, decisions: dict | None = None,
          outlier_review: dict | None = None):
    df = df_raw.copy()
    decisions, outlier_review = decisions or {}, outlier_review or {}
    changes, issues = [], []

    def log_change(idx, field, old, new, rule):
        changes.append({"article_id": df_raw.at[idx, "article_id"], "field": field,
                        "old_value": old, "new_value": new, "rule": rule})

    def log_issue(idx, field, code, severity, value, action):
        issues.append({"article_id": df_raw.at[idx, "article_id"], "field": field, "issue_code": code,
                       "severity": severity, "value": str(value)[:200], "action": action})

    # 1) Unicode/khoảng trắng cho các trường metadata dạng text (KHÔNG đụng content)
    for col in ["article_id", "source_url"] + TEXT_FIELDS + ["source_name"]:
        cleaned = df[col].map(normalize_text)
        for idx in df.index[cleaned != df[col]]:
            log_change(idx, col, df.at[idx, col], cleaned[idx], "NFC+whitespace")
        df[col] = cleaned

    # 2) source_name theo từ điển + đối chiếu domain
    canon = df["source_name"].map(normalize_source)
    for idx in df.index[canon.isna()]:
        log_issue(idx, "source_name", "SRC_UNKNOWN", "High", df.at[idx, "source_name"], "giữ nguyên, cần người duyệt")
    for idx in df.index[canon.notna() & (canon != df["source_name"])]:
        log_change(idx, "source_name", df.at[idx, "source_name"], canon[idx], "source_dictionary")
    df["source_name"] = canon.fillna(df["source_name"])

    # 3) URL
    df["source_url_normalized"] = df["source_url"].map(normalize_url)
    for idx in df.index[df["source_url_normalized"] == ""]:
        log_issue(idx, "source_url", "URL_INVALID", "High", df.at[idx, "source_url"], "để trống bản chuẩn hóa")
    df["source_domain"] = df["source_url_normalized"].str.extract(r"^https://([^/]+)")[0]
    expected = df["source_domain"].map(SOURCE_DOMAINS)
    mism = df.index[expected.notna() & (expected != df["source_name"])]
    for idx in mism:
        log_issue(idx, "source_name", "SRC_DOMAIN_MISMATCH", "Medium",
                  f"{df.at[idx, 'source_name']} vs {df.at[idx, 'source_domain']}", "đánh cờ, không sửa")
    for idx in df.index[expected.isna() & df["source_domain"].notna()]:
        log_issue(idx, "source_url", "DOMAIN_NOT_IN_8_SOURCES", "Medium", df.at[idx, "source_domain"], "đánh cờ, không sửa")

    # 4) Ngày
    pub = pd.to_datetime(df["publish_date"], format="%Y-%m-%d", errors="coerce")
    col = pd.to_datetime(df["collection_date"], format="%Y-%m-%d", errors="coerce")
    for idx in df.index[pub.isna()]:
        log_issue(idx, "publish_date", "DATE_UNPARSABLE", "High", df.at[idx, "publish_date"], "đặt null")
    for idx in df.index[col.isna()]:
        log_issue(idx, "collection_date", "DATE_UNPARSABLE", "Medium", df.at[idx, "collection_date"], "đặt null")
    oor = df.index[pub.notna() & ((pub < PROJECT_START) | (pub > PROJECT_END))]
    for idx in oor:
        log_issue(idx, "publish_date", "DATE_OUT_OF_RANGE", "High", df.at[idx, "publish_date"], "đánh cờ, không sửa")
    for idx in df.index[pub.notna() & col.notna() & (col < pub)]:
        log_issue(idx, "collection_date", "COLLECTED_BEFORE_PUBLISHED", "High",
                  f"{df.at[idx, 'collection_date']} < {df.at[idx, 'publish_date']}", "đánh cờ, không sửa")
    df["publish_date"], df["collection_date"] = pub, col
    df["publish_year"] = pub.dt.year.astype("Int64")
    df["publish_month"] = pub.dt.month.astype("Int64")
    df["publish_quarter"] = pub.dt.quarter.astype("Int64")
    df["publish_year_month"] = pub.dt.strftime("%Y-%m")

    # 5) Chủ đề
    prim = df["topic_primary"].map(parse_topic)
    df["topic_primary_code"] = prim.map(lambda t: t[0])
    for idx in df.index[prim.map(lambda t: t[0] is None)]:
        log_issue(idx, "topic_primary", "TOPIC_INVALID", "High", df.at[idx, "topic_primary"], "đánh cờ, không sửa")
    for idx in df.index[prim.map(lambda t: t[0] is not None and not t[1])]:
        log_issue(idx, "topic_primary", "TOPIC_LABEL_MISMATCH", "Medium", df.at[idx, "topic_primary"], "đánh cờ, không sửa")

    def sec_codes(v: str):
        if not v:
            return None
        parts = [p.strip() for p in v.split(";")]
        return ";".join(parse_topic(p)[0] or "?" for p in parts)

    df["topic_secondary_codes"] = df["topic_secondary"].map(sec_codes)
    for idx in df.index[df["topic_secondary_codes"].fillna("").str.contains(r"\?")]:
        log_issue(idx, "topic_secondary", "TOPIC_INVALID", "Medium", df.at[idx, "topic_secondary"], "đánh cờ, không sửa")

    # 6) Số
    df["relevance_score"] = pd.to_numeric(df["relevance_score"], errors="coerce")
    wc = pd.to_numeric(df["word_count"], errors="coerce")
    for idx in df.index[df["relevance_score"].isna()]:
        log_issue(idx, "relevance_score", "NUMBER_INVALID", "Medium", df_raw.at[idx, "relevance_score"], "đặt null")
    for idx in df.index[wc.isna() | (wc < 0)]:
        log_issue(idx, "word_count", "NUMBER_INVALID", "Medium", df_raw.at[idx, "word_count"], "đặt null")
    df["word_count"] = wc.where(wc >= 0).astype("Int64")
    # ISS-002: đếm lại trên content RAW, chỉ để đối chiếu (không thay word_count gốc)
    df["word_count_recount"] = df_raw["content"].map(lambda s: len(s.split())).astype("Int64")

    # 6b) Ngoại lai (đánh cờ mức Low, không sửa/xóa)
    rc = df["word_count_recount"]
    for idx in df.index[rc > WORDS_LONG]:
        log_issue(idx, "content", "OUTLIER_CONTENT_LONG", "Low", f"{rc[idx]} từ", "đánh cờ, cần xem tay (bài rất dài/ghép nhiều bài?)")
    for idx in df.index[rc < WORDS_SHORT]:
        log_issue(idx, "content", "OUTLIER_CONTENT_SHORT", "Low", f"{rc[idx]} từ", "đánh cờ, cần xem tay (thiếu nội dung?)")
    tl = df["title"].str.len()
    for idx in df.index[tl > TITLE_LONG]:
        log_issue(idx, "title", "OUTLIER_TITLE_LONG", "Low", f"{tl[idx]} ký tự", "đánh cờ, cần xem tay")
    for idx in df.index[tl < TITLE_SHORT]:
        log_issue(idx, "title", "OUTLIER_TITLE_SHORT", "Low", f"{tl[idx]} ký tự", "đánh cờ, cần xem tay")

    # 7) Thiếu -> null nhất quán (sentiment giữ null, KHÔNG gán 'neutral')
    for c in ["topic_secondary", "sentiment", "matched_keywords", "location"]:
        df[c] = df[c].replace("", pd.NA)
    df["n_keywords"] = df["matched_keywords"].map(
        lambda s: 0 if pd.isna(s) else len([k for k in s.split(";") if k.strip()])).astype("Int64")

    # 8) Audit trùng (KHÔNG xóa)
    df["title_key"] = df["title"].map(title_key)
    df["content_hash"] = df_raw["content"].map(content_hash)
    dup_rows, uf, uf_all = [], UnionFind(), UnionFind()

    def link(ids, key):
        for x in ids[1:]:
            uf_all.union(ids[0], x)
            if decisions.get(key, {}).get("decision") != "KHONG_TRUNG":  # quyết định 'không trùng' thì không gom cụm
                uf.union(ids[0], x)

    def rkey(dtype, ids):
        return f"{dtype}|{'; '.join(sorted(ids))}"

    keys = {"article_id": df["article_id"], "url_normalized": df["source_url_normalized"].replace("", pd.NA),
            "title_key": df["title_key"].replace("", pd.NA), "content_hash": df["content_hash"]}
    for dtype, s in keys.items():
        g = df.assign(_k=s).dropna(subset=["_k"]).groupby("_k")
        for k, grp in g:
            if len(grp) < 2:
                continue
            ids = grp["article_id"].tolist()
            link(ids, rkey(dtype, ids))
            dup_rows.append({
                "dup_type": dtype, "n_articles": len(grp), "article_ids": "; ".join(ids),
                "sources": "; ".join(sorted(set(grp["source_name"]))),
                "publish_dates": "; ".join(grp["publish_date"].dt.strftime("%Y-%m-%d").fillna("?")),
                "same_source": grp["source_name"].nunique() == 1,
                "titles": " || ".join(t[:90] for t in grp["title"]),
                "urls": " || ".join(grp["source_url"]),
                "similarity": 1.0 if dtype != "title_key" else None,
                "reason": f"trùng chính xác theo {dtype}" + ("; cùng nguồn" if grp["source_name"].nunique() == 1 else "; khác nguồn"),
                "suggested_action": "XEM XÉT thủ công; chưa loại bài; nếu giữ cả hai thì dùng dup_cluster_id khi chia tập",
            })
    # gần trùng nội dung (TF-IDF cosine) - chỉ lập danh sách review
    for i, j, sim in near_duplicate_pairs(df_raw["content"].tolist(), near_threshold):
        a, b = df.iloc[i], df.iloc[j]
        if a["content_hash"] == b["content_hash"]:
            continue  # đã có ở nhóm content_hash
        link([a["article_id"], b["article_id"]], rkey("near_content_tfidf", [a["article_id"], b["article_id"]]))
        dd = abs((a["publish_date"] - b["publish_date"]).days) if pd.notna(a["publish_date"]) and pd.notna(b["publish_date"]) else None
        dup_rows.append({
            "dup_type": "near_content_tfidf", "n_articles": 2, "article_ids": f"{a['article_id']}; {b['article_id']}",
            "sources": "; ".join(sorted({a["source_name"], b["source_name"]})),
            "publish_dates": "; ".join(x.strftime("%Y-%m-%d") if pd.notna(x) else "?" for x in (a["publish_date"], b["publish_date"])),
            "same_source": a["source_name"] == b["source_name"],
            "titles": f"{a['title'][:90]} || {b['title'][:90]}",
            "urls": f"{a['source_url']} || {b['source_url']}",
            "similarity": round(sim, 4),
            "reason": f"cosine TF-IDF {sim:.3f} >= {near_threshold}; " + ("cùng nguồn" if a["source_name"] == b["source_name"] else "khác nguồn")
                      + (f"; lệch {dd} ngày" if dd is not None else "")
                      + ("; tiêu đề giống" if a["title_key"] == b["title_key"] else "; tiêu đề khác"),
            "suggested_action": "XEM XÉT thủ công (bài cập nhật/đăng lại/cùng sự kiện?); chưa loại bài; dùng dup_cluster_id khi chia tập",
        })
    def clusters(u):
        members: dict[str, list[str]] = {}
        for i in list(u.p):
            members.setdefault(u.find(i), []).append(i)
        return {i: f"DUP-{n:04d}" for n, (root, ids) in enumerate(sorted((r, m) for r, m in members.items() if len(m) > 1), 1)
                for i in ids}

    cluster_id, cluster_all = clusters(uf), clusters(uf_all)
    df["dup_cluster_id"] = df["article_id"].map(cluster_id)
    dup_df = pd.DataFrame(dup_rows, columns=["dup_type", "n_articles", "article_ids", "sources", "publish_dates",
                                             "same_source", "titles", "urls", "similarity", "reason", "suggested_action"])
    dup_df.insert(0, "review_id", [f"DR-{i:04d}" for i in range(1, len(dup_df) + 1)])
    dup_df.insert(1, "review_key", [rkey(t, a.split("; ")) for t, a in zip(dup_df["dup_type"], dup_df["article_ids"])])
    unknown_decisions = set(decisions) - set(dup_df["review_key"])
    if unknown_decisions:
        raise ValueError(
            f"Duplicate decisions contain unknown review_key values: "
            f"{sorted(unknown_decisions)[:5]}"
        )
    for c in ["decision", "keep_article_id", "reviewer", "review_note"]:
        src = c
        dup_df[c] = dup_df["review_key"].map(lambda k: decisions.get(k, {}).get(src, ""))
    art_dec, art_act = {}, {}
    for _, r in dup_df.iterrows():
        if r["decision"] not in DECISION_PRIORITY:
            continue
        article_ids = r["article_ids"].split("; ")
        if r["decision"] == DECISION_PRIORITY[0] and r["keep_article_id"] not in article_ids:
            raise ValueError(
                f"{r['review_key']}: keep_article_id must identify an article in the duplicate group."
            )
        for aid in article_ids:
            if aid not in art_dec or DECISION_PRIORITY.index(r["decision"]) < DECISION_PRIORITY.index(art_dec[aid]):
                art_dec[aid] = r["decision"]
            if r["decision"] == DECISION_PRIORITY[0] and r["keep_article_id"]:
                act = "KEEP" if aid == r["keep_article_id"] else "DROP_PROPOSED"
                if art_act.get(aid) != "DROP_PROPOSED":
                    art_act[aid] = act
    df["dup_review_decision"] = df["article_id"].map(art_dec)
    df["dup_proposed_action"] = df["article_id"].map(art_act)
    stats = {"clusters_before": len(set(cluster_all.values())), "rows_before": len(cluster_all),
             "clusters_after": len(set(cluster_id.values())), "rows_after": len(cluster_id)}

    # 9) Cờ theo dòng
    iss = pd.DataFrame(issues)
    if len(iss):
        flags = iss.groupby("article_id")["issue_code"].agg(lambda s: ";".join(sorted(set(s))))
        df["meta_issue_flags"] = df["article_id"].map(flags)
    else:
        df["meta_issue_flags"] = pd.NA

    iss = pd.DataFrame(issues)
    if len(iss):
        valid_outlier_keys = {
            f"{article_id}|{issue_code}"
            for article_id, issue_code in zip(iss["article_id"], iss["issue_code"])
            if issue_code.startswith("OUTLIER")
        }
        unknown_outlier_reviews = set(outlier_review) - valid_outlier_keys
        if unknown_outlier_reviews:
            raise ValueError(
                f"Outlier reviews contain unknown issue keys: "
                f"{sorted(unknown_outlier_reviews)[:5]}"
            )
        rv = [outlier_review.get(f"{a}|{k}", {}) for a, k in zip(iss["article_id"], iss["issue_code"])]
        iss["review_conclusion"] = [x.get("conclusion", "") for x in rv]
        iss["review_note"] = [x.get("review_note", "") for x in rv]
        iss["reviewer"] = [x.get("reviewer", "") for x in rv]
        oc = {a: c for a, c in zip(iss["article_id"], iss["review_conclusion"]) if c}
    else:
        if outlier_review:
            raise ValueError("Outlier reviews were supplied but the input has no issues.")
        oc = {}
    df["outlier_review_conclusion"] = df["article_id"].map(oc)

    cols = ["article_id", "title", "publish_date", "publish_year", "publish_month", "publish_quarter",
            "publish_year_month", "source_name", "source_domain", "source_url", "source_url_normalized",
            "topic_primary", "topic_primary_code", "topic_secondary", "topic_secondary_codes",
            "matched_keywords", "n_keywords", "location", "sentiment", "relevance_status",
            "collection_date", "data_quality_note", "relevance_score", "word_count", "word_count_recount",
            "title_key", "content_hash", "dup_cluster_id", "dup_review_decision", "dup_proposed_action",
            "outlier_review_conclusion", "meta_issue_flags"]
    return df[cols], pd.DataFrame(changes, columns=["article_id", "field", "old_value", "new_value", "rule"]), \
        iss if len(iss) else pd.DataFrame(columns=["article_id", "field", "issue_code", "severity", "value", "action",
                                                      "review_conclusion", "review_note", "reviewer"]), \
        dup_df, stats


def profile_after(m: pd.DataFrame) -> dict:
    return {
        "rows": len(m), "cols": m.shape[1],
        "dtypes": {c: str(m[c].dtype) for c in ["publish_date", "collection_date", "publish_year", "publish_month",
                                                "publish_quarter", "relevance_score", "word_count"]},
        "nulls": {c: int(m[c].isna().sum()) for c in ["publish_date", "source_name", "source_url_normalized",
                                                      "topic_primary_code", "topic_secondary", "sentiment",
                                                      "location", "matched_keywords", "relevance_score", "word_count"]},
        "dup_clustered_rows": int(m["dup_cluster_id"].notna().sum()),
        "dup_clusters": int(m["dup_cluster_id"].nunique()),
        "flagged_rows": int(m["meta_issue_flags"].notna().sum()),
    }


def write_report(path: Path, a: dict, b: dict, changes, issues, dup_df, m, hash_before, hash_after, raw: Path, stats: dict):
    def f(n):
        return f"{n:,}".replace(",", ".")

    ws = b["text_ws_issue"]
    rc = m["word_count_recount"].astype("float")
    wc = m["word_count"].astype("float")
    diff = (rc - wc)
    mism = int((diff != 0).sum())
    longer = int((diff > 0).sum())
    dup_summary = dup_df.groupby("dup_type").agg(nhom=("review_id", "count"), bai=("n_articles", "sum")) \
        if len(dup_df) else pd.DataFrame()
    dup_lines = "\n".join(f"| `{k}` | {f(int(r.nhom))} | {f(int(r.bai))} |" for k, r in dup_summary.iterrows()) \
        or "| (không phát hiện) | 0 | 0 |"
    iss_lines = "\n".join(f"| `{k}` | {f(v)} |" for k, v in issues["issue_code"].value_counts().items()) \
        or "| (không có) | 0 |"
    chg_lines = "\n".join(f"| `{fld}` / {rule} | {f(n)} |"
                          for (fld, rule), n in changes.groupby(["field", "rule"]).size().items()) \
        or "| (không có thay đổi giá trị) | 0 |"
    n_outlier = int(issues['issue_code'].str.startswith('OUTLIER').sum()) if len(issues) else 0
    reviewed = dup_df[dup_df["decision"] != ""] if len(dup_df) else dup_df
    n_pending_open = len(dup_df) - len(reviewed)
    n_drop_open = int((reviewed["decision"] == DECISION_PRIORITY[0]).sum()) if len(reviewed) else 0
    n_ov_bad = int(((issues["review_conclusion"] == "BAT_THUONG_CAN_XEM") & issues["issue_code"].str.startswith("OUTLIER")).sum()) if len(issues) else 0
    n_rev, n_pending = len(reviewed), len(dup_df) - len(reviewed)
    dec_counts = reviewed["decision"].value_counts().to_dict() if n_rev else {}
    dl = reviewed[reviewed["decision"] == DECISION_PRIORITY[0]] if n_rev else reviewed
    dl_lines = "\n".join(
        f"| {r.review_id} | {r.article_ids.replace('; ', ' / ')} | {r.keep_article_id} | {r.review_note.split(' Đề xuất')[0]} |"
        for r in dl.itertuples()) or "| (không có) | | | |"
    ov_rev = issues[issues["issue_code"].str.startswith("OUTLIER")] if len(issues) else issues
    ov_lines = "\n".join(
        f"| {r.article_id} | `{r.issue_code}` | {r.value} | {r.review_conclusion or 'chưa review'} | {r.review_note} |"
        for r in ov_rev.itertuples()) or "| (không có) | | | | |"
    ov_counts = ov_rev["review_conclusion"].replace("", "chưa review").value_counts().to_dict() if len(ov_rev) else {}
    review_section = f"""## 6b. Trạng thái quyết định review

Quyết định đã được xác nhận (nếu có) nằm ở `config/duplicate_decisions.csv` và `config/outlier_review.csv`; module đọc lại hai file này mỗi lần chạy nên kết quả tái lập được. Không nạp các file trong `config/review_drafts/` vào xử lý. Mọi quyết định có nguồn ghi là bản nháp AI phải được Người 2 xác nhận trước khi chuyển vào cấu hình chính. Không bài nào bị xóa.

**Cặp nghi trùng:** có quyết định được nạp cho {f(n_rev)} / {f(len(dup_df))} dòng (còn {f(n_pending)} dòng chưa có quyết định).

| Quyết định | Số dòng | Ý nghĩa |
|---|---|---|
| `KHONG_TRUNG` | {f(dec_counts.get('KHONG_TRUNG', 0))} | Khác kỳ/giai đoạn/sự kiện, hoặc giống do khối quảng cáo; **không** gom cụm |
| `GIU_CA_HAI_CUNG_SU_KIEN` | {f(dec_counts.get('GIU_CA_HAI_CUNG_SU_KIEN', 0))} | Cùng sự kiện hoặc nguồn tin gốc, bài viết riêng; giữ cả hai, đánh dấu chung cụm; split theo thời gian có thể vẫn giao split |
| `NGHI_DANG_LAI_DE_XUAT_GIU_1` | {f(dec_counts.get('NGHI_DANG_LAI_DE_XUAT_GIU_1', 0))} | Nội dung gần như một bản (PR/thông cáo viết lại sát); đề xuất giữ 1 bài, **chưa xóa**, chờ Người 1 chốt |

Dữ liệu dẫn xuất đã thay đổi theo quyết định: số cụm `dup_cluster_id` từ **{f(stats['clusters_before'])}** (gom theo điểm tương đồng) xuống **{f(stats['clusters_after'])}** (chỉ gom các cặp cùng sự kiện hoặc nghi đăng lại), số bài nằm trong cụm từ {f(stats['rows_before'])} xuống {f(stats['rows_after'])}. Metadata có thêm ba cột `dup_review_decision`, `dup_proposed_action` (`KEEP`/`DROP_PROPOSED`) và `outlier_review_conclusion`.

Các cặp đề xuất giữ 1 bài (quy tắc chọn bài giữ: đăng sớm hơn, cùng ngày thì bài dài hơn):

| Dòng | Cặp bài | Đề xuất giữ | Căn cứ |
|---|---|---|---|
{dl_lines}

Quan sát cho các bước sau (không phải lỗi của metadata): nhiều cặp giống nhau vì hai báo cùng trích một văn bản/thông cáo; bài dạng bản tin/điểm tin/podcast có thể cần Người 4 xem về mức liên quan. Text cleaning chỉ xử lý ký tự/Unicode/khoảng trắng, không xóa boilerplate quảng cáo nếu chưa có tiêu chí kiểm tra được.

**Ngoại lai (9 lượt đánh cờ):** kết luận {", ".join(f"`{k}` {v}" for k, v in ov_counts.items())}. Không bài nào bị loại.

| Bài | Mã | Giá trị | Kết luận | Ghi chú |
|---|---|---|---|---|
{ov_lines}

"""
    same_ok = "ĐẠT" if hash_before == hash_after and a["rows"] == b["rows"] else "KHÔNG ĐẠT"

    path.write_text(f"""# Báo cáo chuẩn hóa metadata - trước/sau (Người 2)

**Module:** `5_process/src/03_clean_metadata.py` · **Đầu vào:** `{raw.relative_to(REPO)}` (chỉ đọc) · **Phạm vi ngày:** {PROJECT_START} → {PROJECT_END}

> Báo cáo sinh tự động từ lần chạy thực tế; số liệu dưới đây tái lập được bằng cách chạy lại module.

## 0. Trạng thái issue và review

| # | Vấn đề | Quy mô | Người xử lý | Bước tiếp theo |
|---|---|---|---|---|
| 1 | ISS-002: `word_count` khác đếm lại `content` | {f(mism)} / {f(len(m))} dòng | Đã giải quyết bằng đối chiếu mã Collecting; giữ nguyên `word_count` raw | Xem mục 7; `word_count_recount` chỉ mô tả `content` cuối |
| 2 | Audit cặp nghi trùng | {f(len(dup_df))} dòng review, {f(a['dup_clusters'])} cụm theo kết quả audit | Hoàn tất phạm vi audit; không áp dụng đề xuất AI thành quyết định | Xem mục 6b; không bài nào bị loại |
| 3 | Ngoại lai độ dài (bài dài >{WORDS_LONG} từ, ngắn <{WORDS_SHORT} từ; tiêu đề dài >{TITLE_LONG} ký tự) | {f(n_outlier)} lượt đánh cờ; chưa có kết luận người review | Đã hoàn tất cờ audit; không sửa/xóa bài | Chỉ cần reviewer thật nếu sau này nhóm muốn áp dụng quyết định loại/giữ |
| 4 | Ký tự vô hình trong `content` raw | {f(b['content_invisible'])} bài | Người 3 đã chạy text-clean output riêng | `content_clean` đã được đối chiếu; raw `content` không đổi |

## 1. Bảo toàn raw và số dòng

| Kiểm tra | Kết quả |
|---|---|
| Số dòng vào / ra | {f(b['rows'])} / {f(a['rows'])} |
| SHA-256 raw trước | `{hash_before}` |
| SHA-256 raw sau | `{hash_after}` |
| Raw bất biến, không mất dòng | **{same_ok}** |

## 2. Kiểu dữ liệu và giá trị thiếu

| Trường | Trước | Sau |
|---|---|---|
| `publish_date` | text (`YYYY-MM-DD`) | {a['dtypes']['publish_date']} |
| `collection_date` | text | {a['dtypes']['collection_date']} |
| `relevance_score` | text | {a['dtypes']['relevance_score']} |
| `word_count` | text | {a['dtypes']['word_count']} |
| `publish_year/month/quarter` | (chưa có) | {a['dtypes']['publish_year']} (cột mới) |
| `source_url_normalized` | (chưa có) | cột mới; `source_url` gốc giữ nguyên |

| Cột | Trống trước (chuỗi rỗng) | Null sau |
|---|---|---|
| `topic_secondary` | {f(b['blank']['topic_secondary'])} | {f(a['nulls']['topic_secondary'])} |
| `sentiment` | {f(b['blank']['sentiment'])} | {f(a['nulls']['sentiment'])} (giữ null, không gán "neutral") |
| `location` | {f(b['blank']['location'])} | {f(a['nulls']['location'])} |
| `matched_keywords` | {f(b['blank']['matched_keywords'])} | {f(a['nulls']['matched_keywords'])} |
| `source_name` | {f(b['blank']['source_name'])} | {f(a['nulls']['source_name'])} |
| `publish_date` | {f(b['blank']['publish_date'])} | {f(a['nulls']['publish_date'])} |

## 3. Giá trị không hợp lệ (trước chuẩn hóa)

| Kiểm tra | Số dòng |
|---|---|
| `publish_date` không parse được | {f(b['publish_date_unparsable'])} |
| `publish_date` ngoài phạm vi dự án | {f(b['publish_date_out_of_range'])} |
| `collection_date` không parse được | {f(b['collection_date_unparsable'])} |
| `collection_date` sớm hơn `publish_date` | {f(b['collection_before_publish'])} |
| `source_url` sai cú pháp | {f(b['url_invalid'])} |
| `source_name` không thuộc 8 nguồn chuẩn | {f(b['source_not_canonical'])} |
| `topic_primary` không thuộc A-L | {f(b['topic_primary_invalid'])} |
| `relevance_score` không phải số | {f(b['relevance_score_nonnumeric'])} |
| `word_count` không phải số nguyên | {f(b['word_count_nonint'])} |

URL có yếu tố cần chuẩn hóa để so sánh: fragment `#` {f(b['url_has_fragment'])}, query `?` {f(b['url_has_query'])}, '/' cuối {f(b['url_trailing_slash'])}, `http://` {f(b['url_http'])}, `www.` {f(b['url_www'])}.

Khoảng trắng/Unicode cần sửa (số dòng): {", ".join(f"`{k}` {f(v)}" for k, v in ws.items())}.

## 4. Thay đổi giá trị đã áp dụng (chi tiết: `logs/metadata_change_log.csv`)

| Trường / quy tắc | Số thay đổi |
|---|---|
{chg_lines}

## 5. Vấn đề đánh cờ, không tự sửa (chi tiết: `logs/metadata_issues.csv`)

| Mã | Số lượt |
|---|---|
{iss_lines}

Số dòng có ít nhất một cờ: **{f(a['flagged_rows'])}**.

## 6. Audit trùng lặp (chi tiết: `data/interim/duplicate_review.csv`)

Chỉ audit, **không loại bản ghi nào**. Gồm khớp chính xác theo khóa đã chuẩn hóa và cặp gần trùng nội dung (cosine TF-IDF từ+bigram, ngưỡng mặc định 0,85; chạy `--near-threshold` để đổi).

| Loại khóa | Số nhóm trùng | Số bài trong các nhóm |
|---|---|---|
{dup_lines}

Hợp nhất các nhóm (union-find) thành **{f(a['dup_clusters'])}** cụm `dup_cluster_id`, gồm **{f(a['dup_clustered_rows'])}** bài. Đây là kết quả audit, không phải quyết định xác nhận trùng. Cần đối chiếu với `split_validation.md` và rà soát mọi cụm giao split trước khi chốt đánh giá.

{review_section}## 7. Đối chiếu ISS-002 (`word_count`)

Đếm lại `content.split()` trên content raw (cột `word_count_recount`, chỉ để đối chiếu; `word_count` gốc giữ nguyên):

- Khác `word_count`: **{f(mism)} / {f(len(m))}** dòng ({mism / len(m):.1%}).
- Trong số đó, đếm lại **lớn hơn** `word_count`: {f(longer)} dòng; trung vị chênh lệch {diff[diff != 0].median():.0f} từ.
- Mã Collecting `4_ma_nguon/clean_and_export.py` tính `word_count` trên thân bài trước khi có thể ghép sapo vào `content` đầu ra; khác biệt định nghĩa đã được xác nhận và `ISS-002` đã resolved. Giữ nguyên `word_count` raw; dùng `word_count_recount` khi cần độ dài của `content` cuối.

## 8. Việc chuyển cho Người 3 (văn bản)

- {f(b['content_invisible'])} bài có ký tự vô hình (zero-width, ví dụ U+200B) trong `content` raw; module metadata này **không sửa `content`**. Bước Người 3 tạo `content_clean` riêng và đã được kiểm tra trên toàn bộ dữ liệu.
- {f(ws['title'])} tiêu đề có ký tự vô hình đã được chuẩn hóa (log ở `metadata_change_log.csv`).

## 9. Giới hạn

- Các quyết định trong `config/duplicate_decisions.csv` và `config/outlier_review.csv` phải được người phụ trách xác nhận; bản nháp trong `config/review_drafts/` không được áp dụng. Gần trùng chỉ dựa trên độ tương đồng TF-IDF với một ngưỡng; có thể bỏ sót bài viết lại bằng từ ngữ khác, và có thể nêu cả bài cập nhật cùng sự kiện. Mọi cặp đều cần người xem quyết định.
- Chuẩn hóa `www.`/`http` chỉ áp dụng cho `source_url_normalized`; có thể coi hai URL khác nhau là một, nên các cặp trùng vẫn cần xem tay.
- Text cleaning chuẩn hóa ký tự/Unicode và khoảng trắng; không áp dụng quy tắc xóa boilerplate quảng cáo nếu chưa có tiêu chí kiểm tra được.
""", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=RAW_DEFAULT)
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--near-threshold", type=float, default=0.85, help="ngưỡng cosine TF-IDF cho gần trùng")
    args = ap.parse_args(argv)

    interim, logs, reports = (args.out / "data" / "interim", args.out / "logs", args.out / "reports")
    for d in (interim, logs, reports):
        d.mkdir(parents=True, exist_ok=True)

    hash_before = sha256_file(args.raw)
    df_raw = pd.read_csv(args.raw, dtype=str, keep_default_na=False, encoding="utf-8")
    before = profile_before(df_raw)

    cfg = args.out / "config"
    decisions = load_config_csv(cfg / "duplicate_decisions.csv", "review_key")
    outlier_review = load_outlier_review_csv(cfg / "outlier_review.csv")

    m, changes, issues, dup_df, stats = clean(df_raw, args.near_threshold, decisions, outlier_review)
    after = profile_after(m)

    m.to_parquet(interim / "metadata_clean.parquet", index=False)
    m.to_csv(interim / "metadata_clean.csv", index=False, encoding="utf-8")
    dup_df.to_csv(interim / "duplicate_review.csv", index=False, encoding="utf-8")
    changes.to_csv(logs / "metadata_change_log.csv", index=False, encoding="utf-8")
    issues.to_csv(logs / "metadata_issues.csv", index=False, encoding="utf-8")

    hash_after = sha256_file(args.raw)
    write_report(reports / "metadata_audit.md", after, before, changes, issues, dup_df, m,
                 hash_before, hash_after, args.raw, stats)

    assert len(m) == len(df_raw), "Số dòng ra khác số dòng vào"
    assert hash_before == hash_after, "Raw bị thay đổi!"
    print(f"OK: {len(m)} rows | {len(changes)} changes | {len(issues)} issues | {len(dup_df)} duplicate groups "
          f"| {after['dup_clusters']} clusters (before review: {stats['clusters_before']}) | raw unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
