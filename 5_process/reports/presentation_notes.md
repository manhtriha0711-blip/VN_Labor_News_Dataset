# Ghi chú thuyết trình — Process VN Labor News Dataset

Slide được sinh bằng `python 5_process/src/create_process_presentation.py` từ báo cáo Process và CSV nguồn ở chế độ chỉ đọc. Không chèn tiêu đề hoặc toàn văn bài báo.

## Nguồn số liệu theo slide

1. Tiêu đề: `Phan_cong_Process_6_nguoi.md`, `00_input_profile.json`.
2. Mục tiêu/phạm vi: `Phan_cong_Process_6_nguoi.md`, `00_input_profile.json`, `process_quality_report.md`.
3. Pipeline: `README_PROCESS.md`, `integration_validation.json`.
4. Chất lượng: `00_input_profile.json`, `01_schema_validation.json`, `integration_validation.json`, `process_statistics.md`.
5. Metadata/nhãn: `metadata_audit.md`, `label_quality.md`, `issue_log.csv`.
6. Thống kê: `process_statistics.md` và biểu đồ do `create_splits_and_leakage_audit.py` sinh.
7. Split/leakage: `split_validation.md`, `split_and_leakage_checks.json`, `handoff_to_modeling.md`.
8. Tiến độ thành viên: `integration_checklist.md`, `process_quality_report.md`, `issue_log.csv`.
9. Kết luận/hạn chế: `process_quality_report.md`, `labeling_guideline.md`, `handoff_to_modeling.md`.

## Lời dẫn gợi ý

- Nhấn mạnh checksum và raw preservation: kết quả biến đổi chỉ nằm ở thư mục Process.
- Phân biệt nhãn tự động với nhãn thủ công; mẫu review chưa được người xác nhận.
- Gọi split là phương án mặc định theo thời gian; 65 ID đã biết bị giữ ngoài modeling.
- 32 cặp tiêu đề và 2 cụm duplicate giao split là cảnh báo ứng viên, không khẳng định chắc chắn trùng.
- Không trình bày các bản nháp AI của metadata như quyết định chính thức.
