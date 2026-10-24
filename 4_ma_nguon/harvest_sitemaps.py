"""Giai đoạn 1-2: duyệt sitemap của từng nguồn (2022 -> nay), lưu toàn bộ URL bài viết và đánh dấu URL ứng viên.

Đầu ra: data/urls/<source>.jsonl  (mỗi dòng: url, lastmod, sm_title, sitemap, candidate)
Chạy lại an toàn: các sitemap đã xử lý được ghi vào data/urls/<source>.done
Dùng: python scripts/harvest_sitemaps.py [source ...]
"""
import html
import json
import re
import sys
import threading
from datetime import date

from common import SOURCES, URLS_DIR, polite_get
from keywords import slug_is_candidate

YEARS = set(range(2022, date.today().year + 1))


def child_sitemaps(index_xml):
    locs = [html.unescape(l) for l in re.findall(r"<loc>\s*(.*?)\s*</loc>", index_xml)]
    out = []
    for l in locs:
        ys = [int(y) for y in re.findall(r"(20\d\d)", l.rsplit("/", 1)[-1])]
        if ys and ys[0] in YEARS:
            out.append(l)
    return out


URL_BLOCK = re.compile(r"<url>(.*?)</url>", re.S)


def parse_urlset(xml):
    for block in URL_BLOCK.findall(xml):
        loc = re.search(r"<loc>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</loc>", block, re.S)
        if not loc:
            continue
        lm = re.search(r"<lastmod>(.*?)</lastmod>", block)
        t = re.search(r"<(?:news:title|image:title)>(.*?)</(?:news:title|image:title)>", block, re.S)
        title = ""
        if t:
            title = html.unescape(t.group(1))
            title = re.sub(r"^<!\[CDATA\[|\]\]>$", "", title.strip()).strip()
        yield html.unescape(loc.group(1).strip()), (lm.group(1)[:10] if lm else ""), title


def harvest(src):
    cfg = SOURCES[src]
    out_path, done_path = URLS_DIR / f"{src}.jsonl", URLS_DIR / f"{src}.done"
    done = set(done_path.read_text(encoding="utf-8").split()) if done_path.exists() else set()
    r = polite_get(cfg["index"], delay=cfg["delay"])
    if r is None or r.status_code != 200:
        print(f"[{src}] không tải được sitemap index", flush=True)
        return
    children = [c for c in child_sitemaps(r.text) if c not in done]
    print(f"[{src}] {len(children)} sitemap con cần xử lý", flush=True)
    n_all = n_cand = 0
    with open(out_path, "a", encoding="utf-8") as fo, open(done_path, "a", encoding="utf-8") as fd:
        for i, sm in enumerate(children, 1):
            resp = polite_get(sm, delay=cfg["delay"], timeout=90)
            if resp is None or resp.status_code != 200:
                print(f"[{src}] lỗi {sm}", flush=True)
                continue
            rows = list(parse_urlset(resp.text))
            for url, lastmod, title in rows:
                cand = slug_is_candidate(url, title)
                n_cand += cand
                fo.write(json.dumps({"url": url, "lastmod": lastmod, "sm_title": title, "sitemap": sm,
                                     "candidate": cand}, ensure_ascii=False) + "\n")
            n_all += len(rows)
            fd.write(sm + "\n")
            fo.flush(); fd.flush()
            if i % 20 == 0:
                print(f"[{src}] {i}/{len(children)} sitemap, {n_all} url, {n_cand} ứng viên", flush=True)
    print(f"[{src}] XONG: {n_all} url, {n_cand} ứng viên", flush=True)


if __name__ == "__main__":
    srcs = sys.argv[1:] or list(SOURCES)
    ts = [threading.Thread(target=harvest, args=(s,)) for s in srcs]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
