"""Giai đoạn 4-6: kiểm tra hợp lệ, lọc liên quan, gán chủ đề/địa phương, khử trùng lặp, xuất CSV/XLSX + báo cáo.

Đầu ra (thư mục output/):
  vn_labor_news_dataset.csv / .xlsx  - mẫu hợp lệ (relevance_status = relevant_auto)
  borderline_for_review.csv          - bài ranh giới, cần người kiểm tra, KHÔNG tính vào số mẫu hợp lệ
  rejected_log.csv                   - bài bị loại kèm lý do
  qa_random_sample.csv               - mẫu ngẫu nhiên để kiểm tra thủ công
  stats.json, data_quality_report.md
"""
import json
import random
import re
from collections import Counter, defaultdict
from datetime import date

import pandas as pd

from common import DATE_FROM, OUT_DIR, RAW_DIR, SOURCES, URLS_DIR, norm_text, normalize_url, strip_accents
from keywords import TOPICS, assess

TODAY = date.today().isoformat()

# 63 tỉnh/thành (trước 1/7/2025); 34 đơn vị sau sáp nhập đều nằm trong danh sách tên này
PROVINCES = [
    "Hà Nội", "TP.HCM", "Hải Phòng", "Đà Nẵng", "Cần Thơ", "Huế", "An Giang", "Bà Rịa - Vũng Tàu", "Bắc Giang",
    "Bắc Kạn", "Bạc Liêu", "Bắc Ninh", "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước", "Bình Thuận", "Cà Mau",
    "Cao Bằng", "Đắk Lắk", "Đắk Nông", "Điện Biên", "Đồng Nai", "Đồng Tháp", "Gia Lai", "Hà Giang", "Hà Nam",
    "Hà Tĩnh", "Hải Dương", "Hậu Giang", "Hòa Bình", "Hưng Yên", "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu",
    "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định", "Nghệ An", "Ninh Bình", "Ninh Thuận", "Phú Thọ",
    "Phú Yên", "Quảng Bình", "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", "Sóc Trăng", "Sơn La", "Tây Ninh",
    "Thái Bình", "Thái Nguyên", "Thanh Hóa", "Tiền Giang", "Trà Vinh", "Tuyên Quang", "Vĩnh Long", "Vĩnh Phúc",
    "Yên Bái",
]
PROV_ALIASES = {
    "TP.HCM": [r"TP\.? ?HCM", r"TP\. Hồ Chí Minh", r"thành phố Hồ Chí Minh", r"Sài Gòn"],
    "Huế": [r"Thừa Thiên[ -]Huế", r"TP\.? Huế", r"thành phố Huế"],
    "Bà Rịa - Vũng Tàu": [r"Bà Rịa[ -–]+Vũng Tàu", r"BR-VT", r"Vũng Tàu"],
    "Thanh Hóa": [r"Thanh Hoá"], "Khánh Hòa": [r"Khánh Hoà"], "Hòa Bình": [r"Hoà Bình"],
    "Đắk Lắk": [r"Đăk Lăk", r"Đắc Lắc"], "Đắk Nông": [r"Đăk Nông"],
}
PROV_RE = {p: re.compile(r"(?<![\wÀ-ỹ])(?:" + "|".join([re.escape(p)] + PROV_ALIASES.get(p, [])) + r")(?![\wÀ-ỹ])")
           for p in PROVINCES}
# "Hòa Bình"/"Bình Định"... có thể trùng tên riêng; chấp nhận sai số nhỏ, ghi chú trong báo cáo

ALLEGATION_TERMS = ["nợ lương", "chậm lương", "trốn đóng", "chậm đóng", "nợ đóng", "sa thải trái", "vi phạm",
                    "bóc lột", "cưỡng bức", "lừa đảo", "khởi tố", "xử phạt"]


def detect_location(title, sapo, content):
    head = f"{title} {sapo}"
    scores = Counter()
    for p, rx in PROV_RE.items():
        h = len(rx.findall(head))
        c = len(rx.findall(content))
        if h or c:
            scores[p] = 3 * h + c
    if not scores:
        return "Toàn quốc/không xác định"
    top = [p for p, s in scores.most_common(3) if s >= 2]
    return "; ".join(top) if top else "Toàn quốc/không xác định"


def norm_title(t):
    return re.sub(r"[^a-z0-9 ]", "", strip_accents(t).lower()).strip()


def shingles(text, k=5):
    w = re.findall(r"\w+", text.lower())
    return {hash(" ".join(w[i:i + k])) for i in range(max(len(w) - k + 1, 1))}


def bottom_k(sh, k=8):
    """Phác thảo bottom-k (họ MinHash): hai văn bản Jaccard cao gần như chắc chắn chung ít nhất 1 giá trị."""
    return sorted(sh)[:k]


def main():
    stats = {"generated_at": TODAY, "per_source": {}}
    # ---- Số URL phát hiện được từ sitemap
    for src in SOURCES:
        p = URLS_DIR / f"{src}.jsonl"
        n_all = n_cand = 0
        if p.exists():
            for l in open(p, encoding="utf-8"):
                n_all += 1
                n_cand += '"candidate": true' in l
        stats["per_source"][src] = {"sitemap_urls_2022_now": n_all, "slug_candidates": n_cand}

    # ---- Bản ghi đã tải
    recs = []
    for src in SOURCES:
        p = RAW_DIR / f"{src}.jsonl"
        if p.exists():
            for l in open(p, encoding="utf-8"):
                try:
                    recs.append(json.loads(l))
                except json.JSONDecodeError:  # dòng đang ghi dở khi chạy song song với fetch
                    pass
    by_url = {}
    for r in recs:  # khử trùng theo URL chuẩn hóa (giữ bản tải sau cùng)
        by_url[normalize_url(r.get("final_url") or r["url"])] = r
    stats["fetch_attempts"] = len(recs)
    stats["unique_urls_attempted"] = len(by_url)

    accepted, borderline, rejected = [], [], []
    for nu, r in by_url.items():
        src = r["source"]
        ps = stats["per_source"][src]
        ps["attempted"] = ps.get("attempted", 0) + 1

        def reject(reason):
            rejected.append({"source": src, "url": r["url"], "title": r.get("title", ""),
                             "publish_date": r.get("publish_date", ""), "reason": reason})
            ps.setdefault("rejected", Counter())[reason.split(" (")[0]] += 1

        if r.get("http_status") != 200 or r.get("error"):
            reject(f"không tải được ({r.get('error') or r.get('http_status')})"); continue
        ps["downloaded"] = ps.get("downloaded", 0) + 1
        title, sapo, content = r.get("title", ""), r.get("sapo", ""), r.get("content", "")
        if not title:
            reject("thiếu tiêu đề"); continue
        if not r.get("publish_date"):
            reject("thiếu ngày xuất bản"); continue
        if not (DATE_FROM <= r["publish_date"] <= TODAY):
            reject("ngoài khoảng thời gian"); continue
        if r.get("content_fallback") and "Tổng Biên tập" in content:
            reject("không trích xuất được thân bài"); continue
        if len(content) < 300:
            reject("nội dung quá ngắn/không truy cập được toàn văn"); continue
        a = assess(title, sapo, content, nu)
        if a["status"] == "excluded":
            reject("không liên quan: " + a["reason"]); continue
        notes = []
        if len(content) < 800:
            notes.append("nội dung ngắn (<800 ký tự)")
        if r.get("content_fallback"):
            notes.append("trích xuất thân bài bằng phương án dự phòng")
        low = (title + " " + content).lower()
        if any(t in low for t in ALLEGATION_TERMS):
            notes.append("có nội dung phản ánh/cáo buộc vi phạm - không phải kết luận vi phạm của dữ liệu")
        notes.append("chủ đề & từ khóa gán tự động theo luật")
        row = {
            "title": title, "content": (sapo + "\n" + content) if sapo and sapo[:60] not in content else content,
            "publish_date": r["publish_date"], "source_name": SOURCES[src]["name"], "source_url": r["url"],
            "topic_primary": f"{a['topic_primary']} - {TOPICS[a['topic_primary']][0]}" if a["topic_primary"] else "",
            "topic_secondary": "; ".join(f"{c} - {TOPICS[c][0]}" for c in a["topic_secondary"]),
            "matched_keywords": "; ".join(a["matched_keywords"]),
            "location": detect_location(title, sapo, content), "sentiment": "",
            "relevance_status": "relevant_auto" if a["status"] == "relevant" else "borderline_auto",
            "collection_date": r.get("fetched_at", TODAY), "data_quality_note": "; ".join(notes),
            "source_key": src, "relevance_score": a["score"], "relevance_reason": a["reason"],
            "word_count": len(content.split()),
        }
        (accepted if a["status"] == "relevant" else borderline).append(row)

    # ---- Khử trùng lặp: tiêu đề chuẩn hóa + nội dung gần giống (SimHash + Jaccard)
    pool = accepted + borderline
    before = len(pool)
    pool.sort(key=lambda x: (x["relevance_status"] != "relevant_auto", -x["word_count"]))  # ưu tiên bản đầy đủ hơn
    keep, dup_log, seen_title = [], [], {}
    sh_cache, buckets = {}, defaultdict(list)
    for row in pool:
        nt = norm_title(row["title"])
        if len(nt) > 25 and nt in seen_title:
            dup_log.append((row["source_url"], seen_title[nt], "trùng tiêu đề")); continue
        sh = shingles(row["content"])
        keys = bottom_k(sh)
        dup_of = None
        for j in {j for key in keys for j in buckets[key]}:
            o = sh_cache[j]
            if len(sh & o) / max(len(sh | o), 1) >= 0.7:
                dup_of = keep[j]["source_url"]; break
        if dup_of:
            dup_log.append((row["source_url"], dup_of, "nội dung gần giống")); continue
        idx = len(keep)
        keep.append(row)
        sh_cache[idx] = sh
        for key in keys:
            buckets[key].append(idx)
        if len(nt) > 25:
            seen_title[nt] = row["source_url"]
    stats["dedup"] = {"before": before, "after": len(keep), "removed": before - len(keep),
                      "removed_by_title": sum(d[2] == "trùng tiêu đề" for d in dup_log),
                      "removed_by_content": sum(d[2] == "nội dung gần giống" for d in dup_log)}

    cols = ["article_id", "title", "content", "publish_date", "source_name", "source_url", "topic_primary",
            "topic_secondary", "matched_keywords", "location", "sentiment", "relevance_status", "collection_date",
            "data_quality_note", "relevance_score", "word_count"]
    df = pd.DataFrame(keep).sort_values(["publish_date", "source_key"]).reset_index(drop=True)
    valid = df[df.relevance_status == "relevant_auto"].copy().reset_index(drop=True)
    border = df[df.relevance_status == "borderline_auto"].copy().reset_index(drop=True)
    valid["article_id"] = [f"VNLAB-{i:06d}" for i in range(1, len(valid) + 1)]
    border["article_id"] = [f"VNLAB-B{i:05d}" for i in range(1, len(border) + 1)]

    valid[cols].to_csv(OUT_DIR / "vn_labor_news_dataset.csv", index=False, encoding="utf-8-sig")
    border[cols].to_csv(OUT_DIR / "borderline_for_review.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(rejected).to_csv(OUT_DIR / "rejected_log.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(dup_log, columns=["removed_url", "kept_url", "reason"]).to_csv(
        OUT_DIR / "duplicates_log.csv", index=False, encoding="utf-8-sig")
    x = valid[cols].copy()
    long_mask = x.content.str.len() > 32000
    x.loc[long_mask, "content"] = x.loc[long_mask, "content"].str[:32000]
    x.loc[long_mask, "data_quality_note"] += "; XLSX: nội dung cắt ở 32.000 ký tự (giới hạn ô Excel) - xem CSV"
    x.to_excel(OUT_DIR / "vn_labor_news_dataset.xlsx", index=False)
    valid.sample(min(100, len(valid)), random_state=7)[["article_id", "title", "publish_date", "source_name",
                                                       "source_url", "topic_primary", "relevance_reason"]] \
        .to_csv(OUT_DIR / "qa_random_sample.csv", index=False, encoding="utf-8-sig")

    # ---- Thống kê
    for src, ps in stats["per_source"].items():
        ps["valid"] = int((valid.source_key == src).sum())
        ps["borderline"] = int((border.source_key == src).sum())
        if "rejected" in ps:
            ps["rejected"] = dict(ps["rejected"])
    stats["valid_total"] = len(valid)
    stats["borderline_total"] = len(border)
    stats["rejected_total"] = len(rejected)
    stats["by_year"] = valid.publish_date.str[:4].value_counts().sort_index().to_dict()
    stats["by_source_year"] = pd.crosstab(valid.source_name, valid.publish_date.str[:4]).to_dict(orient="index")
    stats["by_topic"] = valid.topic_primary.value_counts().to_dict()
    stats["by_location_top20"] = valid.location.str.split("; ").explode().value_counts().head(20).to_dict()
    req = ["title", "content", "publish_date", "source_name", "source_url", "topic_primary"]
    stats["missing_rate"] = {c: round(float((valid[c].fillna("") == "").mean()), 4)
                             for c in cols if c in valid}
    stats["required_fields_complete"] = bool(all(stats["missing_rate"][c] == 0 for c in req))
    stats["content_chars"] = valid.content.str.len().describe().round(0).to_dict()
    json.dump(stats, open(OUT_DIR / "stats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=int)
    write_report(stats, valid, border, rejected)
    print(json.dumps({k: stats[k] for k in ("valid_total", "borderline_total", "rejected_total", "dedup",
                                             "by_year", "by_topic")}, ensure_ascii=False, indent=1, default=int))
    for s, ps in stats["per_source"].items():
        print(s, {k: v for k, v in ps.items() if k != "rejected"})


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def write_report(stats, valid, border, rejected):
    ps = stats["per_source"]
    total = lambda k: sum(v.get(k, 0) for v in ps.values())
    L = [f"# Báo cáo chất lượng dữ liệu – Tin tức lao động Việt Nam", "",
         f"Ngày tạo báo cáo: {stats['generated_at']} · Khoảng thời gian: {DATE_FROM} → {stats['generated_at']}", "",
         "## 1. Phễu dữ liệu (phát hiện → tải → hợp lệ)", "",
         md_table(["Giai đoạn", "Số lượng"], [
             ["URL bài viết 2022–nay phát hiện từ sitemap (8 nguồn)", f"{total('sitemap_urls_2022_now'):,}"],
             ["URL ứng viên theo slug (lọc từ khóa)", f"{total('slug_candidates'):,}"],
             ["URL đã gửi yêu cầu tải (duy nhất)", f"{stats['unique_urls_attempted']:,}"],
             ["Tải thành công (HTTP 200, phân tích được)", f"{total('downloaded'):,}"],
             ["Bị loại (thiếu dữ liệu / ngoài thời gian / không liên quan)", f"{stats['rejected_total']:,}"],
             ["Qua lọc trước khử trùng lặp (hợp lệ + ranh giới)", f"{stats['dedup']['before']:,}"],
             ["Bị loại do trùng lặp", f"{stats['dedup']['removed']:,}"],
             ["**Mẫu hợp lệ (relevant_auto)**", f"**{stats['valid_total']:,}**"],
             ["Mẫu ranh giới cần kiểm tra tay (không tính)", f"{stats['borderline_total']:,}"]]), "",
         "## 2. Theo nguồn", "",
         md_table(["Nguồn", "URL sitemap", "Ứng viên", "Đã tải", "Hợp lệ", "Ranh giới", "Tỷ lệ hợp lệ/đã tải",
                   "% bộ dữ liệu"],
                  [[SOURCES[s]["name"], f"{v['sitemap_urls_2022_now']:,}", f"{v['slug_candidates']:,}",
                    f"{v.get('downloaded', 0):,}", f"{v['valid']:,}", v["borderline"],
                    f"{v['valid'] / max(v.get('downloaded', 0), 1):.0%}",
                    f"{v['valid'] / max(stats['valid_total'], 1):.1%}"] for s, v in ps.items()]), "",
         "## 3. Theo năm", "",
         md_table(["Năm", "Số bài"], [[y, f"{n:,}"] for y, n in stats["by_year"].items()]), "",
         "### Nguồn × năm", ""]
    years = sorted(stats["by_year"])
    L += [md_table(["Nguồn"] + years, [[s] + [d.get(y, 0) for y in years]
                                        for s, d in stats["by_source_year"].items()]), ""]
    L += ["## 4. Theo nhóm chủ đề chính", "",
          md_table(["Chủ đề", "Số bài", "Tỷ lệ"], [[t, f"{n:,}", f"{n / max(stats['valid_total'], 1):.1%}"]
                                                 for t, n in stats["by_topic"].items()]), "",
          "## 5. Địa phương được nhắc nhiều nhất (top 20)", "",
          md_table(["Địa phương", "Số bài"], [[k, v] for k, v in stats["by_location_top20"].items()]), "",
          "## 6. Chất lượng", "",
          f"- Tỷ lệ trùng lặp (trên tập qua lọc): {stats['dedup']['removed'] / max(stats['dedup']['before'], 1):.2%} "
          f"({stats['dedup']['removed_by_title']} trùng tiêu đề, {stats['dedup']['removed_by_content']} nội dung gần giống)",
          f"- Trường bắt buộc đầy đủ 100%: {'Có' if stats['required_fields_complete'] else 'KHÔNG'}",
          "- Tỷ lệ thiếu theo cột (mẫu hợp lệ):", "",
          md_table(["Cột", "Tỷ lệ trống", "Ghi chú"],
                   [[c, f"{r:.1%}", "cố ý để trống – chưa phân tích cảm xúc" if c == "sentiment" else
                     ("không phải bài nào cũng có chủ đề phụ" if c == "topic_secondary" else "")]
                    for c, r in stats["missing_rate"].items()]), "",
          f"- Độ dài nội dung (ký tự): trung vị {stats['content_chars'].get('50%', 0):,.0f}, "
          f"nhỏ nhất {stats['content_chars'].get('min', 0):,.0f}, lớn nhất {stats['content_chars'].get('max', 0):,.0f}", "",
          "### Lý do loại bỏ", ""]
    rc = Counter(r["reason"].split(" (")[0] for r in rejected)
    L += [md_table(["Lý do", "Số bài"], rc.most_common()), ""]
    (OUT_DIR / "data_quality_report.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
