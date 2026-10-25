# Báo cáo chuẩn hóa metadata - trước/sau (Người 2)

**Module:** `5_process/src/03_clean_metadata.py` · **Đầu vào:** `1_du_lieu_chinh\vn_labor_news_dataset.csv` (chỉ đọc) · **Phạm vi ngày:** 2022-01-01 → 2026-10-23

> Báo cáo sinh tự động từ lần chạy thực tế; số liệu dưới đây tái lập được bằng cách chạy lại module.

## 0. Vấn đề còn mở (cần người quyết định)

| # | Vấn đề | Quy mô | Người xử lý | Bước tiếp theo |
|---|---|---|---|---|
| 1 | ISS-002: `word_count` khác đếm lại `content` | 11.953 / 12.784 dòng | Người 1 xác nhận | Đối chiếu cách đếm trong mã Collecting rồi chốt dùng cột nào |
| 2 | Cặp/nhóm nghi trùng chờ quyết định giữ/loại | 71 dòng review, 62 cụm | Người 2 + Người 1 | Điền quyết định cho từng dòng `duplicate_review.csv`; chưa loại bài nào |
| 3 | Ngoại lai độ dài (bài dài >5000 từ, ngắn <100 từ; tiêu đề dài >200 ký tự) | 9 lượt đánh cờ | Người 2 xem tay, Người 5 cân nhắc khi thống kê | Xem `metadata_issues.csv` (mã `OUTLIER_*`) |
| 4 | Ký tự vô hình trong `content` | 67 bài | Người 3 | Xử lý trong bước làm sạch văn bản |

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

Hợp nhất các nhóm (union-find) thành **62** cụm `dup_cluster_id`, gồm **129** bài. Người 5 dùng cột này để giữ các bài cùng cụm trong cùng một tập khi chia train/validation/test (tránh rò rỉ).

## 7. Đối chiếu ISS-002 (`word_count`)

Đếm lại `content.split()` trên content raw (cột `word_count_recount`, chỉ để đối chiếu; `word_count` gốc giữ nguyên):

- Khác `word_count`: **11.953 / 12.784** dòng (93.5%).
- Trong số đó, đếm lại **lớn hơn** `word_count`: 11.953 dòng; trung vị chênh lệch 39 từ.
- Mã Collecting xác nhận `word_count` được tính bằng `len(content.split())` trên phần thân bài trích xuất trước khi tạo trường cuối cùng; trường `content` xuất ra có thể ghép thêm sapo. Vì vậy đây là khác biệt định nghĩa giữa hai trường, không phải căn cứ để sửa `word_count` gốc. Giữ nguyên cột gốc và dùng `word_count_recount` khi cần độ dài theo `content` cuối.

## 8. Việc chuyển cho Người 3 (văn bản)

- 67 bài có ký tự vô hình (zero-width, ví dụ U+200B) trong `content`; module này **không sửa `content`**.
- 14 tiêu đề có ký tự vô hình đã được chuẩn hóa (log ở `metadata_change_log.csv`).

## 9. Giới hạn

- Gần trùng chỉ dựa trên độ tương đồng TF-IDF với một ngưỡng; có thể bỏ sót bài viết lại bằng từ ngữ khác, và có thể nêu cả bài cập nhật cùng sự kiện. Mọi cặp đều cần người xem quyết định.
- Chuẩn hóa `www.`/`http` chỉ áp dụng cho `source_url_normalized`; có thể coi hai URL khác nhau là một, nên các cặp trùng vẫn cần xem tay.
- Tiêu đề chỉ chuẩn hóa Unicode/khoảng trắng; làm sạch sâu văn bản thuộc Người 3.
