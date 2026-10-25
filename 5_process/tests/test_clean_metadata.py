"""Unit test cho 03_clean_metadata.py (Người 2). Chạy: python -m unittest 5_process/tests/test_clean_metadata.py"""
import importlib.util
import sys
import unittest
from pathlib import Path

import pandas as pd

SRC = Path(__file__).resolve().parents[1] / "src" / "03_clean_metadata.py"
spec = importlib.util.spec_from_file_location("clean_metadata", SRC)
cm = importlib.util.module_from_spec(spec)
sys.modules["clean_metadata"] = cm
spec.loader.exec_module(cm)


class TestNormalize(unittest.TestCase):
    def test_text_keeps_vietnamese_marks(self):
        s = "  Lương  tối   thiểu\u200b vùng – Đà Nẵng \u00a0"
        self.assertEqual(cm.normalize_text(s), "Lương tối thiểu vùng – Đà Nẵng")

    def test_text_nfc(self):
        decomposed = "Nguye\u0302\u0303n"  # e + ^ + ~ (NFD)
        self.assertEqual(cm.normalize_text(decomposed), "Nguyễn")

    def test_text_does_not_change_numbers_or_negation(self):
        s = "Không tăng lương 7,5% từ 1/7/2026"
        self.assertEqual(cm.normalize_text(s), s)

    def test_source_aliases(self):
        for raw, want in [("Tuoi Tre", "Tuổi Trẻ"), ("tuổi trẻ online", "Tuổi Trẻ"), ("SGGP", "Sài Gòn Giải Phóng"),
                          ("vneconomy.vn", "VnEconomy"), ("Báo Dân trí", "Dân Trí"), ("Nhân Dân", "Nhân Dân")]:
            self.assertEqual(cm.normalize_source(raw), want, raw)
        self.assertIsNone(cm.normalize_source("Báo lạ"))

    def test_url(self):
        n = cm.normalize_url
        self.assertEqual(n("http://WWW.Tuoitre.vn/a-b-123.htm/?utm_source=x&id=2#frag"),
                         "https://tuoitre.vn/a-b-123.htm?id=2")
        self.assertEqual(n("https://tuoitre.vn/a-b-123.htm"), n("https://www.tuoitre.vn/a-b-123.htm/"))
        self.assertEqual(n("not a url"), "")
        self.assertEqual(n("ftp://x.vn/a"), "")
        self.assertEqual(n(""), "")

    def test_title_key_keeps_diacritics(self):
        self.assertEqual(cm.title_key("Bữa cơm công đoàn - ấm lòng!"), cm.title_key("Bữa cơm công đoàn ấm lòng"))
        self.assertNotEqual(cm.title_key("Lương"), cm.title_key("Luong"))

    def test_topic(self):
        self.assertEqual(cm.parse_topic("C - Tiền lương, bảo hiểm, quyền lợi"), ("C", True))
        self.assertEqual(cm.parse_topic("C - nhãn lạ"), ("C", False))
        self.assertEqual(cm.parse_topic("Z - x"), (None, False))


def _row(i, **kw):
    r = dict(article_id=f"VNLAB-{i:06d}", title=f"Tiêu đề {i}", content=" ".join(f"tu{i}x{k}" for k in range(30)),
             publish_date="2024-03-05", source_name="Tuổi Trẻ", source_url=f"https://tuoitre.vn/bai-{i}.htm",
             topic_primary="C - Tiền lương, bảo hiểm, quyền lợi", topic_secondary="", matched_keywords="lương",
             location="Hà Nội", sentiment="", relevance_status="relevant_auto", collection_date="2026-10-23",
             data_quality_note="x", relevance_score="12.0", word_count="10")
    r.update(kw)
    return r


class TestPipeline(unittest.TestCase):
    def run_clean(self, rows):
        raw = pd.DataFrame(rows, dtype=str)
        return raw, *cm.clean(raw)

    def test_row_count_and_raw_untouched(self):
        raw, m, ch, iss, dup = self.run_clean([_row(1), _row(2)])
        snap = raw.copy()
        cm.clean(raw)
        pd.testing.assert_frame_equal(raw, snap)
        self.assertEqual(len(m), 2)

    def test_sentiment_stays_null_not_neutral(self):
        _, m, *_ = self.run_clean([_row(1)])
        self.assertTrue(m["sentiment"].isna().all())
        self.assertTrue(m["topic_secondary"].isna().all())

    def test_dates_and_flags(self):
        rows = [_row(1), _row(2, publish_date="2019-01-01"), _row(3, publish_date="05/03/2024"),
                _row(4, collection_date="2024-01-01")]
        _, m, _, iss, _ = self.run_clean(rows)
        codes = set(iss["issue_code"])
        self.assertIn("DATE_OUT_OF_RANGE", codes)
        self.assertIn("DATE_UNPARSABLE", codes)
        self.assertIn("COLLECTED_BEFORE_PUBLISHED", codes)
        self.assertEqual(int(m.loc[0, "publish_quarter"]), 1)
        self.assertTrue(pd.isna(m.loc[2, "publish_date"]))
        self.assertEqual(len(m), 4)  # không loại dòng nào

    def test_source_domain_mismatch_flagged_not_fixed(self):
        _, m, _, iss, _ = self.run_clean([_row(1, source_name="Thanh Niên")])
        self.assertIn("SRC_DOMAIN_MISMATCH", set(iss["issue_code"]))
        self.assertEqual(m.loc[0, "source_name"], "Thanh Niên")

    def test_original_url_preserved(self):
        u = "http://www.tuoitre.vn/bai-1.htm/#x"
        _, m, *_ = self.run_clean([_row(1, source_url=u)])
        self.assertEqual(m.loc[0, "source_url"], u)
        self.assertEqual(m.loc[0, "source_url_normalized"], "https://tuoitre.vn/bai-1.htm")

    def test_duplicates_flagged_and_clustered_not_removed(self):
        rows = [_row(1), _row(2, source_url="https://www.tuoitre.vn/bai-1.htm/"),  # trùng URL chuẩn hóa
                _row(3, title="Tiêu đề 3"), _row(4, title="tiêu đề 3!"),            # trùng title_key
                _row(5)]
        _, m, _, _, dup = self.run_clean(rows)
        self.assertEqual(len(m), 5)
        self.assertEqual(m.loc[0, "dup_cluster_id"], m.loc[1, "dup_cluster_id"])
        self.assertEqual(m.loc[2, "dup_cluster_id"], m.loc[3, "dup_cluster_id"])
        self.assertNotEqual(m.loc[0, "dup_cluster_id"], m.loc[2, "dup_cluster_id"])
        self.assertIn("url_normalized", set(dup["dup_type"]))

    def test_near_duplicate_content_flagged(self):
        base = " ".join(f"tu{k}" for k in range(60))
        rows = [_row(1, content=base + " abc"), _row(2, content=base + " xyz"), _row(3)]
        _, m, _, _, dup = self.run_clean(rows)
        self.assertIn("near_content_tfidf", set(dup["dup_type"]))
        self.assertEqual(m.loc[0, "dup_cluster_id"], m.loc[1, "dup_cluster_id"])
        self.assertTrue(pd.isna(m.loc[2, "dup_cluster_id"]))
        self.assertEqual(len(m), 3)

    def test_outliers_flagged_not_changed(self):
        long_c = " ".join(f"w{k}" for k in range(5200))
        _, m, _, iss, _ = self.run_clean([_row(1, content=long_c), _row(2, title="x" * 220), _row(3, content="ngắn quá")])
        codes = set(iss["issue_code"])
        self.assertTrue({"OUTLIER_CONTENT_LONG", "OUTLIER_TITLE_LONG", "OUTLIER_CONTENT_SHORT"} <= codes)
        self.assertEqual(len(m), 3)
        self.assertEqual(m.loc[1, "title"], "x" * 220)  # không sửa tiêu đề

    def test_duplicate_article_id_reported(self):
        _, m, _, _, dup = self.run_clean([_row(1), _row(1, source_url="https://tuoitre.vn/khac.htm", title="Khác")])
        self.assertIn("article_id", set(dup["dup_type"]))
        self.assertEqual(len(m), 2)

    def test_word_count_original_kept_and_recount_added(self):
        _, m, *_ = self.run_clean([_row(1, content="một hai ba bốn", word_count="3")])
        self.assertEqual(int(m.loc[0, "word_count"]), 3)
        self.assertEqual(int(m.loc[0, "word_count_recount"]), 4)

    def test_invalid_topic_flagged(self):
        _, _, _, iss, _ = self.run_clean([_row(1, topic_primary="Z - lạ")])
        self.assertIn("TOPIC_INVALID", set(iss["issue_code"]))


if __name__ == "__main__":
    unittest.main()
