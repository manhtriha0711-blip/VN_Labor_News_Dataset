"""Tiện ích dùng chung: cấu hình nguồn, HTTP lịch sự (giới hạn tốc độ theo host, retry), chuẩn hóa văn bản."""
import re
import threading
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
URLS_DIR = DATA / "urls"
RAW_DIR = DATA / "raw"
OUT_DIR = ROOT / "output"
for d in (URLS_DIR, RAW_DIR, OUT_DIR):
    d.mkdir(parents=True, exist_ok=True)

DATE_FROM = "2022-01-01"
USER_AGENT = "Mozilla/5.0 (compatible; VN-Labor-News-Dataset/1.0; academic Data Mining coursework)"

# Nguồn: tên hiển thị, sitemap index, khoảng nghỉ giữa 2 request (giây)
SOURCES = {
    "dantri":     {"name": "Dân Trí",    "index": "https://dantri.com.vn/sitemaps/articles.xml", "delay": 1.0},
    "tuoitre":    {"name": "Tuổi Trẻ",   "index": "https://tuoitre.vn/sitemaps/index.rss",       "delay": 0.8},
    "thanhnien":  {"name": "Thanh Niên", "index": "https://thanhnien.vn/sitemap.xml",            "delay": 0.8},
    "vietnamnet": {"name": "VietNamNet", "index": "https://vietnamnet.vn/sitemap.xml",           "delay": 0.8},
    "tienphong":  {"name": "Tiền Phong", "index": "https://tienphong.vn/sitemaps.xml",           "delay": 0.8},
    "vneconomy":  {"name": "VnEconomy",  "index": "https://vneconomy.vn/sitemap.xml",            "delay": 0.8},
    "nhandan":    {"name": "Nhân Dân",   "index": "https://nhandan.vn/sitemap.xml",              "delay": 0.8},
    "sggp":       {"name": "Sài Gòn Giải Phóng", "index": "https://www.sggp.org.vn/sitemaps.xml", "delay": 0.8},
}

_session = threading.local()
_host_lock = {}
_host_last = {}
_global_lock = threading.Lock()


def _sess():
    if not hasattr(_session, "s"):
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "vi,en;q=0.5"})
        _session.s = s
    return _session.s


def polite_get(url, delay=0.8, timeout=45, retries=3):
    """GET có giới hạn tốc độ theo host; trả về Response hoặc None. Không vượt cơ chế chặn truy cập."""
    host = urlsplit(url).netloc
    with _global_lock:
        lock = _host_lock.setdefault(host, threading.Lock())
    for attempt in range(retries):
        with lock:
            wait = _host_last.get(host, 0) + delay - time.time()
            if wait > 0:
                time.sleep(wait)
            _host_last[host] = time.time()
        try:
            r = _sess().get(url, timeout=timeout)
            if r.status_code == 200:
                r.encoding = "utf-8"
                return r
            if r.status_code in (403, 404, 410):
                return r
            if r.status_code == 429:
                time.sleep(30 * (attempt + 1))
        except requests.RequestException:
            pass
        time.sleep(3 * (attempt + 1))
    return None


def strip_accents(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def norm_text(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "")).strip()


def normalize_url(u):
    p = urlsplit(u.strip())
    host = p.netloc.lower().removeprefix("www.").removeprefix("m.")
    return urlunsplit(("https", host, p.path.rstrip("/"), "", ""))
