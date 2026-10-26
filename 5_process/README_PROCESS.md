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
- `reference/person5_source_workbooks/`: workbook bàn giao gốc của Người 5, chỉ lưu để tham chiếu; không dùng làm đầu vào xử lý.
- `splits/`: manifest phân chia dữ liệu theo thời gian, chỉ gồm ID và metadata audit.

## Cài đặt và chạy pipeline Process

Cài dependency thống nhất cho các bước Process (nếu môi trường chưa có):

```powershell
python -m pip install -r 5_process/requirements.txt
```

Từ thư mục gốc repository, chạy từng lệnh riêng theo thứ tự. Kiểm thử đơn vị là bước đầu; chỉ chạy pipeline toàn bộ khi tests đạt. Nếu lệnh nào báo lỗi, dừng ở bước đó, xử lý lỗi rồi mới chạy tiếp:

```powershell
python -m unittest discover -s 5_process/tests -p "test_*.py" -v
python -m unittest test_text_cleaning -v
```

```powershell
python 5_process/src/01_profile_data.py
```

```powershell
python 5_process/src/02_validate_schema.py
```

```powershell
python 5_process/src/03_clean_metadata.py
```

```powershell
python 5_process/src/text_cleaning.py
```

```powershell
python 5_process/src/create_splits_and_leakage_audit.py
```

```powershell
python 5_process/src/validate_process_integration.py
```

```powershell
python 5_process/src/create_manual_label_sample.py
python 5_process/src/validate_manual_labels.py
```

```powershell
python 5_process/src/create_process_presentation.py
```

`01_profile_data.py` lập hồ sơ đầu vào; `02_validate_schema.py` xác thực schema và ghi issue. Các bước sau đều đọc CSV chuẩn `1_du_lieu_chinh/vn_labor_news_dataset.csv`; không xử lý từ Excel và không ghi đè dữ liệu Collecting.

`validate_process_integration.py` đối chiếu SHA-256, số dòng/ID giữa raw và các đầu ra metadata, text cleaning và split; kiểm tra trường raw được giữ nguyên trong CSV làm sạch và các cột `_clean` khớp hàm làm sạch. Kết quả được lưu tại `reports/integration_validation.json`. Nếu một bước trả mã lỗi khác 0, dừng pipeline và xử lý lỗi trước khi chạy tiếp.

Issue dùng chung của nhóm nằm ở `logs/issue_log.csv`; `reports/process_quality_report.md` và `reports/integration_checklist.md` là trạng thái tích hợp mới nhất. Báo cáo phân biệt rõ phần nghiệm thu kỹ thuật của Người 1 với các review thủ công còn chờ.

## Metadata và audit trùng lặp

Chạy lại từ CSV nguồn chỉ đọc:

```powershell
python 5_process/src/03_clean_metadata.py
```

Module sinh `data/interim/metadata_clean.parquet`/`.csv`, `data/interim/duplicate_review.csv`, các log metadata và `reports/metadata_audit.md`. Bản nguồn từ Người 2 được tích hợp cùng test; các output metadata được tái tạo từ CSV dự án để bảo đảm chúng khớp với code hiện tại.

Các quyết định trong `config/duplicate_decisions.csv` và `config/outlier_review.csv` chỉ chứa kết luận đã được người phụ trách xác nhận; module kiểm tra reviewer, schema, nhãn hợp lệ và khóa review trước khi áp dụng. Các bản nháp AI trong `config/review_drafts/` và `reports/review_drafts/` chỉ là tài liệu tham khảo, không được pipeline tự động nạp, không thay thế xác nhận của người review và không được dùng để loại bài. Công việc audit của Người 2 đã hoàn tất; xem kết quả và giới hạn trong `reports/metadata_audit.md`.

## Thống kê, split và bàn giao Modeling

Từ thư mục gốc, sinh lại thống kê, biểu đồ, manifest theo thời gian và audit ứng viên trùng:

```powershell
python 5_process/src/create_splits_and_leakage_audit.py
```

Lệnh đọc CSV nguồn ở chế độ chỉ đọc, kiểm tra schema/ID/ngày, và tạo `reports/process_statistics.md`, biểu đồ trong `reports/charts/`, các manifest trong `splits/`, `reports/split_validation.md` và `reports/handoff_to_modeling.md`. Mặc định train là trước 2025, validation là năm 2025, test từ 2026. Đây là lựa chọn mặc định để bàn giao, không phải xác nhận cuối của nhóm.

`topic_primary` là weak label tự động, không phải nhãn vàng. `split_manifest.csv` giữ nguyên mốc ngày để audit; script bổ sung `modeling_eligibility_manifest.csv`, gắn các bản ghi thuộc cặp/cụm đã biết giao split thành `review_hold` để chúng không đi vào train/evaluation trước khi được rà soát. Đây là heuristic, không chứng minh không còn leakage. Không huấn luyện mô hình trong bước này. Xem `reports/handoff_to_modeling.md` và `reports/split_validation.md` trước khi dùng manifest.

`create_process_presentation.py` tạo `reports/presentation.pptx` cùng ghi chú thuyết trình `reports/presentation_notes.md` từ các báo cáo đã xác minh và biểu đồ sinh lại được. Slide không đưa tiêu đề hoặc toàn văn bài báo.

## Làm sạch văn bản

Tạo `5_process/data/processed/articles_text_clean.csv`:

```powershell
python 5_process/src/text_cleaning.py
```

Module thêm `title_clean` và `content_clean`, giữ nguyên các cột gốc và không chỉnh sửa CSV nguồn. Văn bản được chuẩn hóa Unicode NFC; khoảng trắng và ký tự điều khiển được xử lý nhất quán. Zero-width space, BOM nằm trong văn bản và word joiner được đổi thành dấu cách; soft hyphen và các ký tự định dạng vô hình khác được bỏ. ZWJ/ZWNJ được giữ để không phá các cụm chữ hoặc emoji cần ký tự nối. Nếu CSV sai số trường, module báo lỗi và không thay thế đầu ra hiện có.

CSV đầu ra chứa toàn văn bài báo có bản quyền; không commit hoặc đẩy file này lên repository công khai. Tái tạo file khi cần từ CSV nguồn nội bộ.

## Trạng thái dữ liệu nhãn

`config/labeling_guideline.md` định nghĩa nhãn liên quan và các chủ đề A–L. Chạy `create_manual_label_sample.py` để tái tạo mẫu 57 dòng trực tiếp từ authoritative CSV: 56 dòng phân tầng theo `topic_primary` bằng thứ tự SHA-256 của `article_id` và một ví dụ ưu tiên `VNLAB-000002`. File `borderline_for_review.csv` không khớp authoritative dataset và không được dùng làm nguồn mẫu (`ISS-008`). Các trường gợi ý AI được để trống; chỉ người thật đọc và điền đủ `relevance_manual`, `topic_manual`, `review_reason`, `reviewer_id` và `review_date` mới được tính là đã review. Xem trạng thái và nguồn mẫu tại `reports/label_quality.md`.

Các CSV review chứa toàn văn bài báo nên được giữ cục bộ, không commit hoặc đưa lên repository công khai. `.gitignore` đã loại `manual_label_sample*.csv` khỏi Git.

Kiểm tra nguồn gốc, trường gốc, danh mục nhãn và trạng thái review:

```powershell
python 5_process/src/create_manual_label_sample.py
python 5_process/src/validate_manual_labels.py
```

Validator đối chiếu từng trường nguồn với authoritative CSV, kiểm tra quota phân tầng và báo số dòng còn chờ. Sau khi người kiểm định điền đủ mẫu, yêu cầu kiểm tra hoàn tất:

```powershell
python 5_process/src/validate_manual_labels.py --require-complete
```

Các file mẫu nhãn có chứa nội dung bài báo. Không đưa chúng hoặc dữ liệu toàn văn lên repository công khai.
