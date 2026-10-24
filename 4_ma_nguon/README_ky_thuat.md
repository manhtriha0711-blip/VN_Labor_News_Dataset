# Bộ dữ liệu tin tức lao động – việc làm Việt Nam (2022 → nay)

Bộ dữ liệu bài báo tiếng Việt về thị trường việc làm, thất nghiệp và quyền lợi người lao động tại Việt Nam,
phục vụ môn Data Mining. Mỗi dòng là **một bài báo có thật**, có URL gốc để kiểm tra lại; không có bản ghi
nào được tự tạo hay suy diễn.

## Tệp bàn giao

| Tệp | Nội dung |
|---|---|
| `output/vn_labor_news_dataset.csv` | Bộ dữ liệu chính (UTF-8 có BOM – mở được bằng Excel và pandas) |
| `output/vn_labor_news_dataset.xlsx` | Bản Excel (nội dung > 32.000 ký tự bị cắt theo giới hạn ô Excel, có ghi chú) |
| `output/borderline_for_review.csv` | Bài "ranh giới" cần người kiểm tra – **không** tính vào số mẫu hợp lệ |
| `output/rejected_log.csv` | Mọi bài đã tải nhưng bị loại, kèm lý do |
| `output/duplicates_log.csv` | Bài bị loại do trùng lặp và bài được giữ lại |
| `output/qa_random_sample.csv` | 100 mẫu ngẫu nhiên để kiểm tra thủ công |
| `output/data_quality_report.md`, `output/stats.json` | Báo cáo số lượng theo nguồn/năm/chủ đề và chất lượng |
| `data/urls/*.jsonl` | Toàn bộ URL phát hiện từ sitemap (checkpoint giai đoạn 1–2) |
| `data/raw/*.jsonl` | Bản ghi đã tải, chưa lọc (checkpoint giai đoạn 3) |
| `scripts/` | Mã nguồn |

## Nguồn và phương thức thu thập

Tất cả nguồn đều cho phép thu thập theo `robots.txt` (`User-agent: * / Allow: /`) và công bố sitemap theo
ngày/tháng. Dữ liệu được lấy **chỉ** qua sitemap công khai + trang bài viết công khai, tốc độ ~1 request/giây/nguồn,
User-Agent ghi rõ mục đích học thuật.

| Nguồn | Tên miền | Sitemap dùng |
|---|---|---|
| Dân Trí | dantri.com.vn | `/sitemaps/Article-YYYY-MM-01.xml` |
| Tuổi Trẻ | tuoitre.vn | `/StaticSitemaps/sitemaps-YYYY-M-a-b.xml` |
| Thanh Niên | thanhnien.vn | `/sitemaps/sitemaps-YYYY-M-a-b.xml` |
| VietNamNet | vietnamnet.vn | `/sitemap-article-M-YYYY-NN.xml` |
| Tiền Phong | tienphong.vn | `/sitemaps/news-YYYY-M.xml` |
| VnEconomy | vneconomy.vn | `/sitemap/news-YYYY-MM.xml` |
| Nhân Dân | nhandan.vn | `/sitemaps/news-YYYY-M.xml` |
| Sài Gòn Giải Phóng | sggp.org.vn | `/sitemaps/news-YYYY-M.xml` |

**Dân Trí chỉ chiếm ~2,4% bộ dữ liệu**: máy chủ phản hồi rất chậm với truy cập tuần tự (~20 bài/phút, sau đó còn
chậm hơn), nên việc tải bị dừng chủ động ở ~400 bài để không tăng tải cho máy chủ. Còn ~18.500 URL ứng viên Dân Trí
chưa tải; có thể chạy tiếp bằng `python scripts/fetch_articles.py --sources dantri --budget 3000` (tự bỏ qua bài đã tải).

Nguồn đã khảo sát nhưng **không dùng**:
- **laodong.vn** – trả về trang thử thách cookie bằng JavaScript (cơ chế chống bot); không vượt cơ chế này.
- **nld.com.vn** – tên miền chuyển về Tuổi Trẻ, sitemap rỗng.
- **vnexpress.net** – sitemap theo ngày trả lỗi 504 liên tục tại thời điểm thu thập.
- **plo.vn** – `robots.txt` cấm toàn bộ (`Disallow: /`).

## Quy trình

1. **Khảo sát nguồn** (`probe_*.py`): kiểm tra robots.txt, cấu trúc sitemap, cấu trúc HTML bài viết.
2. **Phát hiện URL** (`harvest_sitemaps.py`): duyệt mọi sitemap con 2022→nay; đánh dấu URL "ứng viên" nếu slug
   (hoặc tiêu đề trong sitemap) khớp mẫu từ khóa lao động không dấu (`keywords.SLUG_PATTERNS`).
3. **Trích xuất** (`fetch_articles.py`): tải bài theo thứ tự ưu tiên (slug "mạnh" trước, trộn ngẫu nhiên seed=42
   để phân bố đều theo thời gian); lấy tiêu đề (h1/og:title), ngày xuất bản (JSON-LD `datePublished` → meta
   `article:published_time`), sapo (meta description), thân bài (bộ chọn CSS riêng từng báo, có phương án dự phòng).
4. **Lọc & làm sạch** (`clean_and_export.py` + `keywords.assess`):
   - Loại: không tải được, thiếu tiêu đề/ngày, ngoài khoảng thời gian, thân bài < 300 ký tự hoặc không trích xuất được.
   - Loại tin tuyển dụng thông thường, quảng cáo/tài trợ, thể thao, tin trao huân chương, bản tin tổng hợp nhiều chủ đề.
   - Loại tin quốc tế: tiêu đề có yếu tố nước ngoài nhưng thân bài gần như không liên hệ Việt Nam.
   - Chấm điểm liên quan: đếm "từ neo" lao động (người lao động, việc làm, công nhân, BHXH, NLĐ…) và từ khóa
     "mạnh" của 12 nhóm A–L. Từ chung (kinh tế, lạm phát, nghị định, tên tỉnh…) chỉ là bổ trợ.
     Kết quả: `relevant_auto` (tính vào mẫu hợp lệ), `borderline_auto` (cần người kiểm tra), hoặc loại.
5. **Khử trùng lặp**: URL chuẩn hóa → tiêu đề chuẩn hóa (bỏ dấu, ký tự đặc biệt) → nội dung gần giống
   (SimHash 64-bit trên shingle 5 từ, xác nhận bằng Jaccard ≥ 0,7). Ưu tiên giữ bản đầy đủ hơn.
6. **Báo cáo**: số lượng theo nguồn/năm/chủ đề/địa phương, tỷ lệ thiếu dữ liệu, tỷ lệ trùng lặp, lý do loại.

## Các cột dữ liệu

| Cột | Ý nghĩa |
|---|---|
| `article_id` | Mã duy nhất `VNLAB-000001`… |
| `title`, `content` | Tiêu đề; sapo + thân bài trích xuất được (không gồm chú thích ảnh, hộp tin liên quan) |
| `publish_date` | Ngày xuất bản YYYY-MM-DD lấy từ siêu dữ liệu của chính bài báo |
| `source_name`, `source_url` | Tên báo, URL gốc |
| `topic_primary`, `topic_secondary` | Nhóm chủ đề A–L, **gán tự động theo luật từ khóa** |
| `matched_keywords` | Từ khóa A–L khớp trong bài |
| `location` | Tối đa 3 tỉnh/thành được nhắc nhiều nhất; "Toàn quốc/không xác định" nếu không rõ |
| `sentiment` | **Để trống** – chưa phân tích, không gán khi chưa có căn cứ |
| `relevance_status` | `relevant_auto` (bộ chính) / `borderline_auto` (tệp ranh giới) |
| `collection_date` | Ngày tải bài |
| `data_quality_note` | Ghi chú: nội dung ngắn, trích xuất dự phòng, **bài có nội dung phản ánh/cáo buộc vi phạm** (không phải kết luận vi phạm) |
| `relevance_score`, `word_count` | Điểm liên quan, số từ thân bài (cột bổ sung) |

## Lưu ý sử dụng

- Nhãn chủ đề và mức độ liên quan là **tự động**. Kiểm tra tay các mẫu ngẫu nhiên (50 + 30 bài, sau 2 vòng tinh chỉnh
  bộ lọc) cho thấy khoảng **85–90%** bài đúng chủ đề rõ ràng; phần còn lại là bài "ăn theo" từ khóa (vd. nhân viên
  một công ty bị bắt vì lý do khác, VĐV nước ngoài "nghỉ việc không lương"). Nên kiểm tra tay thêm nếu dùng làm nhãn huấn luyện.
- Bài có từ "nợ lương", "trốn đóng BHXH", "sa thải"… **không** đồng nghĩa doanh nghiệp vi phạm pháp luật; bộ dữ liệu
  không gán nhãn vi phạm.
- Nội dung bài báo thuộc bản quyền của các cơ quan báo chí; bộ dữ liệu chỉ dùng cho mục đích học tập/nghiên cứu,
  không phát hành lại công khai toàn văn.
- Tên tỉnh/thành: dùng tên trước sáp nhập (63 tỉnh); các tỉnh sau 1/7/2025 mang tên một tỉnh cũ nên vẫn được nhận diện.

## Chạy lại / mở rộng

```powershell
pip install requests beautifulsoup4 lxml pandas openpyxl
python scripts/harvest_sitemaps.py                 # giai đoạn 1-2 (chạy tiếp được nếu bị ngắt)
python scripts/fetch_articles.py --budget 3000     # giai đoạn 3; tăng --budget để tải thêm
python scripts/clean_and_export.py                 # giai đoạn 4-6
```
