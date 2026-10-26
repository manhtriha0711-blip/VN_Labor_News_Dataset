# Báo cáo kiểm định nhãn — trạng thái chuẩn bị review

**Trạng thái:** Chưa có nhãn thủ công; 0/57 dòng được người kiểm định xác nhận.
**Ngày rà soát:** 2026-10-27
**Hướng dẫn:** `5_process/config/labeling_guideline.md`
**Nguồn có thẩm quyền:** `1_du_lieu_chinh/vn_labor_news_dataset.csv`
**File làm việc:** `5_process/data/processed/manual_label_sample.csv`

## 1. Mẫu review và nguồn gốc

- Mẫu có 57 dòng duy nhất: 56 mẫu phân tầng theo `topic_primary` và một ví dụ ưu tiên `VNLAB-000002` theo `ISS-001`.
- Script `5_process/src/create_manual_label_sample.py` tạo mẫu trực tiếp từ CSV có thẩm quyền. 56 ID được chọn tái lập bằng thứ tự SHA-256 của `article_id` trong từng tầng, với quota A-H: 5 mỗi nhóm, I: 2, J-K: 5 mỗi nhóm và L: 4.
- Cả 16 trường nguồn trong mẫu được validator đối chiếu với bản ghi raw theo `article_id`. Các trường nguồn và nhãn tự động không bị sửa.
- `borderline_for_review.csv` có 304 dòng nhưng không có `article_id` hoặc URL trùng với CSV có thẩm quyền. Do đó file này không được dùng làm nguồn mẫu cho dataset hiện tại; vấn đề được ghi nhận tại `ISS-008`.
- Mọi trường nhãn thủ công đang trống trên 57/57 dòng. Ba trường `ai_suggested_*` đều trống; `ai_review_status` chỉ ghi “No AI suggestion; awaiting human review”.

## 2. Ví dụ ưu tiên

`VNLAB-000002` — “Monaco sa thải Niko Kovac giữa kỳ nghỉ đông” được giữ làm ví dụ cần review theo `ISS-001`. Từ khóa “sa thải” dẫn đến nhãn tự động D trong khi bài viết nói về bóng đá, nên đây là một trường hợp có dấu hiệu nhiễu cần người kiểm định xác nhận. Bản ghi gốc được giữ nguyên; không tự điền nhãn thủ công.

## 3. Giới hạn

- Chưa có người kiểm định xác nhận; chưa thể báo cáo precision, recall, kappa hoặc tỷ lệ nhãn sai.
- Đây là mẫu phục vụ review và kiểm tra theo tầng, không thay thế nhãn vàng đại diện cho toàn bộ 12.784 bài.
- `topic_primary` dùng để phân tầng là nhãn tự động, không phải nhãn đúng đã được con người xác nhận.
- Đánh giá đồng thuận cần ít nhất hai người gán nhãn độc lập trên cùng một tập con trước khi đối chiếu.

## 4. Bước còn lại để nghiệm thu

1. Người kiểm định đọc 57 bản ghi trong `manual_label_sample.csv` theo `labeling_guideline.md`.
2. Điền đủ `relevance_manual`, `topic_manual`, `review_reason`, `reviewer_id` và `review_date`; ghi người và ngày thực tế. Với `Not relevant`/`Uncertain`, để `topic_manual` trống.
3. Chạy `python 5_process/src/validate_manual_labels.py --require-complete`.
4. Chỉ sau khi validator đạt và có xác nhận thật mới cập nhật báo cáo phân bố nhãn, trạng thái review và đóng `ISS-003`.

Hiện tại các đầu ra kỹ thuật đã sẵn sàng; blocker còn lại là người thật xác nhận nhãn trên 57 dòng.
