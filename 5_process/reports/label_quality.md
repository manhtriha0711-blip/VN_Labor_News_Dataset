# Báo cáo kiểm định nhãn — trạng thái chuẩn bị review

**Trạng thái:** Mẫu chính thức của authoritative dataset đã hoàn tất review thủ công (57/57 dòng hợp lệ). Riêng pool borderline cũ có 56/304 dòng đã review và lưu thành sidecar; pool này không thuộc authoritative dataset.
**Ngày rà soát:** 2026-10-27
**Hướng dẫn:** `5_process/config/labeling_guideline.md`
**Nguồn có thẩm quyền:** `1_du_lieu_chinh/vn_labor_news_dataset.csv`
**File làm việc:** `5_process/data/processed/manual_label_sample.csv`

## 1. Mẫu review và nguồn gốc

- Mẫu có 57 dòng duy nhất: 56 mẫu phân tầng theo `topic_primary` và một ví dụ ưu tiên `VNLAB-000002` theo `ISS-001`.
- Script `5_process/src/create_manual_label_sample.py` tạo mẫu trực tiếp từ CSV có thẩm quyền. 56 ID được chọn tái lập bằng thứ tự SHA-256 của `article_id` trong từng tầng, với quota A-H: 5 mỗi nhóm, I: 2, J-K: 5 mỗi nhóm và L: 4.
- Cả 16 trường nguồn trong mẫu được validator đối chiếu với bản ghi raw theo `article_id`. Các trường nguồn và nhãn tự động không bị sửa.
- `borderline_for_review.csv` có 304 dòng nhưng không có `article_id` hoặc URL trùng với CSV có thẩm quyền. Do đó file này không được dùng làm nguồn mẫu cho dataset hiện tại; vấn đề được ghi nhận tại `ISS-008`.
- Cả 57 dòng đã có các trường review bắt buộc hợp lệ; các chủ đề để trống đúng quy tắc cho `Not relevant`/`Uncertain`.
- Reviewer: `RV004`; ngày hoàn tất review: `2026-10-27`.
- Phân bố `relevance_manual`: 45 `Relevant`, 10 `Borderline`, 2 `Not relevant`.
- Validator strict `python 5_process/src/validate_manual_labels.py --require-complete` đạt: 57 reviewed, 0 pending; toàn bộ trường nguồn khớp authoritative CSV.
- Bản gợi ý AI riêng tại `5_process/reports/review_drafts/manual_label_ai_suggestions.csv` vẫn chỉ là tài liệu tham khảo, không thay thế hoặc ghi đè nhãn thủ công.

## 2. Nhãn thủ công cho pool borderline riêng

- Các quyết định từ `C:\Users\manht\Downloads\manual_label_sample.csv` được lưu tại `5_process/data/processed/legacy_borderline_manual_labels.csv`. Sidecar chỉ giữ `article_id`, nhãn thủ công, lý do, reviewer và ngày; không sao chép tiêu đề, nội dung, URL hoặc metadata bài báo.
- Cả 56 ID, tiêu đề, URL và nội dung đều khớp các dòng tương ứng trong `3_du_lieu_phu/borderline_for_review.csv`; đối chiếu đủ 16 trường nguồn, chuẩn hóa khác biệt kiểu xuống dòng. Batch có 56 dòng: 9 `Relevant`, 28 `Borderline`, 19 `Not relevant`. Topic được điền cho toàn bộ bài `Relevant`/`Borderline` và để trống cho `Not relevant`; các lý do đều có nội dung.
- Người kiểm định và ngày review theo xác nhận của người dùng: `Hà Mạnh Trí`, `2026-10-27`. Batch đã hoàn tất cho 56 bản ghi thuộc pool riêng này.
- Pool borderline 304 dòng không khớp authoritative CSV 12.784 bài hiện hành. Vì vậy không ghép nhãn của pool này vào mẫu chính thức 57 dòng hoặc dataset chính, và không dùng để đánh giá chất lượng mô hình trên dataset chính.

## 3. Ví dụ ưu tiên

`VNLAB-000002` — “Monaco sa thải Niko Kovac giữa kỳ nghỉ đông” được giữ làm ví dụ cần review theo `ISS-001`. Từ khóa “sa thải” dẫn đến nhãn tự động D trong khi bài viết nói về bóng đá, nên đây là một trường hợp có dấu hiệu nhiễu cần người kiểm định xác nhận. Bản ghi gốc được giữ nguyên; không tự điền nhãn thủ công.

## 4. Giới hạn

- Chưa có người kiểm định xác nhận; chưa thể báo cáo precision, recall, kappa hoặc tỷ lệ nhãn sai.
- Đây là mẫu phục vụ review và kiểm tra theo tầng, không thay thế nhãn vàng đại diện cho toàn bộ 12.784 bài.
- `topic_primary` dùng để phân tầng là nhãn tự động, không phải nhãn đúng đã được con người xác nhận.
- Đánh giá đồng thuận cần ít nhất hai người gán nhãn độc lập trên cùng một tập con trước khi đối chiếu.

## 5. Nghiệm thu và giới hạn

- Nhãn là quyết định của một reviewer, không phải đồng thuận đa reviewer; không tính kappa hoặc độ đồng thuận liên người.
- Đây là mẫu review phân tầng cộng một trường hợp ưu tiên, không phải mẫu ngẫu nhiên đại diện; không suy rộng tỷ lệ lỗi/độ chính xác cho toàn bộ 12.784 bài.
- `topic_primary` vẫn là weak label; nhãn thủ công chỉ áp dụng cho 57 ID trong mẫu, không tự động gán cho toàn bộ dataset.
