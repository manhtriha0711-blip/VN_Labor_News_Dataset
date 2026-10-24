# Ghi chú rà soát đầu vào Collecting

**Thời điểm rà soát:** 24/10/2026  
**Phụ trách:** Người 1 — trưởng nhóm  
**Trạng thái:** Rà soát đầu vào ban đầu; các issue được theo dõi riêng trong `../logs/issue_log.csv`.

## 1. Nguồn dữ liệu và nguyên tắc

- Đầu vào chuẩn cho Process: `1_du_lieu_chinh/vn_labor_news_dataset.csv`.
- Không dùng file Excel làm đầu vào xử lý vì nội dung dài có thể bị cắt theo giới hạn ô.
- Chỉ đọc dữ liệu Collecting; không sửa hoặc ghi đè CSV, Excel, log hay báo cáo gốc.
- Đầu ra Process phải được tạo ở thư mục riêng và mọi chuẩn hóa/thay đổi phải có thể truy vết.
- Phạm vi ngày quan sát được: `2022-01-01` đến `2026-10-23`.
- CSV có 12.784 bản ghi, 16 cột. `article_id` và `source_url` không trùng trong lần rà soát.

## 2. Schema CSV

| # | Cột | Ý nghĩa/trạng thái rà soát |
|---|---|---|
| 1 | `article_id` | ID bài; không thiếu, không trùng |
| 2 | `title` | Tiêu đề; không thiếu |
| 3 | `content` | Nội dung; không thiếu; dùng CSV để giữ văn bản đầy đủ |
| 4 | `publish_date` | Ngày xuất bản; parse được trong lần rà soát |
| 5 | `source_name` | Tên nguồn báo; không thiếu |
| 6 | `source_url` | URL gốc; không thiếu, không trùng |
| 7 | `topic_primary` | Chủ đề chính gán tự động; không thiếu, chưa phải nhãn đã xác nhận thủ công |
| 8 | `topic_secondary` | Chủ đề phụ; được phép trống |
| 9 | `matched_keywords` | Từ khóa khớp; không thiếu trong lần rà soát |
| 10 | `location` | Địa danh được nhắc nhiều nhất; không thiếu; không mặc định là nơi sự kiện xảy ra |
| 11 | `sentiment` | Chưa gán; trống toàn bộ có chủ ý, không được đổi thành “neutral” |
| 12 | `relevance_status` | Trạng thái liên quan; toàn bộ CSV chính là `relevant_auto` |
| 13 | `collection_date` | Ngày thu thập; không thiếu |
| 14 | `data_quality_note` | Ghi chú chất lượng; không thiếu trong lần rà soát |
| 15 | `relevance_score` | Điểm liên quan dạng số; cần giữ nguyên giá trị gốc |
| 16 | `word_count` | Số từ; cần xác minh định nghĩa và cách tính, xem issue `ISS-002` |

Theo checklist schema của kế hoạch, các trường bắt buộc là `article_id`, `title`, `content`, `publish_date`, `source_name`, `source_url`, `topic_primary` và `relevance_status`. Lần rà soát CSV không thấy trường nào trong nhóm này bị thiếu. Những giá trị thiếu đã xác nhận/được chấp nhận là `topic_secondary` (5.746/12.784 dòng) và `sentiment` (12.784/12.784 dòng).

## 3. Rủi ro và việc cần xác minh

1. Nhãn `topic_primary` và `relevance_status` là kết quả tự động; không coi là ground truth. Ví dụ bài thể thao về Monaco đang mang nhãn chủ đề D được ghi tại `ISS-001`, giao Người 4 xem xét trong kiểm định nhãn.
2. `word_count` khác kết quả đếm lại trên `content` cuối ở 11.953/12.784 dòng. Chưa sửa giá trị; cần xác minh định nghĩa và thời điểm đếm với Người 2/3, xem `ISS-002`.
3. Bản Excel là bản tiện xem, không phải nguồn chuẩn để xử lý văn bản dài.
4. `sentiment` trống không có nghĩa là cảm xúc trung tính.
5. Raw Collecting và các báo cáo lịch sử phải được giữ nguyên để đảm bảo truy nguyên.

## 4. Biên bản tiến độ

Trưởng nhóm xác nhận buổi khởi động 15:00–15:30 ngày 24/10 đã diễn ra. Bảng theo dõi vẫn cần đường dẫn biên bản và xác nhận đầu vào/đầu ra đã thống nhất trước khi P01 được nghiệm thu hoàn tất.
