# Đọc trước — VN Labor News Dataset

Trang này là lối vào nhanh cho dự án. Nếu chưa chắc nên mở file nào, bắt đầu từ bảng dưới đây.

## Mở file phù hợp

| Mục đích | File nên mở |
|---|---|
| Xem trạng thái Process mới nhất | `5_process/reports/process_quality_report.md` |
| Chạy pipeline, xem hướng dẫn và vị trí đầu ra | `5_process/README_PROCESS.md` |
| Đọc dữ liệu chuẩn bằng Python | `1_du_lieu_chinh/vn_labor_news_dataset.csv` |
| Xem thử một phần dữ liệu | `1_du_lieu_chinh/xem_nhanh_200_bai.xlsx` |
| Xem thống kê và báo cáo của giai đoạn trước | `2_thong_ke_bao_cao/` |
| Chuẩn bị làm slide Người 6 | `Phan_cong_Process_6_nguoi.md` và `5_process/reports/process_quality_report.md` |
| Thực hiện review nhãn | `5_process/config/labeling_guideline.md` và `5_process/data/processed/manual_label_sample.csv` |
| Kiểm tra split/leakage trước Modeling | `5_process/reports/handoff_to_modeling.md` |
| Xem phân công nhóm | `Phan_cong_Process_6_nguoi.md` |

Không mở các file CSV trung gian, biểu đồ hay manifest nếu chỉ cần xem tóm tắt; mở báo cáo tương ứng trong `5_process/reports/` trước.

## Trạng thái hiện tại

- Dữ liệu chuẩn có 12.784 dòng và 16 cột; CSV là nguồn xử lý chính. Không ghi đè dữ liệu nguồn.
- Các kiểm tra Process gần nhất: 45/45 test Process, 7/7 test gốc và integration validation PASS.
- Phần slide của Người 6 chưa nằm trong đợt tích hợp này; có thể bắt đầu từ báo cáo chất lượng và thống kê đã kiểm tra.
- Mẫu review có 57 dòng, nhưng **0/57 nhãn được người thật xác nhận**. Đây vẫn là phần cần hoàn tất; không dùng nhãn AI thay thế.
- Có 65 ID thuộc các ứng viên/cụm giao split đã biết được đánh dấu `review_hold`; loại chúng khỏi modeling cho đến khi có quyết định phù hợp.
- Process chưa huấn luyện mô hình. Xem báo cáo chất lượng và handoff trước khi bắt đầu Modeling.

## Bố cục thư mục gốc

- `1_du_lieu_chinh/` — dữ liệu nguồn và file xem mẫu. Khi xử lý, dùng CSV; workbook chỉ để xem.
- `2_thong_ke_bao_cao/` — báo cáo/thống kê từ giai đoạn trước Process.
- `3_du_lieu_phu/` — các file phụ trợ của giai đoạn trước. Không mặc định xem chúng là nguồn chuẩn Process; riêng pool review cũ có vấn đề provenance được ghi tại `5_process/logs/issue_log.csv` (`ISS-008`).
- `4_ma_nguon/` — mã dùng ở giai đoạn thu thập và tạo dữ liệu.
- `5_process/` — mã, kiểm thử, cấu hình, logs, dữ liệu dẫn xuất, manifests và báo cáo của giai đoạn Process.

## Quy tắc an toàn dữ liệu

- CSV chuẩn và nội dung bài báo thuộc bản quyền các tòa soạn. Không đưa dữ liệu toàn văn lên nơi công khai.
- `5_process/data/processed/articles_text_clean.csv` là đầu ra lớn chứa toàn văn; không mở nếu không cần và không commit.
- `manual_label_sample.csv` chứa nội dung bài báo. Chỉ điền nhãn thủ công sau khi người review đọc và xác nhận; giữ các cột nguồn bất biến.
- `topic_primary` là nhãn tự động (weak label), không phải nhãn vàng. `sentiment` chưa được gán.
