"""Kiểm chứng: tải lại URL mẫu, so tiêu đề hiện tại với tiêu đề đã lưu, phát hiện chuyển hướng.

Dùng: python scripts/verify_urls.py <file.csv> <n> [seed]
"""
import sys

import pandas as pd
from bs4 import BeautifulSoup

from common import norm_text, polite_get

path, n = sys.argv[1], int(sys.argv[2])
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
df = pd.read_csv(path)
url_col = "source_url" if "source_url" in df else "url"
ok = 0
for _, r in df.sample(min(n, len(df)), random_state=seed).iterrows():
    resp = polite_get(r[url_col], delay=0.5)
    if resp is None:
        print("NO-RESPONSE |", r[url_col]); continue
    soup = BeautifulSoup(resp.text, "lxml")
    h1 = soup.find("h1")
    live = norm_text(h1.get_text(" ")) if h1 else norm_text(soup.title.get_text() if soup.title else "")
    same = norm_text(str(r["title"]))[:40].lower() in live.lower() or live.lower()[:40] in norm_text(str(r["title"])).lower()
    redirected = resp.url.rstrip("/") != r[url_col].rstrip("/")
    ok += resp.status_code == 200 and same
    print(f"{resp.status_code} | {'KHỚP' if same else 'KHÁC'} | {'REDIRECT->' + resp.url if redirected else ''}")
    print(f"     url : {r[url_col]}")
    print(f"     lưu : {str(r['title'])[:90]}")
    print(f"     live: {live[:90]}")
print(f"\n=> {ok}/{min(n, len(df))} URL tồn tại và đúng tiêu đề")
