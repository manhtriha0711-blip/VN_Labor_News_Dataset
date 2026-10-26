# Bàn giao cho nhóm Modeling

## Trạng thái

- Đã sinh manifest theo thời gian: train trước 2025-01-01, validation trong năm 2025, test từ 2026-01-01.
- Quy mô: train 8,213, validation 2,562, test 2,009; tổng 12,784 bài.
- `topic_primary` chỉ là **weak label** tự động, không phải nhãn vàng. Cần xác nhận đây là nhãn mục tiêu trước khi huấn luyện; mẫu review 57 dòng (56 phân tầng + 1 ví dụ ưu tiên) vẫn chờ con người xác nhận.
- Đây là manifest metadata, không phải feature matrix. Chưa huấn luyện mô hình.

## Việc bắt buộc trước khi báo cáo kết quả cuối

- Modeling manifest gắn 65 ID liên quan tới 32 cặp tiêu đề và 2 cụm metadata đã biết là `review_hold`. Chỉ dùng các dòng có `modeling_split` là train/validation/test. Nếu muốn đưa holdout trở lại, rà soát thủ công, ghi quyết định và tái sinh audit.
- Xác nhận nhãn đích, định nghĩa task và tiêu chí đánh giá; loại `article_id`, nhãn mục tiêu và mọi trường suy ra trực tiếp từ nhãn khỏi features.
- Trước khi cố định split đánh giá cuối, xác nhận rằng các dòng `review_hold` được loại trừ hoặc có quyết định review được ghi nhận. Heuristic không bảo đảm phát hiện hết leakage; nếu thay đổi dữ liệu hoặc quy tắc, chạy lại script audit.
- Với phân chia theo thời gian, báo cáo macro-F1 và chỉ số từng lớp; nêu rõ mất cân bằng và tính yếu của nhãn.

## File đầu ra

- `5_process/splits/split_manifest.csv` và `train_manifest.csv`, `validation_manifest.csv`, `test_manifest.csv`.
- `5_process/splits/modeling_eligibility_manifest.csv`: giữ toàn bộ ID; các ứng viên/cụm đã biết giao split được gắn `modeling_split=review_hold`, không dùng cho đánh giá đến khi review.
- `5_process/reports/split_validation.md`: quy tắc, số lượng, phân bố và cảnh báo.
- `5_process/reports/split_and_leakage_checks.json`: kiểm tra dạng máy đọc được.
- `5_process/reports/near_duplicate_title_candidates.csv`: cặp tiêu đề cần review; là sàng lọc ứng viên, không xác nhận trùng.
