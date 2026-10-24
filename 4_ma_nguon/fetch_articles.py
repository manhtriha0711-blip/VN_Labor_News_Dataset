"""Giai đoạn 3: tải và trích xuất bài viết từ các URL ứng viên.

Đầu ra: data/raw/<source>.jsonl (url, http_status, title, sapo, content, publish_date, author, fetched_at, error)
- Chạy lại sẽ bỏ qua URL đã tải (checkpoint theo từng dòng).
- Ưu tiên URL có slug "mạnh", trộn ngẫu nhiên (seed cố định) để phân bố đều theo thời gian.
Dùng: python scripts/fetch_articles.py --budget 4000 [--sources dantri tuoitre ...]
"""
import argparse
import html
import json
import random
import re
import threading
from datetime import datetime

from bs4 import BeautifulSoup

from common import DATE_FROM, RAW_DIR, SOURCES, URLS_DIR, norm_text, normalize_url, polite_get, strip_accents
from keywords import slug_of

STRONG_SLUG = re.compile(
    r"(?:^|-)(?:that-nghiep|mat-viec|viec-lam|nguoi-lao-dong|cong-doan|dinh-cong|tien-luong|no-luong|"
    r"cham-luong|tang-luong|luong-toi-thieu|luong-co-so|luong-huu|bhxh|bao-hiem-xa-hoi|bao-hiem-that-nghiep|"
    r"sa-thai|cat-giam-(?:lao-dong|nhan-su|nhan-vien|cong-nhan|bien-che)|nghi-viec|thoi-viec|ngung-viec|"
    r"hop-dong-lao-dong|tai-nan-lao-dong|an-toan-lao-dong|xuat-khau-lao-dong|lao-dong|thuong-tet|"
    r"lua-dao-tuyen-dung|viec-nhe-luong-cao|dao-tao-nghe|hoc-nghe|tinh-gian|tuyen-dung|nhan-luc|tro-cap|"
    r"tang-ca|nghi-huu|shipper|tai-xe-cong-nghe|nhay-viec|kiet-suc|ap-luc-cong-viec|an-sinh)(?:-|$)")

CONTENT_SEL = {
    "dantri": ["div.singular-content", "div.e-magazine__body", "div.dt-news__content", "article"],
    "tuoitre": ["div.detail-content", "div#main-detail-body"],
    "thanhnien": ["div.detail-content", "div.detail-cmain"],
    "vietnamnet": ["div#maincontent", "div.maincontent", "div.content-detail"],
    "tienphong": ["div.article__body"],
    "nhandan": ["div.article__body"],
    "sggp": ["div.article__body"],
    "vneconomy": ["main#article-editor", "div.detail__content", "div.news-content"],
}
JUNK_CLASS = re.compile(r"relate|VCSortableInPreviewMode|banner|ads?\b|advert|box-tin|tin-lien-quan|"
                        r"knc-|author|social|share|comment|tags?\b|readmore|xem-them|embed", re.I)


def extract(src, url, text):
    soup = BeautifulSoup(text, "lxml")

    def meta(*keys):
        for k in keys:
            m = soup.find("meta", attrs={"property": k}) or soup.find("meta", attrs={"name": k}) \
                or soup.find("meta", attrs={"itemprop": k})
            if m and m.get("content"):
                return html.unescape(m["content"]).strip()
        return ""

    # Ngày xuất bản: JSON-LD -> meta
    pub = ""
    for s in soup.find_all("script", type="application/ld+json"):
        m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', s.string or s.get_text() or "")
        if m:
            pub = html.unescape(m.group(1)); break
    pub = pub or meta("article:published_time", "datePublished", "pubdate", "publishdate")
    m = re.match(r"(\d{4}-\d{2}-\d{2})", pub)
    publish_date = m.group(1) if m else ""

    h1 = soup.find("h1")
    title = norm_text(h1.get_text(" ")) if h1 and h1.get_text(strip=True) else ""
    title = title or norm_text(meta("og:title", "twitter:title"))
    sapo = norm_text(meta("description", "og:description"))
    author = norm_text(meta("author", "article:author"))

    box, fallback = None, False
    for sel in CONTENT_SEL.get(src, []):
        box = soup.select_one(sel)
        if box and len(box.get_text(strip=True)) > 200:
            break
        box = None
    if box is None:  # dự phòng: phần tử cha chứa nhiều chữ trong <p> nhất
        score = {}
        for p in soup.find_all("p"):
            score[p.parent] = score.get(p.parent, 0) + len(p.get_text(strip=True))
        box = max(score, key=score.get) if score else None
        fallback = True
    paras = []
    if box is not None:
        for bad in box.find_all(["script", "style", "figure", "figcaption", "table", "iframe", "noscript"]):
            bad.decompose()
        for bad in box.find_all(True, class_=JUNK_CLASS):
            bad.decompose()
        for el in box.find_all(["p", "h2", "h3", "li"]):
            if el.find_parent(["li"]) and el.name != "li":
                continue
            t = norm_text(el.get_text(" "))
            if len(t) >= 25 and t not in paras:
                paras.append(t)
    content = "\n".join(paras)
    return {"title": title, "sapo": sapo, "content": content, "publish_date": publish_date, "author": author,
            "content_fallback": fallback}


def load_queue(src, budget, seed=42):
    rows, seen = [], set()
    for line in open(URLS_DIR / f"{src}.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if not r["candidate"]:
            continue
        nu = normalize_url(r["url"])
        if nu in seen:
            continue
        seen.add(nu)
        if r["lastmod"] and r["lastmod"] < DATE_FROM and src != "vietnamnet":
            continue
        s = slug_of(r["url"]) + "-" + re.sub(r"[^a-z0-9]+", "-", strip_accents(r.get("sm_title", "")).lower())
        # slug "cong-nhan" nhập nhằng (công nhân / công nhận) nên chỉ coi là mạnh khi tiêu đề có dấu xác nhận
        strong = STRONG_SLUG.search(s) or "công nhân" in r.get("sm_title", "").lower()
        r["prio"] = 0 if strong else 1
        rows.append(r)
    rnd = random.Random(seed)
    rnd.shuffle(rows)
    rows.sort(key=lambda r: r["prio"])  # sort ổn định: giữ thứ tự ngẫu nhiên trong cùng mức ưu tiên
    return rows[:budget], len(rows)


def worker(src, budget):
    cfg = SOURCES[src]
    out = RAW_DIR / f"{src}.jsonl"
    done = set()
    if out.exists():
        done = {normalize_url(json.loads(l)["url"]) for l in open(out, encoding="utf-8")}
    queue, total = load_queue(src, budget)
    todo = [r for r in queue if normalize_url(r["url"]) not in done]
    print(f"[{src}] ứng viên={total}, ngân sách={budget}, đã tải={len(done)}, cần tải={len(todo)}", flush=True)
    ok = 0
    with open(out, "a", encoding="utf-8") as fo:
        for i, r in enumerate(todo, 1):
            rec = {"source": src, "url": r["url"], "sm_title": r.get("sm_title", ""), "prio": r["prio"],
                   "fetched_at": datetime.now().strftime("%Y-%m-%d")}
            resp = polite_get(r["url"], delay=cfg["delay"])
            if resp is None:
                rec.update(http_status=0, error="timeout/connection")
            else:
                rec["http_status"] = resp.status_code
                if resp.status_code == 200:
                    try:
                        rec.update(extract(src, r["url"], resp.text))
                        rec["final_url"] = resp.url
                        ok += 1
                    except Exception as e:  # ghi nhận lỗi, không bỏ qua im lặng
                        rec["error"] = f"parse: {e}"
                else:
                    rec["error"] = f"http {resp.status_code}"
            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fo.flush()
            if i % 200 == 0:
                print(f"[{src}] {i}/{len(todo)} (ok {ok})", flush=True)
    print(f"[{src}] XONG: tải thành công {ok}/{len(todo)}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=4000)
    ap.add_argument("--sources", nargs="*", default=list(SOURCES))
    a = ap.parse_args()
    ts = [threading.Thread(target=worker, args=(s, a.budget)) for s in a.sources]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
