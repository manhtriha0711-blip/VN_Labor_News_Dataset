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

## 3. Quy tắc làm sạch

- Chuẩn hóa Unicode về dạng NFC.
- Loại bỏ khoảng trắng ở đầu và cuối văn bản.
- Chuẩn hóa các chuỗi khoảng trắng không cần thiết.
- Xử lý ký tự điều khiển không phù hợp, nhưng không làm mất nội dung hợp lệ.
- Tạo hai trường riêng là `title_clean` và `content_clean`.
- Giữ nguyên dữ liệu gốc để có thể đối chiếu.
- Không tự ý loại bỏ từ phủ định, số liệu, tên riêng hoặc URL.

## 4. Tiêu chí đạt

- Các trường hợp kiểm thử cho kết quả đúng như mong đợi.
- Không làm mất dấu tiếng Việt hoặc thông tin quan trọng.
- Dữ liệu gốc vẫn được giữ nguyên.
- Có thể chạy lại quy trình làm sạch để tái tạo kết quả.

## 5. Trạng thái

Tài liệu mô tả các trường hợp và kết quả mong đợi. Cần chạy kiểm thử trên module thực tế trước khi xác nhận tất cả trường hợp đều đạt.
