# Phân công công việc Process — 6 thành viên

**Dự án:** VN_Labor_News_Dataset  
**Trưởng nhóm mặc định:** Người 1  
**Mục tiêu:** Tạo dữ liệu Process có kiểm tra, truy vết và chạy lại được; chưa huấn luyện mô hình.

## Đầu vào và quy ước chung

- Dùng `1_du_lieu_chinh/vn_labor_news_dataset.csv` làm đầu vào chuẩn. Không dùng Excel để xử lý vì nội dung dài có thể bị cắt.
- Dữ liệu Collecting là raw, chỉ đọc. Không sửa hoặc ghi đè CSV, Excel, log hay báo cáo gốc; mọi kết quả mới lưu riêng trong `5_process/`.
- Dùng `article_id` để liên kết các đầu ra. Giữ riêng nhãn tự động và nhãn do người kiểm tra; không coi nhãn tự động là ground truth.
- Không tự điền `sentiment` khi đang trống. Không xóa bản ghi nghi trùng nếu chưa có quyết định và lý do được ghi log.
- Mỗi người bàn giao file cùng hướng dẫn chạy ngắn, kiểm tra đã làm, kết quả thực tế và vấn đề còn mở. Báo issue kèm bằng chứng, người phụ trách và bước xử lý tiếp theo.
- Không đưa toàn văn bài báo lên nơi công khai hoặc vào slide công khai.

## Phân công

### Người 1 — Trưởng nhóm, schema và tích hợp

**Cần làm**
- Chốt schema, tên cột, đường dẫn và hợp đồng input/output giữa các module.
- Lập hồ sơ đầu vào: số dòng/cột, kiểu dữ liệu, giá trị thiếu, khoảng ngày, checksum và phiên bản chạy.
- Kiểm tra cột bắt buộc, ID/URL trùng, ngày, nguồn và nhãn; ghi lỗi vào issue log, không tự suy diễn hay âm thầm loại dòng.
- Tích hợp module của Người 2 và 3; chạy thử trên mẫu rồi chạy toàn bộ nếu kiểm thử đạt.
- Tổng hợp thay đổi, lỗi, số dòng trước/sau và hạn chế; nghiệm thu gói bàn giao.

**Bàn giao**
- `5_process/reports/00_input_profile.md` và `00_input_profile.json`
- `5_process/logs/issue_log.csv`
- `5_process/reports/process_quality_report.md`
- `5_process/README_PROCESS.md`
- Bản Process tích hợp và checklist nghiệm thu

**Hoàn thành khi**
- Đầu vào được nhận diện rõ; raw không thay đổi; pipeline tích hợp chạy được hoặc blocker được mô tả có bằng chứng.
- Báo cáo khớp với đầu ra và mọi lỗi/loại/đánh dấu đều có lý do truy vết.

### Người 2 — Metadata và audit trùng lặp

**Cần làm**
- Chuẩn hóa metadata trong các trường dẫn xuất: ngày, tên nguồn, khoảng trắng và URL so sánh.
- Giữ URL gốc; nếu tạo URL chuẩn hóa thì lưu ở cột riêng.
- Kiểm tra ID, URL chuẩn hóa, tiêu đề và các cặp nội dung nghi gần trùng.
- Chỉ lập danh sách để review; không tự xóa bản ghi trùng.

**Bàn giao**
- Module làm sạch metadata và dữ liệu metadata đầu ra riêng
- `5_process/reports/metadata_audit.md`
- `5_process/data/interim/duplicate_review.csv`
- Log các giá trị được chuẩn hóa và lỗi chưa xử lý

**Hoàn thành khi**
- Có thể chạy lại; trường gốc vẫn được giữ; mọi cặp nghi trùng có ID/URL và lý do để người phụ trách quyết định.

### Người 3 — Làm sạch văn bản

**Cần làm**
- Tạo `title_clean` và `content_clean` riêng; chuẩn hóa Unicode, khoảng trắng và ký tự điều khiển rõ ràng.
- Giữ nguyên dấu tiếng Việt, dấu câu, số liệu, tên riêng, thuật ngữ pháp lý và từ phủ định như “không”, “chưa”.
- Không viết đè `title` hoặc `content`; không xóa boilerplate nếu chưa có quy tắc kiểm tra được.
- Viết kiểm thử và ví dụ trước/sau, gồm tiếng Việt có dấu, số liệu, URL và nội dung dài.

**Bàn giao**
- Module text cleaning
- `5_process/data/processed/articles_text_clean.csv` (hoặc định dạng đã thống nhất)
- Test và `5_process/reports/text_cleaning_examples.md`

**Hoàn thành khi**
- Test đạt; trường gốc còn nguyên; đầu ra sạch có thể tái tạo và không làm mất nội dung quan trọng.

### Người 4 — Kiểm định nhãn và mức liên quan

**Cần làm**
- Viết hướng dẫn ngắn cho nhãn liên quan và 12 nhóm A–L.
- Chọn mẫu phân tầng, ưu tiên nhóm ít bài, bài có điểm liên quan thấp/khả năng nhiễu và `borderline_for_review.csv`.
- Ghi nhãn thủ công vào cột riêng: `relevance_manual`, `topic_manual`, `review_reason`, `reviewer_id`, `review_date`.
- Đưa ví dụ nhãn sai đã phát hiện vào mẫu kiểm tra; ghi nhận bất đồng và giới hạn của mẫu.
- Không sửa nhãn tự động hoặc gán sentiment trong dữ liệu gốc.

**Bàn giao**
- `5_process/config/labeling_guideline.md`
- `5_process/data/processed/manual_label_sample.csv`
- `5_process/reports/label_quality.md`

**Hoàn thành khi**
- Có quy tắc gán nhãn, mẫu có nguồn gốc rõ ràng và báo cáo nêu cách lấy mẫu, kết quả kiểm tra, bất đồng và giới hạn.

### Người 5 — Thống kê và bàn giao Modeling

**Cần làm**
- Tạo thống kê theo nguồn, năm/tháng, chủ đề, địa danh và độ dài văn bản; đối chiếu tổng số với CSV.
- Tạo các đặc trưng mô tả cơ bản và biểu đồ có thể sinh lại từ mã.
- Đề xuất chia tập theo thời gian cho bài toán dự đoán bài mới; kiểm tra trùng/chủ đề/nguồn giữa các tập trước khi tạo.
- Ghi rõ nhãn tự động là weak labels nếu dùng; tránh leakage từ ID, URL hoặc trường suy ra trực tiếp từ nhãn.
- Chỉ chuẩn bị dữ liệu cho Modeling; không huấn luyện mô hình trong phần việc này.

**Bàn giao**
- `5_process/reports/process_statistics.md` và biểu đồ/mã tạo biểu đồ
- `5_process/reports/handoff_to_modeling.md`
- Đề xuất split và kiểm tra leakage; các file split chỉ tạo khi đã thống nhất nhãn và quy tắc

**Hoàn thành khi**
- Số liệu khớp nguồn đầu vào; biểu đồ tái tạo được; handoff nêu rõ trường dùng, giới hạn nhãn và rủi ro leakage.

### Người 6 — Slide và trình bày

**Cần làm**
- Trình bày mục tiêu, nguồn dữ liệu, quy trình Collecting → Process, cách kiểm tra chất lượng và phân công.
- Chỉ dùng số liệu đã đối chiếu với Người 1/5; đánh dấu nội dung chưa chạy là kế hoạch, không trình bày như kết quả.
- Nêu giới hạn: nhãn tự động, sentiment chưa gán, địa danh chỉ là nơi được nhắc, dữ liệu báo chí không đại diện toàn xã hội.
- Dùng biểu đồ/tóm tắt, không đưa toàn văn bài báo lên slide công khai.

**Bàn giao**
- `presentation.pptx`
- Ghi chú thuyết trình và nguồn số liệu/hình ảnh
- PDF nếu nhóm cần

**Hoàn thành khi**
- Slide khớp báo cáo, có nguồn cho số liệu, mở được và không chứa kết quả chưa xác minh.

## Cách phối hợp và nghiệm thu chung

1. Mỗi thành viên bàn giao module độc lập cùng ví dụ chạy và các lỗi còn mở cho Người 1.
2. Người 1 kiểm tra tên cột/ID/đường dẫn trước khi tích hợp; Người 4 và Người 5 cung cấp kết quả để Người 6 cập nhật slide.
3. Nhóm review chéo: kiểm tra raw preservation, schema, log, khả năng chạy lại và độ khớp số liệu.
4. Chỉ nghiệm thu khi các file đầu ra mở được, có hướng dẫn, báo cáo nêu rõ hạn chế và không có thay đổi không truy vết.

## Phạm vi không làm

- Không huấn luyện hoặc tối ưu mô hình phức tạp trong giai đoạn Process.
- Không gán sentiment tự động khi chưa có hướng dẫn và nhãn kiểm định.
- Không tự loại bài vì bất thường hoặc nghi trùng.
- Không công bố lại toàn văn bài báo.

Tham khảo kế hoạch tổng thể tại [Ke_hoach_giai_doan_Process_VN_Labor_News_Dataset.md](./Ke_hoach_giai_doan_Process_VN_Labor_News_Dataset.md) và phân công trước tại [Phan_cong_6_nguoi_Process_HAN_27-10-2026.docx](./Phan_cong_6_nguoi_Process_HAN_27-10-2026.docx).
