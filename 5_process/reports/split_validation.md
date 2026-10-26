# Split validation and leakage audit

## Quy tắc áp dụng

- Train: ngày đăng trước 2025-01-01 (2022–2024).
- Validation: 2025-01-01 đến 2025-12-31.
- Test: từ 2026-01-01 đến ngày cuối dữ liệu.
- Nhãn mục tiêu mặc định: `topic_primary`, phải được hiểu là **weak labels** tự động, chưa phải nhãn vàng.
- Đây là split mặc định được tạo để hoàn thiện bàn giao theo yêu cầu; nếu nhóm thay đổi nhãn hoặc mốc thời gian, cần tái sinh manifest.

## Kết quả kiểm tra

- CSV: 12,784 dòng; manifest: 12,784 dòng; tổng số dòng trong 3 split = 12,784.
- **train**: 8,213 bài (64.2%), 2022-01-01 đến 2024-12-31.
- **validation**: 2,562 bài (20.0%), 2025-01-01 đến 2025-12-31.
- **test**: 2,009 bài (15.7%), 2026-01-01 đến 2026-10-23.
- ID trong manifest duy nhất: True. Không thiếu split: True.
- Ứng viên trùng gần theo tiêu đề: 118 cặp; trong đó 32 cặp khác split. Xem `near_duplicate_title_candidates.csv`.

- Cụm trong metadata audit hiện đi qua nhiều split: **2** cụm. Đây là cảnh báo leakage cần xử lý trước khi đánh giá cuối; xem bảng dưới.

| Cụm | Số bài | Split | Article IDs |
|---|---:|---|---|
| `DUP-0037` | 2 | train; validation | VNLAB-006489; VNLAB-009701 |
| `DUP-0059` | 4 | test; validation | VNLAB-010169; VNLAB-010170; VNLAB-010171; VNLAB-010777 |

- Để không dùng các bản ghi đã biết có rủi ro cross-split khi modeling, `modeling_eligibility_manifest.csv` chuyển **65** bản ghi liên quan sang `review_hold`; không xóa khỏi temporal manifest. Eligible counts: train 8,185, validation 2,544, test 1,990.

### Phân bố nhãn weak theo split

| Topic primary (weak label) | Train | Validation | Test |
|---|---:|---:|---:|
| A - Thị trường lao động Việt Nam | 1292 | 349 | 358 |
| B - Thất nghiệp, mất việc, cắt giảm nhân sự | 370 | 81 | 55 |
| C - Tiền lương, bảo hiểm, quyền lợi | 2878 | 804 | 639 |
| D - Hợp đồng lao động, nghỉ việc, sa thải | 578 | 328 | 115 |
| E - Điều kiện làm việc, an toàn lao động | 267 | 68 | 86 |
| F - Công đoàn, đình công, tranh chấp lao động | 1052 | 312 | 253 |
| G - Nhóm lao động dễ bị ảnh hưởng | 779 | 295 | 231 |
| H - Chính sách việc làm, đào tạo nghề, an sinh xã hội | 581 | 163 | 151 |
| I - Lừa đảo tuyển dụng, bóc lột lao động | 222 | 70 | 33 |
| J - Kinh tế và yếu tố tác động đến việc làm | 59 | 11 | 11 |
| K - Pháp luật lao động và thực thi | 110 | 74 | 64 |
| L - Tâm lý người lao động, chất lượng việc làm | 25 | 7 | 13 |

### Phân bố nguồn theo split

| Nguồn | Train | Validation | Test |
|---|---:|---:|---:|
| Dân Trí | 182 | 74 | 45 |
| Nhân Dân | 1213 | 198 | 234 |
| Sài Gòn Giải Phóng | 1049 | 373 | 300 |
| Thanh Niên | 1335 | 390 | 285 |
| Tiền Phong | 595 | 164 | 116 |
| Tuổi Trẻ | 1007 | 443 | 355 |
| VietNamNet | 1310 | 397 | 242 |
| VnEconomy | 1522 | 523 | 432 |

## Cảnh báo diễn giải

- Kiểm tra trùng gần chỉ là rà soát ứng viên theo tiêu đề với ngưỡng fuzzy ratio >= 90 trong các block tiêu đề; không phải kiểm định đầy đủ nội dung, không kết luận cặp nào chắc chắn trùng. Cần xem thủ công các cặp, đặc biệt cặp `cross_split=True`.
- `split_manifest.csv` giữ nguyên phân chia theo thời gian để audit. Khi modeling, dùng `modeling_eligibility_manifest.csv` và chỉ lấy `modeling_split` thuộc train/validation/test; các bản ghi thuộc candidate/cụm đã biết được giữ ở `review_hold`, không bị xóa. Rà soát thủ công trước khi đưa chúng trở lại.
- Rà soát tiêu đề theo block là heuristic không toàn diện; holdout này giảm rủi ro đã phát hiện nhưng không chứng minh không còn leakage.
- Chia theo thời gian mô phỏng dự đoán bài trong tương lai; phân bố chủ đề có thể lệch theo thời gian. Báo cáo macro-F1 và từng lớp, nhất là lớp hiếm.
- Khi `topic_primary` là target, tuyệt đối không đưa chính nó hoặc biến suy ra trực tiếp từ nó vào features. Không dùng `article_id`, `source_url`, `matched_keywords`, `topic_secondary`, `relevance_score`, `relevance_status`, `data_quality_note` hay `collection_date` làm feature mặc định.
- Không huấn luyện mô hình trong bước này. Các file split là manifest/metadata, không phải tập đặc trưng đã mã hóa.
