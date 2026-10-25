# Báo cáo chất lượng Process — bản tích hợp sơ bộ

**Ngày kiểm tra:** 2026-10-26  
**Trạng thái:** Chưa phải nghiệm thu cuối; đang chờ đầu ra của Người 3, xác nhận nhãn của Người 4, thống kê/handoff của Người 5 và slide của Người 6.

## 1. Đầu vào và schema

- Nguồn chuẩn: `1_du_lieu_chinh/vn_labor_news_dataset.csv`; CSV được dùng thay vì Excel.
- Quy mô: **12.784 dòng, 16 cột**.
- SHA-256: `9ed13a4758ba6aecb2c6673c9d107f19739a25b1bea364bfa86bd33b23581c96`.
- Khoảng ngày xuất bản: **2022-01-01 đến 2026-10-23**.
- Không thiếu trường bắt buộc; `article_id` và `source_url` duy nhất.
- Giá trị trống được giữ đúng nghĩa: `topic_secondary` trống 5.746 dòng; `sentiment` trống 12.784 dòng, chưa gán nhãn.
- Kiểm tra schema: **PASS**, không có lỗi mức High/Critical. Có một cảnh báo thông tin về khác biệt định nghĩa `word_count`/`content`.
- Kết quả máy đọc được: `00_input_profile.json`, `01_schema_validation.json`; lỗi kiểm tra tại `../logs/schema_validation_issues.csv`.

## 2. Kết quả metadata đã chạy lại

- Module Người 2 chạy thành công trên CSV hiện tại: **12.784 dòng vào, 12.784 dòng ra; raw bất biến theo SHA-256 trước/sau**.
- Unit test metadata: **18/18 đạt**.
- Thay đổi metadata được ghi log: 14 tiêu đề chuẩn hóa Unicode/khoảng trắng; không sửa `content`.
- Ngoại lai được đánh cờ, không tự sửa/xóa: 9 lượt.
- Có 67 bài được module ghi nhận chứa ký tự vô hình trong `content`; chuyển Người 3 xử lý ở trường dẫn xuất.
- Audit trùng: 71 dòng review, 62 cụm gồm 129 bài. Chưa có quyết định loại; tất cả bản ghi vẫn được giữ.
- `word_count` được mã Collecting tính trên thân bài trước khi có thể ghép sapo vào `content` đầu ra. Vì vậy 11.953/12.784 dòng khác `content.split()` là khác biệt định nghĩa; giữ cột gốc và dùng `word_count_recount` cho độ dài của `content` cuối khi cần.

## 3. Kiểm định nhãn

- Mẫu hiện có 56 bài từ `borderline_for_review.csv`, đại diện đủ 12 chủ đề.
- Các trường `relevance_manual`, `topic_manual`, `review_reason`, `reviewer_id`, `review_date` hiện đều trống. Vì vậy **chưa có nhãn thủ công được xác nhận** và chưa được tính precision/recall hay mức đồng thuận.
- `label_quality.md` tự ghi là bản AI sơ bộ, có lỗi định dạng và tham chiếu một file đầu ra không nằm trong bộ file hiện tại. Các thống kê trong đó chưa được xác minh từ mẫu nhãn hiện tại.
- Ví dụ Monaco `VNLAB-000002` là trường hợp cần đưa vào rà soát ưu tiên vì hiện mang nhãn D nhưng nội dung nói về huấn luyện viên bóng đá; không sửa nhãn tự động trước khi Người 4 xác nhận.

## 4. Trạng thái các phần việc

| Phần | Trạng thái | Bằng chứng/việc còn lại |
|---|---|---|
| Người 1 — profile, schema, điều phối | Đã có bản kiểm tra ban đầu | Profile, schema report, issue log và checklist được lưu; cần nghiệm thu sau tích hợp toàn bộ |
| Người 2 — metadata/audit trùng | Đã chạy | 18 test đạt; audit chạy lại theo checksum hiện tại; 71 dòng duplicate review cần quyết định |
| Người 3 — text cleaning | Chờ bàn giao | Chưa có module, test và ví dụ trước/sau trong `5_process` |
| Người 4 — nhãn thủ công | Chờ xác nhận | 56 dòng nhãn chưa điền; cần sửa báo cáo sơ bộ và review trường hợp ưu tiên |
| Người 5 — thống kê/Modeling handoff | Chờ bàn giao | Chưa có báo cáo, biểu đồ, đề xuất split/leakage trong `5_process` |
| Người 6 — slide | Chờ bàn giao | Chưa có slide trong thư mục Process; cần đối chiếu mọi số liệu với báo cáo |

## 5. Hạn chế và quyết định còn mở

1. Không coi nhãn tự động A–L hay `relevant_auto` là ground truth.
2. Không tự gán `sentiment`; không loại bài chỉ vì cờ ngoại lai hoặc nghi trùng.
3. Chưa tạo tập train/validation/test cho đến khi Người 5 chốt quy tắc và có nhãn/khóa chống leakage phù hợp.
4. Đây là báo cáo tiến độ chất lượng Process dựa trên các artefact hiện có, không phải kết quả hoàn thành toàn dự án.
