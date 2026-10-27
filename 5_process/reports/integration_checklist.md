# Checklist tích hợp và nghiệm thu Process

**Cập nhật:** 2026-10-27
**Người 1 — nghiệm thu kỹ thuật:** Hoàn thành.
**Gói tích hợp kỹ thuật (Người 1–5):** Hoàn thành, gồm review nhãn thủ công 57/57 của Người 4. Slide Người 6 được để riêng để bàn giao.

## Người 1 — đầu vào, schema và tích hợp

- [x] Xác nhận CSV là nguồn chuẩn; profile có 12.784 dòng, 16 cột, checksum và phiên bản chạy.
- [x] Kiểm tra schema, ID/URL trùng, ngày, nguồn và topic; ghi issue. Kết quả PASS, không có lỗi Critical/High.
- [x] Giữ nguyên các trường thiếu có chủ ý; không tự gán `sentiment` hoặc sửa `word_count`.
- [x] Chạy unit tests trước pipeline toàn bộ; không ghi đè raw.
- [x] Tích hợp và chạy lại metadata Người 2, text cleaning Người 3, thống kê/split Người 5.
- [x] Đối chiếu raw preservation, dòng, ID, text-clean fields và split manifest bằng `validate_process_integration.py`.
- [x] Cập nhật README, báo cáo chất lượng, issue log và hướng dẫn chạy.

## Trạng thái các đầu việc liên quan

- [x] Người 2: module, audit list, logs và outputs chạy được; AI recommendations không được áp dụng như quyết định của người review; `ISS-006` đóng theo phạm vi audit.
- [x] Người 3: module, tests, ví dụ và output đầy đủ; đầu ra kiểm tra trên 12.784 dòng.
- [x] Người 4: 57/57 nhãn được reviewer RV004 xác nhận ngày 2026-10-27; validator strict đạt (`ISS-003` resolved).
- [x] Người 5: báo cáo/split/handoff được tái sinh; 65 ID liên quan các ứng viên cross-split đã biết được gắn `review_hold` (`ISS-007` mitigated).
- [ ] Người 6: tự xây dựng slide và ghi chú từ các báo cáo/biểu đồ đã kiểm tra; phần này được để ngoài gói tích hợp để bàn giao riêng.

## Kiểm tra đã chạy

- [x] `python -m unittest discover -s 5_process/tests -p "test_*.py" -v` — 47/47 đạt.
- [x] `python -m unittest test_text_cleaning -v` — 7/7 đạt.
- [x] Pipeline từ raw: profile → schema → metadata → text cleaning → thống kê/split.
- [x] `python 5_process/src/validate_process_integration.py` — PASS; raw bất biến, 12.784 dòng/ID đối chiếu khớp.
- [x] `python 5_process/src/create_manual_label_sample.py` — tạo lại 57 dòng từ raw: 56 phân tầng theo topic + 1 ví dụ ưu tiên.
- [x] `python 5_process/src/validate_manual_labels.py --require-complete` — 57 reviewed, 0 pending; source fields đối chiếu khớp.

## Điều kiện trước khi gọi toàn bộ Process là hoàn tất

1. Người 6 hoàn tất slide và ghi chú thuyết trình theo phân công.
2. Nếu muốn đưa các ID `review_hold` trở lại modeling, ghi quyết định review và chạy lại leakage audit.
