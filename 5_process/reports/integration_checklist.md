# Checklist tích hợp và nghiệm thu — Người 1

**Trạng thái hiện tại:** Đang thực hiện; chưa được xem là bản Process cuối.

## Đầu vào và schema

- [x] Lưu hồ sơ đầu vào và SHA-256 tại `00_input_profile.json`/`.md`.
- [x] Chạy kiểm tra schema; lưu kết quả và issue log.
- [x] Xác nhận CSV gốc vẫn nguyên vẹn; không xử lý từ Excel.
- [x] Ghi rõ các trường thiếu được chấp nhận: `topic_secondary`, `sentiment`.

## Tích hợp module

- [x] Người 2: metadata cleaning, audit trùng; unit tests đạt 18/18 sau khi khôi phục cấu trúc.
- [ ] Người 3: text cleaning, tests, ví dụ trước/sau.
- [ ] Người 4: người kiểm định xác nhận mẫu nhãn; bản hiện tại còn trống nhãn thủ công.
- [ ] Người 5: thống kê, biểu đồ, đề xuất split và leakage audit.
- [ ] Người 6: slide khớp số liệu đã xác minh, không chứa toàn văn bài báo.

## Chất lượng và bàn giao

- [x] Làm rõ định nghĩa `word_count` với mã Collecting; giữ nguyên raw và ghi rõ trường đếm lại.
- [ ] Review các cụm trùng; chưa loại bài tự động.
- [ ] Chạy pipeline tích hợp trên mẫu, sau đó toàn bộ khi kiểm thử đạt.
- [ ] Đối chiếu số dòng, schema, hash raw, issue log, báo cáo và slide.
- [ ] README có lệnh chạy đúng từ thư mục gốc và yêu cầu môi trường.
- [ ] Mở thử các file bàn giao; loại dữ liệu toàn văn khỏi nội dung công khai.
