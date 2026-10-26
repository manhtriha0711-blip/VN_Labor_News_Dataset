# Text Cleaning — Kiểm thử trước và sau

## 1. Mục tiêu

Kiểm tra chức năng làm sạch tiêu đề và nội dung tin tức tiếng Việt, bảo đảm văn bản thống nhất nhưng không làm mất thông tin quan trọng.

## 2. Các trường hợp kiểm thử

| STT | Dữ liệu đầu vào | Kết quả mong đợi |
|---|---|---|
| 1 | `  Thị trường lao động Việt Nam  ` | `Thị trường lao động Việt Nam` |
| 2 | `Người lao động\t\tViệt Nam` | `Người lao động Việt Nam` |
| 3 | `Chính phủ chưa công bố số liệu.` | Giữ nguyên nội dung và từ phủ định `chưa` |
| 4 | `Lương tối thiểu tăng 6%; áp dụng từ 01/07/2026.` | Giữ nguyên số liệu, dấu câu và ngày tháng |
| 5 | `Xem thêm https://example.com/news` | Giữ nguyên URL |
| 6 | `Công ty TNHH ABC tuyển dụng tại Hà Nội.` | Giữ nguyên tên riêng và địa danh |
| 7 | Văn bản tiếng Việt có dấu Unicode | Giữ nguyên dấu tiếng Việt và ý nghĩa câu |
| 8 | Văn bản có zero-width space, BOM, soft hyphen và ký tự định dạng vô hình | Dấu phân cách vô hình được chuẩn hóa/bỏ; không dính từ |
| 9 | Chuỗi emoji/chữ cần ZWJ hoặc ZWNJ | Giữ nguyên ký tự nối |
| 10 | Nội dung dài hơn 70.000 ký tự qua pipeline CSV | Giữ đủ nội dung đã chuẩn hóa; các trường nguồn không đổi |

## 3. Quy tắc làm sạch

- Chuẩn hóa Unicode về dạng NFC.
- Loại bỏ khoảng trắng ở đầu và cuối văn bản.
- Chuẩn hóa các chuỗi khoảng trắng không cần thiết.
- Xóa ký tự điều khiển; đổi zero-width space, BOM trong văn bản và word joiner thành dấu cách; bỏ soft hyphen và ký tự định dạng vô hình khác.
- Giữ ZWJ/ZWNJ để không phá các cụm chữ hoặc emoji cần ký tự nối.
- Tạo hai trường riêng là `title_clean` và `content_clean`.
- Giữ nguyên dữ liệu gốc để có thể đối chiếu.
- Không tự ý loại bỏ từ phủ định, số liệu, tên riêng hoặc URL.
- Chỉ thay thế CSV đầu ra khi toàn bộ đầu vào hợp lệ; từ chối đường dẫn nguồn và đích trùng nhau.

## 4. Tiêu chí đạt

- Các trường hợp kiểm thử cho kết quả đúng như mong đợi.
- Không làm mất dấu tiếng Việt hoặc thông tin quan trọng.
- Dữ liệu gốc vẫn được giữ nguyên.
- Có thể chạy lại quy trình làm sạch để tái tạo kết quả.

## 5. Trạng thái

Đã chạy lại `python -m unittest discover -s 5_process/tests -p "test_*.py" -v`: 43 test Process đạt; kiểm thử gốc `python -m unittest test_text_cleaning -v`: 7/7 đạt. Pipeline toàn bộ tạo 12.784 dòng; `validate_process_integration.py` đối chiếu từng trường gốc và xác nhận `title_clean`/`content_clean` khớp hàm làm sạch. CSV nguồn không thay đổi.
