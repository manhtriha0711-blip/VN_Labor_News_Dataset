# Báo cáo chất lượng Process — tích hợp và nghiệm thu kỹ thuật

**Ngày chạy lại:** 2026-10-27
**Trạng thái Người 1:** **Hoàn thành nghiệm thu kỹ thuật phần tích hợp.**
**Trạng thái gói Process:** Các đầu ra tích hợp của Người 1–5 đã được tạo và kiểm tra. Slide của Người 6 được để ngoài gói này để thành viên tự thực hiện; nhãn thủ công vẫn chờ người thật xác nhận. Các cặp/cụm nghi trùng đã biết được cô lập khỏi modeling manifest.

## 1. Đầu vào chuẩn và schema

- Nguồn duy nhất: `1_du_lieu_chinh/vn_labor_news_dataset.csv`; không dùng workbook để xử lý.
- Quy mô: **12.784 dòng, 16 cột**; `article_id` duy nhất.
- SHA-256: `9ed13a4758ba6aecb2c6673c9d107f19739a25b1bea364bfa86bd33b23581c96`.
- Khoảng `publish_date`: **2022-01-01 đến 2026-10-23**; không có ngày lỗi.
- `source_url` duy nhất; tên nguồn thuộc danh sách 8 nguồn; `topic_primary` theo mã A–L.
- Schema validation: **PASS**, 0 lỗi Critical/High. Một cảnh báo Info ghi nhận `word_count` khác `content.split()` ở 11.953/12.784 dòng; giá trị raw được giữ nguyên, khác biệt định nghĩa đã ghi tại `ISS-002`.
- Thiếu dữ liệu được giữ đúng nghĩa: `topic_secondary` trống 5.746 dòng; `sentiment` trống 12.784 dòng, không được đổi thành “neutral”.
- Hồ sơ máy đọc được: `00_input_profile.json`, `01_schema_validation.json`; issue schema tại `../logs/schema_validation_issues.csv`.

## 2. Chạy lại và đối chiếu tích hợp

Đã chạy tuần tự các bước profile → schema → metadata → text cleaning → thống kê/split từ CSV nguồn. Bộ test mẫu chạy trước khi chạy dữ liệu đầy đủ.

`integration_validation.json` xác nhận:

- Raw vẫn cùng SHA-256 trước/sau và có 12.784 ID duy nhất.
- Metadata CSV và Parquet đều có đúng 12.784 ID như raw.
- Text-clean CSV có 12.784 dòng; toàn bộ 16 trường gốc được so từng dòng và giữ nguyên; `title_clean`/`content_clean` khớp hàm làm sạch ở cả 12.784 dòng.
- Temporal split manifest và modeling eligibility manifest đều có đúng 12.784 ID, không thiếu hoặc lặp; quy tắc ngày, hold reasons và số lượng khớp raw.
- Không có bản ghi nào bị loại khỏi các đầu ra đã kiểm tra.

Test: **45/45** test Process đạt; **7/7** test gốc đạt. Lệnh chạy được ghi trong `../README_PROCESS.md`.

## 3. Trạng thái đầu ra theo phần việc

| Phần | Đã tích hợp / kiểm tra | Còn mở |
|---|---|---|
| Người 1 — profile, schema, điều phối | Hồ sơ/checksum cập nhật; schema chạy; raw-preservation và khớp ID kiểm tra xuyên các module; checklist và README thống nhất | Nghiệm thu kỹ thuật hoàn tất |
| Người 2 — metadata | 12.784 dòng vào/ra; raw bất biến; 14 thay đổi metadata được log; 9 lượt ngoại lai được đánh cờ; 71 dòng duplicate review, 62 cụm; không xóa bài | Hoàn tất phạm vi audit theo phân công. Gợi ý AI chỉ là tham khảo, không nạp thành quyết định production |
| Người 3 — text | 12.784 dòng; cột gốc giữ nguyên; cột sạch tái tạo và kiểm tra từng dòng; ví dụ và test có sẵn | Không còn blocker kỹ thuật đã biết |
| Người 4 — nhãn | Hướng dẫn, mẫu, validator và báo cáo chất lượng đã tích hợp; mẫu 57 bài được tái tạo trực tiếp từ raw (56 phân tầng theo topic + 1 ưu tiên ISS-001) | **0/57** được người thật xác nhận; `ISS-003` mở. Không tính gợi ý AI là nhãn |
| Người 5 — thống kê/split | Thống kê, 5 biểu đồ, script, temporal manifest, eligibility manifest, báo cáo leakage và handoff đều sinh được | 65 ID liên quan cặp/cụm cross-split đã biết được cô lập bằng `review_hold`; heuristic không đảm bảo phát hiện hết leakage |
| Người 6 — slide | Báo cáo chất lượng, thống kê, split và biểu đồ đã sẵn sàng làm nguồn | Chưa tạo slide; bàn giao riêng cho Người 6 |

## 4. Split và giới hạn đánh giá

- Train: **8.213** bài (trước 2025); validation: **2.562** bài (năm 2025); test: **2.009** bài (từ 2026-01-01).
- 118 cặp tiêu đề được sàng lọc; 32 cặp nằm khác split. Đây là ứng viên, không phải phán quyết trùng.
- Hai cụm metadata giao split: `DUP-0037` (train/validation; 2 bài) và `DUP-0059` (validation/test; 4 bài). Các bản ghi liên quan đã được giữ ở `review_hold`; không tự ý loại hoặc chuyển bài.
- 65 ID duy nhất có liên quan đến các cặp/cụm giao split đã biết được giữ trong `modeling_eligibility_manifest.csv` với `modeling_split=review_hold`; temporal manifest gốc vẫn giữ đủ dữ liệu.
- `topic_primary` là weak label tự động, chưa phải nhãn vàng. Chưa huấn luyện mô hình và không tuyên bố split heuristic đã loại hết leakage.
- Chi tiết: `split_validation.md`, `split_and_leakage_checks.json`, `process_statistics.md`, `handoff_to_modeling.md`.

## 5. Các việc còn mở và ranh giới nghiệm thu

1. **Người 4:** người thật hoàn thành 57 dòng review mẫu, sau đó chạy validator strict.
2. **Người 6:** tạo slide, ghi chú thuyết trình và nguồn số liệu theo phân công; deliverable này chưa được đưa vào nhánh tích hợp.
3. Có thể review các ID đang ở `review_hold` sau này; không đưa lại vào modeling trước khi ghi quyết định.
4. Không gán sentiment; không dùng nhãn tự động làm ground truth; không công bố dữ liệu toàn văn.

Các trạng thái trên cũng được theo dõi tại `../logs/issue_log.csv`. Việc phần Người 1 được nghiệm thu kỹ thuật **không đồng nghĩa** các công việc review thủ công hoặc toàn bộ Process của nhóm đã hoàn tất.
