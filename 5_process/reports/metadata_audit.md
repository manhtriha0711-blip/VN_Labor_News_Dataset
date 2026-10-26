# Báo cáo chuẩn hóa metadata - trước/sau (Người 2)

**Module:** `5_process/src/03_clean_metadata.py` · **Đầu vào:** `1_du_lieu_chinh\vn_labor_news_dataset.csv` (chỉ đọc) · **Phạm vi ngày:** 2022-01-01 → 2026-10-23

> Báo cáo sinh tự động từ lần chạy thực tế; số liệu dưới đây tái lập được bằng cách chạy lại module.

## 0. Trạng thái issue và review

| # | Vấn đề | Quy mô | Người xử lý | Bước tiếp theo |
|---|---|---|---|---|
| 1 | ISS-002: `word_count` khác đếm lại `content` | 11.953 / 12.784 dòng | Đã giải quyết bằng đối chiếu mã Collecting; giữ nguyên `word_count` raw | Xem mục 7; `word_count_recount` chỉ mô tả `content` cuối |
| 2 | Audit cặp nghi trùng | 71 dòng review, 62 cụm theo kết quả audit | Hoàn tất phạm vi audit; không áp dụng đề xuất AI thành quyết định | Xem mục 6b; không bài nào bị loại |
| 3 | Ngoại lai độ dài (bài dài >5000 từ, ngắn <100 từ; tiêu đề dài >200 ký tự) | 9 lượt đánh cờ; chưa có kết luận người review | Đã hoàn tất cờ audit; không sửa/xóa bài | Chỉ cần reviewer thật nếu sau này nhóm muốn áp dụng quyết định loại/giữ |
| 4 | Ký tự vô hình trong `content` raw | 67 bài | Người 3 đã chạy text-clean output riêng | `content_clean` đã được đối chiếu; raw `content` không đổi |

## 1. Bảo toàn raw và số dòng

| Kiểm tra | Kết quả |
|---|---|
| Số dòng vào / ra | 12.784 / 12.784 |
| SHA-256 raw trước | `9ed13a4758ba6aecb2c6673c9d107f19739a25b1bea364bfa86bd33b23581c96` |
| SHA-256 raw sau | `9ed13a4758ba6aecb2c6673c9d107f19739a25b1bea364bfa86bd33b23581c96` |
| Raw bất biến, không mất dòng | **ĐẠT** |

## 2. Kiểu dữ liệu và giá trị thiếu

| Trường | Trước | Sau |
|---|---|---|
| `publish_date` | text (`YYYY-MM-DD`) | datetime64[us] |
| `collection_date` | text | datetime64[us] |
| `relevance_score` | text | float64 |
| `word_count` | text | Int64 |
| `publish_year/month/quarter` | (chưa có) | Int64 (cột mới) |
| `source_url_normalized` | (chưa có) | cột mới; `source_url` gốc giữ nguyên |

| Cột | Trống trước (chuỗi rỗng) | Null sau |
|---|---|---|
| `topic_secondary` | 5.746 | 5.746 |
| `sentiment` | 12.784 | 12.784 (giữ null, không gán "neutral") |
| `location` | 0 | 0 |
| `matched_keywords` | 0 | 0 |
| `source_name` | 0 | 0 |
| `publish_date` | 0 | 0 |

## 3. Giá trị không hợp lệ (trước chuẩn hóa)

| Kiểm tra | Số dòng |
|---|---|
| `publish_date` không parse được | 0 |
| `publish_date` ngoài phạm vi dự án | 0 |
| `collection_date` không parse được | 0 |
| `collection_date` sớm hơn `publish_date` | 0 |
| `source_url` sai cú pháp | 0 |
| `source_name` không thuộc 8 nguồn chuẩn | 0 |
| `topic_primary` không thuộc A-L | 0 |
| `relevance_score` không phải số | 0 |
| `word_count` không phải số nguyên | 0 |

URL có yếu tố cần chuẩn hóa để so sánh: fragment `#` 0, query `?` 0, '/' cuối 0, `http://` 0, `www.` 1.722.

Khoảng trắng/Unicode cần sửa (số dòng): `title` 14, `location` 0, `matched_keywords` 0, `topic_primary` 0, `topic_secondary` 0, `data_quality_note` 0, `relevance_status` 0.

## 4. Thay đổi giá trị đã áp dụng (chi tiết: `logs/metadata_change_log.csv`)

| Trường / quy tắc | Số thay đổi |
|---|---|
| `title` / NFC+whitespace | 14 |

## 5. Vấn đề đánh cờ, không tự sửa (chi tiết: `logs/metadata_issues.csv`)

| Mã | Số lượt |
|---|---|
| `OUTLIER_CONTENT_SHORT` | 4 |
| `OUTLIER_CONTENT_LONG` | 3 |
| `OUTLIER_TITLE_LONG` | 2 |

Số dòng có ít nhất một cờ: **9**.

## 6. Audit trùng lặp (chi tiết: `data/interim/duplicate_review.csv`)

Chỉ audit, **không loại bản ghi nào**. Gồm khớp chính xác theo khóa đã chuẩn hóa và cặp gần trùng nội dung (cosine TF-IDF từ+bigram, ngưỡng mặc định 0,85; chạy `--near-threshold` để đổi).

| Loại khóa | Số nhóm trùng | Số bài trong các nhóm |
|---|---|---|
| `near_content_tfidf` | 70 | 140 |
| `title_key` | 1 | 2 |

Hợp nhất các nhóm (union-find) thành **62** cụm `dup_cluster_id`, gồm **129** bài. Đây là kết quả audit, không phải quyết định xác nhận trùng. Cần đối chiếu với `split_validation.md` và rà soát mọi cụm giao split trước khi chốt đánh giá.

## 6b. Trạng thái quyết định review

Quyết định đã được xác nhận (nếu có) nằm ở `config/duplicate_decisions.csv` và `config/outlier_review.csv`; module đọc lại hai file này mỗi lần chạy nên kết quả tái lập được. Không nạp các file trong `config/review_drafts/` vào xử lý. Mọi quyết định có nguồn ghi là bản nháp AI phải được Người 2 xác nhận trước khi chuyển vào cấu hình chính. Không bài nào bị xóa.

**Cặp nghi trùng:** có quyết định được nạp cho 0 / 71 dòng (còn 71 dòng chưa có quyết định).

| Quyết định | Số dòng | Ý nghĩa |
|---|---|---|
| `KHONG_TRUNG` | 0 | Khác kỳ/giai đoạn/sự kiện, hoặc giống do khối quảng cáo; **không** gom cụm |
| `GIU_CA_HAI_CUNG_SU_KIEN` | 0 | Cùng sự kiện hoặc nguồn tin gốc, bài viết riêng; giữ cả hai, đánh dấu chung cụm; split theo thời gian có thể vẫn giao split |
| `NGHI_DANG_LAI_DE_XUAT_GIU_1` | 0 | Nội dung gần như một bản (PR/thông cáo viết lại sát); đề xuất giữ 1 bài, **chưa xóa**, chờ Người 1 chốt |

Dữ liệu dẫn xuất đã thay đổi theo quyết định: số cụm `dup_cluster_id` từ **62** (gom theo điểm tương đồng) xuống **62** (chỉ gom các cặp cùng sự kiện hoặc nghi đăng lại), số bài nằm trong cụm từ 129 xuống 129. Metadata có thêm ba cột `dup_review_decision`, `dup_proposed_action` (`KEEP`/`DROP_PROPOSED`) và `outlier_review_conclusion`.

Các cặp đề xuất giữ 1 bài (quy tắc chọn bài giữ: đăng sớm hơn, cùng ngày thì bài dài hơn):

| Dòng | Cặp bài | Đề xuất giữ | Căn cứ |
|---|---|---|---|
| (không có) | | | |

Quan sát cho các bước sau (không phải lỗi của metadata): nhiều cặp giống nhau vì hai báo cùng trích một văn bản/thông cáo; bài dạng bản tin/điểm tin/podcast có thể cần Người 4 xem về mức liên quan. Text cleaning chỉ xử lý ký tự/Unicode/khoảng trắng, không xóa boilerplate quảng cáo nếu chưa có tiêu chí kiểm tra được.

**Ngoại lai (9 lượt đánh cờ):** kết luận `chưa review` 9. Không bài nào bị loại.

| Bài | Mã | Giá trị | Kết luận | Ghi chú |
|---|---|---|---|---|
| VNLAB-001959 | `OUTLIER_CONTENT_LONG` | 13683 từ | chưa review |  |
| VNLAB-006226 | `OUTLIER_CONTENT_LONG` | 10711 từ | chưa review |  |
| VNLAB-006577 | `OUTLIER_CONTENT_LONG` | 9811 từ | chưa review |  |
| VNLAB-000473 | `OUTLIER_CONTENT_SHORT` | 87 từ | chưa review |  |
| VNLAB-000720 | `OUTLIER_CONTENT_SHORT` | 99 từ | chưa review |  |
| VNLAB-002081 | `OUTLIER_CONTENT_SHORT` | 98 từ | chưa review |  |
| VNLAB-005534 | `OUTLIER_CONTENT_SHORT` | 69 từ | chưa review |  |
| VNLAB-004910 | `OUTLIER_TITLE_LONG` | 237 ký tự | chưa review |  |
| VNLAB-011093 | `OUTLIER_TITLE_LONG` | 203 ký tự | chưa review |  |

## 7. Đối chiếu ISS-002 (`word_count`)

Đếm lại `content.split()` trên content raw (cột `word_count_recount`, chỉ để đối chiếu; `word_count` gốc giữ nguyên):

- Khác `word_count`: **11.953 / 12.784** dòng (93.5%).
- Trong số đó, đếm lại **lớn hơn** `word_count`: 11.953 dòng; trung vị chênh lệch 39 từ.
- Mã Collecting `4_ma_nguon/clean_and_export.py` tính `word_count` trên thân bài trước khi có thể ghép sapo vào `content` đầu ra; khác biệt định nghĩa đã được xác nhận và `ISS-002` đã resolved. Giữ nguyên `word_count` raw; dùng `word_count_recount` khi cần độ dài của `content` cuối.

## 8. Việc chuyển cho Người 3 (văn bản)

- 67 bài có ký tự vô hình (zero-width, ví dụ U+200B) trong `content` raw; module metadata này **không sửa `content`**. Bước Người 3 tạo `content_clean` riêng và đã được kiểm tra trên toàn bộ dữ liệu.
- 14 tiêu đề có ký tự vô hình đã được chuẩn hóa (log ở `metadata_change_log.csv`).

## 9. Giới hạn

- Các quyết định trong `config/duplicate_decisions.csv` và `config/outlier_review.csv` phải được người phụ trách xác nhận; bản nháp trong `config/review_drafts/` không được áp dụng. Gần trùng chỉ dựa trên độ tương đồng TF-IDF với một ngưỡng; có thể bỏ sót bài viết lại bằng từ ngữ khác, và có thể nêu cả bài cập nhật cùng sự kiện. Mọi cặp đều cần người xem quyết định.
- Chuẩn hóa `www.`/`http` chỉ áp dụng cho `source_url_normalized`; có thể coi hai URL khác nhau là một, nên các cặp trùng vẫn cần xem tay.
- Text cleaning chuẩn hóa ký tự/Unicode và khoảng trắng; không áp dụng quy tắc xóa boilerplate quảng cáo nếu chưa có tiêu chí kiểm tra được.
