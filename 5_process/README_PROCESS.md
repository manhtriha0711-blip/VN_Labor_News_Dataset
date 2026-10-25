# Process — cấu trúc và cách chạy

Thư mục này chứa đầu ra Process; dữ liệu Collecting trong `1_du_lieu_chinh/` chỉ đọc và không được ghi đè.

## Cấu trúc

- `src/`: module xử lý.
- `tests/`: unit tests.
- `config/`: hướng dẫn và quy ước gán nhãn.
- `data/processed/`: mẫu gán nhãn chờ người kiểm định.
- `data/interim/`: đầu ra trung gian, metadata đã chuẩn hóa và audit trùng.
- `logs/`: change log, issue log và lỗi metadata.
- `reports/`: báo cáo rà soát, audit metadata và chất lượng nhãn.

## Profile, schema và metadata

Môi trường hiện dùng Python 3.11 và pandas 3.0.2. Các lệnh dưới đây cần `pandas`; module metadata cần thêm `scikit-learn` và `pyarrow` để audit gần trùng và ghi Parquet. Cài các gói này trong môi trường Python của dự án nếu chưa có.

Từ thư mục gốc repository, chạy:

```powershell
python 5_process/src/01_profile_data.py
python 5_process/src/02_validate_schema.py
python 5_process/src/03_clean_metadata.py
```

Hai bước đầu tạo profile và kiểm tra schema từ `1_du_lieu_chinh/vn_labor_news_dataset.csv`. Module metadata cũng đọc CSV đó ở chế độ chỉ đọc, kiểm tra SHA-256 trước/sau và không loại bản ghi nghi trùng. Kết quả được ghi vào `reports/`, `logs/` và `data/interim/`.

Issue dùng chung của nhóm nằm ở `logs/issue_log.csv`; `reports/process_quality_report.md` là báo cáo tích hợp tiến độ, chưa phải nghiệm thu cuối.

Chạy unit tests:

```powershell
python -m unittest discover -s 5_process/tests -p "test_*.py" -v
```

## Trạng thái dữ liệu nhãn

`data/processed/manual_label_sample.csv` là mẫu để kiểm định. Chỉ xem là nhãn thủ công chính thức sau khi người kiểm định đọc và xác nhận từng dòng, điền người/ngày review và cập nhật báo cáo. `reports/label_quality.md` hiện là bản sơ bộ có hỗ trợ AI, chưa phải kết quả đã xác nhận.

Các file mẫu nhãn có chứa nội dung bài báo. Không đưa chúng hoặc dữ liệu toàn văn lên repository công khai.
