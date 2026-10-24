# KẾ HOẠCH GIAI ĐOẠN PROCESS
## Dự án VN_Labor_News_Dataset – Khai thác tin tức việc làm, thất nghiệp và quyền lợi người lao động tại Việt Nam

**Phiên bản:** 1.0  
**Ngày lập:** 24/10/2026  
**Phạm vi:** Kế hoạch xử lý dữ liệu sau Collecting; chưa chạy pipeline Process trên toàn bộ dữ liệu.

---

## 1. Mục đích và vị trí của Process trong dự án

Dự án thu thập tin tức báo chí tiếng Việt về việc làm, thất nghiệp và quyền lợi người lao động tại Việt Nam. Giai đoạn Collecting đã tạo ra một bộ dữ liệu có bài báo thật và URL gốc để kiểm chứng. Giai đoạn Process sẽ biến dữ liệu đã thu thập thành dữ liệu **được kiểm tra, chuẩn hóa, có thể tái lập và phù hợp cho phân tích/mô hình hóa**.

Theo tinh thần CRISP-DM, Process ở đây tương ứng chủ yếu với **Data Preparation**: Data Cleaning, Data Transformation và Feature Engineering. Đây chưa phải giai đoạn huấn luyện mô hình. Modeling sẽ sử dụng các phiên bản dữ liệu đã được Process kiểm soát chất lượng.

### Mục tiêu đầu ra
1. Bảo toàn dữ liệu thu thập gốc để có thể truy nguyên.
2. Phát hiện và ghi nhận lỗi dữ liệu thay vì âm thầm xóa hoặc sửa.
3. Chuẩn hóa kiểu dữ liệu, văn bản tiếng Việt, ngày tháng, tên nguồn và địa danh.
4. Kiểm định nhãn chủ đề tự động và mức độ liên quan; tạo tập nhãn kiểm tra thủ công.
5. Tạo các bảng dữ liệu sạch phục vụ EDA, phân loại chủ đề, phân cụm/topic modeling và phân tích cảm xúc.
6. Sinh báo cáo chất lượng trước/sau Process cùng log, cấu hình và mã nguồn để người khác có thể chạy lại.

---

## 2. Hiện trạng Collecting đã kiểm tra

Từ gói `VN_Labor_News_Dataset.zip` và các báo cáo đi kèm:

- Bộ dữ liệu chính CSV có **12.784 dòng và 16 cột**.
- Khoảng thời gian `publish_date`: **2022-01-01 đến 2026-10-23**.
- Có 8 nguồn: VnEconomy, Thanh Niên, VietNamNet, Tuổi Trẻ, Sài Gòn Giải Phóng, Nhân Dân, Tiền Phong và Dân Trí.
- Trong lần kiểm tra trực tiếp CSV: `article_id` trùng 0; `source_url` trùng 0; `title` và `content` trống 0; cột `sentiment` trống 100%.
- Nội dung có độ dài trung vị khoảng **3.405 ký tự**; giá trị nhỏ nhất 310, lớn nhất 61.342 ký tự.
- Nhãn `topic_primary` gồm 12 nhóm A–L. Nhóm C (tiền lương, bảo hiểm, quyền lợi) chiếm 4.321 bài, khoảng 33,8%; nhóm J chỉ có 81 bài và nhóm L có 45 bài.
- Báo cáo Collecting nêu 304 bài ranh giới cần xem xét thủ công, 137 bản ghi bị loại do trùng lặp, và độ chính xác chủ đề/mức liên quan khi kiểm tra tay ước tính khoảng 85–90%.
- Tệp chính chỉ chứa `relevant_auto`; nhãn chủ đề được gán bằng luật/từ khóa, **không phải nhãn chuyên gia đã xác nhận**.

### Những rủi ro cần xử lý trong Process
1. **Nhãn sai do trùng từ khóa:** một bài thể thao có từ “sa thải” vẫn có thể được gán vào chủ đề lao động. Đây là ví dụ lỗi đã thấy trong mẫu dữ liệu, nên phải có bước rà soát nội dung thực tế, không chỉ dựa vào `relevance_score`.
2. **Mất cân bằng chủ đề:** nhóm C lớn hơn nhiều nhóm J/L. Accuracy đơn thuần sẽ không đủ để đánh giá mô hình phân loại.
3. **`sentiment` chưa có nhãn:** không được tự động coi là trung tính; phải giữ là chưa gán nhãn cho đến khi có quy trình gán nhãn.
4. **Địa danh:** trường `location` là địa danh được nhắc nhiều nhất, không nhất thiết là nơi sự kiện diễn ra. Báo cáo cũng ghi dùng tên tỉnh/thành trước đợt thay đổi địa giới năm 2025; cần lưu ý khi phân tích địa lý.
5. **Nội dung dài:** bản Excel có thể cắt nội dung do giới hạn ô; CSV là nguồn xử lý chính.
6. **Tính nhất quán báo cáo:** báo cáo thống kê và dữ liệu phải được tái sinh từ cùng một đầu vào phiên bản hóa, không sửa số liệu bằng tay.
7. **Bản quyền và diễn giải:** dữ liệu phục vụ học tập/nghiên cứu; không công bố lại toàn văn bài báo. Tin báo chí phản ánh cáo buộc không đồng nghĩa đã có kết luận vi phạm.

---

## 3. Nguyên tắc thiết kế

- **Không ghi đè raw:** dữ liệu gốc sau Collecting được giữ nguyên và chỉ đọc.
- **Mọi thay đổi có thể truy vết:** có log số dòng bị sửa, loại, gắn cờ và lý do.
- **Không xóa dữ liệu chỉ vì bất thường:** trước tiên đánh dấu để kiểm tra; chỉ loại khỏi tập phân tích khi có quy tắc và lý do rõ ràng.
- **Tách trường gốc và trường dẫn xuất:** ví dụ `content` giữ nguyên; tạo `content_clean`, `content_model` riêng.
- **Fit preprocessing trên train בלבד:** scaler, vectorizer, feature selection và các bước học từ dữ liệu phải fit trên tập train, rồi áp dụng sang validation/test để tránh leakage.
- **Không dùng dữ liệu test để lựa chọn mô hình hoặc chỉnh tham số.**
- **Giữ lại URL và ID để kiểm chứng**, nhưng không đưa URL/ID vào đặc trưng văn bản của mô hình.
- **Phân biệt dữ kiện với suy luận:** `topic_primary` là nhãn tự động; sentiment chưa có nhãn; `location` là địa danh được nhắc nhiều nhất.

---

## 4. Kiến trúc thư mục đề xuất cho Process

Giữ nguyên thư mục Collecting đã bàn giao. Tạo lớp Process riêng, không thay đổi các file gốc:

```text
VN_Labor_News_Dataset/
├── 00_DOC_TRUOC.md
├── 1_du_lieu_chinh/                 # đầu ra Collecting; không ghi đè
├── 2_thong_ke_bao_cao/              # báo cáo Collecting; giữ bản lịch sử
├── 3_du_lieu_phu/                   # log, mẫu QA, bài ranh giới
├── 4_ma_nguon/                      # mã Collecting hiện có
├── 5_process/
│   ├── README_PROCESS.md
│   ├── config/
│   │   ├── process_config.yaml
│   │   ├── topic_taxonomy.yaml
│   │   └── stopwords_vi.txt
│   ├── src/
│   │   ├── 01_profile_data.py
│   │   ├── 02_validate_schema.py
│   │   ├── 03_clean_metadata.py
│   │   ├── 04_clean_text.py
│   │   ├── 05_deduplicate_audit.py
│   │   ├── 06_prepare_labels.py
│   │   ├── 07_build_text_views.py
│   │   ├── 08_split_datasets.py
│   │   └── 09_generate_reports.py
│   ├── data/
│   │   ├── interim/
│   │   ├── processed/
│   │   └── splits/
│   ├── logs/
│   ├── reports/
│   └── tests/
└── 6_modeling/                       # giai đoạn kế tiếp, chưa triển khai trong Process
```

Nếu repository hiện tại có cấu trúc khác, hãy giữ nguyên cấu trúc đang hoạt động và ánh xạ các thành phần tương đương; không tạo thêm bản sao dữ liệu lớn không cần thiết.

### Quy ước phiên bản
Mỗi lần chạy cần ghi:
- thời gian chạy, phiên bản mã nguồn/commit nếu có;
- đường dẫn và SHA-256 của đầu vào;
- phiên bản Python và thư viện chính;
- cấu hình sử dụng;
- số dòng đầu vào, đầu ra, bị gắn cờ và bị loại theo từng lý do.

---

## 5. Quy trình Process chi tiết

### P0 — Đóng băng đầu vào và lập hồ sơ dữ liệu
**Việc làm**
- Chọn CSV làm nguồn dữ liệu chính; không dùng Excel làm đầu vào pipeline.
- Tính checksum SHA-256 cho CSV và các tệp phụ trợ.
- Ghi schema, số dòng/cột, kiểu dữ liệu, khoảng ngày, phân bố nguồn/chủ đề và tỷ lệ thiếu.
- Lưu profile vào `5_process/reports/00_input_profile.json` và bản đọc được `00_input_profile.md`.

**Đầu ra**
- Bản hồ sơ đầu vào có thể tái lập.
- Manifest ghi rõ file nào là dữ liệu chính, file nào là báo cáo/log phụ trợ.

**Điều kiện đạt**
- Có thể xác định chính xác đầu vào nào đã tạo ra mỗi bản Process.

### P1 — Kiểm tra schema và tính toàn vẹn
**Kiểm tra**
- Cột bắt buộc có đủ: `article_id`, `title`, `content`, `publish_date`, `source_name`, `source_url`, `topic_primary`, `relevance_status`.
- `article_id` duy nhất; URL chuẩn hóa không trùng; không có tiêu đề/nội dung rỗng hoặc chỉ chứa khoảng trắng.
- `publish_date` parse được và nằm trong khoảng dự án.
- `source_name` thuộc danh sách 8 nguồn đã công bố.
- `topic_primary` thuộc đúng 12 nhãn A–L.
- `relevance_status` đúng giá trị được quy định.
- `word_count` và `relevance_score` là số hợp lệ; đối chiếu `word_count` với cách đếm từ đã thống nhất.
- Kiểm tra URL hợp lệ về cú pháp; không cần tải lại toàn bộ bài ở bước này.

**Cách xử lý**
- Lỗi có thể sửa chắc chắn (ví dụ khoảng trắng đầu/cuối ở metadata) thì chuẩn hóa và ghi log.
- Lỗi không chắc chắn thì đưa vào `validation_issues.csv`, không tự suy diễn.
- Không tự động bỏ bài chỉ vì trường phụ như `topic_secondary` trống.

**Đầu ra**
- `interim/validated_records.parquet` hoặc CSV UTF-8.
- `reports/01_schema_validation.md`.
- `logs/validation_issues.csv`.

### P2 — Chuẩn hóa metadata
**Việc làm**
- Chuẩn hóa `source_name` theo từ điển nguồn thống nhất.
- Parse `publish_date` thành kiểu ngày ISO; tạo `publish_year`, `publish_month`, `publish_quarter`.
- Chuẩn hóa khoảng trắng và Unicode ở `title`, `location`, `matched_keywords`; không sửa nội dung câu chữ gốc.
- Chuẩn hóa URL để so sánh (ví dụ bỏ fragment, xử lý dấu `/` cuối) nhưng giữ nguyên `source_url` gốc; lưu thêm `source_url_normalized`.
- Chuẩn hóa giá trị thiếu thành null nhất quán; không biến `sentiment` trống thành “neutral”.
- Kiểm tra `collection_date` không sớm hơn ngày xuất bản nếu dữ liệu nguồn cho phép đối chiếu.

**Đầu ra**
- `interim/metadata_clean.parquet`.
- Báo cáo trước/sau về kiểu dữ liệu, giá trị thiếu và giá trị không hợp lệ.

### P3 — Làm sạch và tạo các phiên bản văn bản
Không nên chỉ tạo một cột “text đã làm sạch” dùng cho mọi mục tiêu. Cần giữ ít nhất ba lớp:

1. `content_raw`: nội dung nhận từ Collecting, không ghi đè.
2. `content_clean`: chuẩn hóa kỹ thuật như Unicode, khoảng trắng, xuống dòng, ký tự lỗi rõ ràng; giữ dấu tiếng Việt, dấu câu và ý nghĩa.
3. `text_model`: văn bản dành riêng cho một tác vụ mô hình cụ thể, có thể chuyển chữ thường, xử lý URL/ký hiệu và tách từ tùy mô hình.

**Quy trình**
- Chuẩn hóa Unicode về NFC; loại ký tự điều khiển không cần thiết.
- Chuẩn hóa khoảng trắng, xuống dòng và các chuỗi lặp vô nghĩa.
- Chỉ loại boilerplate rõ ràng như khối “tin liên quan”, chú thích ảnh hoặc quảng cáo nếu còn sót; lưu quy tắc và số lần áp dụng.
- Không xóa số, phần trăm, mốc thời gian, tên cơ quan, tên luật/nghị định hoặc các từ như “không”, “chưa”, “không được” vì chúng có thể đổi nghĩa của tin lao động.
- Giữ nguyên bản có dấu. Bản bỏ dấu chỉ nên là trường phụ nếu một thử nghiệm cụ thể chứng minh hữu ích.
- Tạo `title_clean`, `content_clean`, `text_title_content` (tiêu đề + nội dung) để có thể so sánh hiệu quả.
- Đếm lại độ dài ký tự/từ sau làm sạch; đánh dấu văn bản bất thường ngắn/dài thay vì tự động xóa.

**Tách từ tiếng Việt**
- Thử nghiệm tối thiểu hai phương án: TF-IDF theo từ/ký tự và tách từ tiếng Việt bằng một thư viện phù hợp như `underthesea` hoặc `pyvi`.
- Chốt phiên bản thư viện và từ điển stopword trong cấu hình.
- Không loại stopword mặc định một cách máy móc. Giữ phủ định, từ chỉ mức độ và từ pháp lý quan trọng.
- Với mô hình ngôn ngữ tiền huấn luyện như PhoBERT, dùng đúng tokenizer của mô hình, không dùng chuỗi đã xử lý theo pipeline TF-IDF.

**Đầu ra**
- `processed/articles_text_clean.parquet`.
- Báo cáo ví dụ trước/sau trên mẫu đại diện, gồm tiếng Việt có dấu, URL, số liệu, tên riêng và văn bản dài.

### P4 — Kiểm tra trùng lặp và nội dung gần trùng
Collecting đã khử trùng lặp; Process không được mặc định chạy lại rồi xóa thêm. Bước này là **audit**:
- Kiểm tra trùng `article_id`, URL chuẩn hóa, tiêu đề chuẩn hóa.
- Lấy mẫu các cặp nội dung gần giống bằng hash/độ tương đồng.
- Xem xét các bài cập nhật cùng sự kiện, bài đăng lại, bài có tiêu đề khác nhưng nội dung giống.
- Nếu phát hiện cặp nghi trùng mới, ghi vào `duplicates_review.csv`; người phụ trách quyết định giữ một hay cả hai tùy mục tiêu phân tích.
- Nếu giữ nhiều bài về cùng một sự kiện, cần lưu nhóm `duplicate_cluster_id`/`event_cluster_id` để tránh rò rỉ giữa train và test.

**Đầu ra**
- `reports/04_duplicate_audit.md`.
- `interim/duplicate_review.csv`.
- Không loại bài mới nếu chưa có quy tắc và log được duyệt.

### P5 — Kiểm định mức liên quan và nhãn chủ đề A–L
Đây là bước ưu tiên cao vì nhãn hiện tại được gán tự động theo từ khóa.

**Thiết kế kiểm tra thủ công**
- Tạo mẫu phân tầng theo `topic_primary`, `source_name`, năm và mức `relevance_score`; lấy thêm mẫu các bài có điểm thấp, bài ngắn/dài bất thường và bài có từ khóa dễ gây nhiễu.
- Dùng `borderline_for_review.csv` làm nguồn ưu tiên kiểm tra nếu có trong gói.
- Mỗi mẫu được người đánh giá gán:
  - `relevance_manual`: relevant / borderline / irrelevant;
  - `topic_manual`: một nhãn A–L hoặc multi-label nếu quy tắc đề tài cho phép;
  - `review_reason`: lý do ngắn;
  - `reviewer_id`, `review_date`.
- Viết hướng dẫn gán nhãn có định nghĩa và ví dụ cho 12 nhóm.
- Hai người gán nhãn độc lập trên một phần mẫu; đo tỷ lệ đồng thuận (và Cohen’s kappa nếu phù hợp), thảo luận bất đồng rồi chốt nhãn.
- Tính precision của bộ lọc liên quan và precision/recall theo từng nhóm trên tập kiểm tra đã gán nhãn. Không gọi tỷ lệ 85–90% là kết quả chắc chắn cho toàn bộ dữ liệu nếu mẫu đánh giá không đại diện.

**Xử lý nhãn**
- Giữ `topic_primary_auto`; không ghi đè nhãn gốc.
- Tạo `topic_primary_final` chỉ sau khi quy tắc sửa nhãn được duyệt.
- Tạo `relevance_final` tương tự.
- Không dùng `sentiment` cho mô hình khi chưa có nhãn đáng tin cậy.

**Đầu ra**
- `data/processed/manual_label_sample.csv`.
- `config/labeling_guideline.md`.
- `reports/05_label_quality.md`.
- Bảng nhãn cuối có nguồn gốc rõ ràng: auto hay manual.

### P6 — Chuẩn hóa địa danh và trường thời gian
**Việc làm**
- Giữ nguyên `location` gốc.
- Tạo `location_normalized` theo từ điển alias, lưu phiên bản từ điển và ngày áp dụng.
- Vì tên tỉnh/thành và địa giới thay đổi, không tự động đổi tên lịch sử sang địa giới mới nếu chưa xác định mục tiêu phân tích.
- Tách `location_type` (địa phương cụ thể / toàn quốc / không xác định) nếu cần.
- Lưu ý: `location` hiện phản ánh địa danh được nhắc nhiều nhất, không khẳng định địa điểm diễn ra sự kiện.
- Tạo biến thời gian từ `publish_date` như năm, tháng, quý; dùng để EDA và chia tập theo thời gian.

**Đầu ra**
- `processed/articles_metadata_clean.parquet`.
- `config/location_aliases.csv` và báo cáo các alias chưa xử lý.

### P7 — Feature Engineering theo mục tiêu, không trộn lẫn
Tạo đặc trưng theo từng nhánh; không đưa tất cả cột vào một mô hình.

**Nhánh EDA/thống kê**
- Năm, quý, tháng xuất bản.
- Nguồn báo.
- Chủ đề tự động và chủ đề đã kiểm định.
- Địa danh chuẩn hóa và loại địa danh.
- Độ dài tiêu đề/nội dung, số từ, số từ khóa, điểm liên quan.
- Tần suất từ/cụm từ theo thời gian và theo chủ đề.

**Nhánh phân loại chủ đề**
- Đầu vào văn bản: `title_clean`, `content_clean` hoặc kết hợp tiêu đề/nội dung.
- Baseline: TF-IDF word n-gram và character n-gram.
- Có thể so sánh với tách từ tiếng Việt và mô hình tiền huấn luyện ở giai đoạn Modeling.
- Không dùng `topic_primary_auto` làm đầu vào; đó là nhãn mục tiêu nếu bài toán là dự đoán chủ đề.

**Nhánh topic modeling/phân cụm**
- Tạo corpus riêng, lọc theo mục tiêu; ghi rõ cách lấy mẫu và tiền xử lý.
- So sánh các cấu hình thay vì tuyên bố một mô hình duy nhất là đúng.
- Đánh giá chủ đề bằng cả chỉ số phù hợp và đọc/diễn giải thủ công.

**Nhánh cảm xúc**
- Chưa triển khai mô hình sentiment khi `sentiment` trống 100%.
- Trước hết xác định định nghĩa nhãn phù hợp với tin lao động (ví dụ thái độ/đánh giá trong bài, không phải kết luận đúng-sai pháp lý), xây dựng hướng dẫn, gán nhãn một tập mẫu và kiểm tra độ đồng thuận.
- Không suy ra “bài tiêu cực” chỉ vì có từ “sa thải”, “nợ lương” hoặc “đình công”.

**Nhánh phân tích địa lý**
- Không coi `location` là nhãn địa điểm sự kiện nếu chưa xác minh. Phân tích địa phương cần nêu rõ hạn chế này.

### P8 — Chia tập dữ liệu an toàn cho Modeling
Không chia ngẫu nhiên mặc định cho mọi mục tiêu tin tức.

**Phân loại chủ đề**
- Nếu mục tiêu là dự đoán bài mới trong tương lai, ưu tiên chia theo thời gian: train giai đoạn trước, validation ở giai đoạn tiếp theo, test ở giai đoạn mới nhất.
- Có thể báo cáo thêm kết quả random stratified split để so sánh, nhưng không thay thế đánh giá theo thời gian.
- Gom các bản ghi cùng URL chuẩn hóa hoặc cùng cụm nội dung/sự kiện vào một partition để tránh rò rỉ.
- Chỉ dùng mẫu đã có nhãn được kiểm định làm tập đánh giá chính; nếu dùng nhãn tự động, phải ghi rõ đây là đánh giá so với nhãn yếu (weak labels).

**Nguyên tắc leakage**
- Vectorizer, tokenizer học từ dữ liệu, feature selection, scaler và bước chọn đặc trưng phải fit trên train.
- Validation dùng để chọn mô hình/siêu tham số; test chỉ dùng đánh giá cuối.
- Không dùng `sentiment` trống, `article_id`, URL hoặc trường được tạo trực tiếp từ nhãn làm đặc trưng dự đoán chủ đề.
- Lưu ID của từng tập để có thể tái tạo đúng phép chia.

**Đầu ra**
- `data/splits/train.csv`, `validation.csv`, `test.csv` hoặc các file ID tương ứng.
- `reports/08_split_audit.md`, gồm phân bố năm/nguồn/chủ đề, kiểm tra trùng chéo giữa tập.

### P9 — Báo cáo chất lượng sau Process
Báo cáo phải so sánh trước/sau và giải thích thay đổi:
- số dòng đầu vào, đầu ra, bị loại, bị gắn cờ;
- tỷ lệ thiếu theo cột;
- lỗi schema, ID/URL trùng, nội dung rỗng;
- phân bố nguồn, năm, chủ đề và địa danh;
- phân bố độ dài văn bản;
- kết quả kiểm tra nhãn thủ công;
- số bản ghi được chuẩn hóa, số cặp nghi trùng;
- các hạn chế còn lại và khuyến nghị sử dụng.

**Đầu ra**
- `reports/process_quality_report.md`.
- `reports/process_stats.json`.
- `logs/process_run.log`.
- Biểu đồ thống kê có mã tạo lại, không chỉ ảnh chụp.

---

## 6. Bảng kiểm soát đầu ra

| Tên đầu ra | Nội dung | Ai/việc sử dụng |
|---|---|---|
| `articles_metadata_clean.parquet` | Metadata chuẩn hóa, giữ các trường gốc | EDA, thống kê |
| `articles_text_clean.parquet` | Văn bản đã chuẩn hóa kỹ thuật | NLP |
| `manual_label_sample.csv` | Mẫu gán nhãn thủ công | Kiểm định nhãn |
| `articles_labeled.parquet` | Dữ liệu kèm nhãn auto và nhãn đã duyệt (nếu có) | Classification |
| `train/validation/test` | Các tập chia có ID truy vết | Modeling |
| `process_quality_report.md` | Báo cáo chất lượng trước/sau | Báo cáo dự án |
| `process_stats.json` | Chỉ số máy đọc được | Dashboard/biểu đồ |
| `process_run.log` | Nhật ký chạy | Tái lập, debug |
| `manifest.json` | Input hash, phiên bản, cấu hình, output hash | Kiểm toán pipeline |

Không nhất thiết phải lưu CSV và Parquet cho mọi trung gian. Parquet phù hợp cho xử lý nội bộ; CSV UTF-8 có thể được xuất cho người dùng Excel/Python khi cần.

---

## 7. Kế hoạch triển khai theo thứ tự ưu tiên

### Sprint 1 — Hồ sơ dữ liệu và kiểm định schema
- [ ] Đóng băng CSV đầu vào và tạo checksum.
- [ ] Viết profile dữ liệu tự động.
- [ ] Viết kiểm tra schema, ngày, ID, URL, nhãn và kiểu dữ liệu.
- [ ] Tạo báo cáo lỗi; chưa loại dữ liệu tự động ngoài quy tắc rõ ràng.

**Tiêu chí hoàn thành:** chạy lại cho cùng đầu vào tạo ra cùng thống kê; lỗi được ghi log.

### Sprint 2 — Làm sạch metadata và văn bản
- [ ] Chuẩn hóa ngày, nguồn, URL so sánh, Unicode và khoảng trắng.
- [ ] Tạo `content_clean` và `text_model` tách biệt.
- [ ] Kiểm tra mẫu trước/sau làm sạch.
- [ ] Viết unit test cho văn bản tiếng Việt, phủ định, số liệu, URL và nội dung dài.

**Tiêu chí hoàn thành:** không mất dấu tiếng Việt, không làm mất từ phủ định/số liệu quan trọng; bản gốc vẫn nguyên vẹn.

### Sprint 3 — Kiểm định nhãn và trùng lặp
- [ ] Audit trùng lặp lần hai, không xóa tự động.
- [ ] Thiết kế hướng dẫn gán nhãn A–L và liên quan.
- [ ] Lấy mẫu phân tầng; ưu tiên nhóm nhỏ và mẫu dễ nhiễu.
- [ ] Gán nhãn thủ công, đo đồng thuận và tạo báo cáo chất lượng nhãn.

**Tiêu chí hoàn thành:** có tập đánh giá thủ công và báo cáo chất lượng nhãn; không tuyên bố nhãn auto là ground truth.

### Sprint 4 — Đặc trưng, chia tập và bàn giao Modeling
- [ ] Tạo trường thời gian và địa danh chuẩn hóa.
- [ ] Tạo corpus riêng cho EDA, classification và topic modeling.
- [ ] Chia train/validation/test theo thời gian và kiểm tra trùng chéo.
- [ ] Sinh báo cáo chất lượng cuối, manifest và hướng dẫn chạy lại.

**Tiêu chí hoàn thành:** người khác có thể chạy Process từ CSV đầu vào và tái tạo các đầu ra đã công bố.

---

## 8. Kiểm thử bắt buộc

1. **Schema test:** thiếu cột bắt buộc phải báo lỗi rõ ràng.
2. **ID test:** ID trùng phải được báo, không tự chọn bản ghi để xóa.
3. **Date test:** ngày lỗi định dạng hoặc ngoài phạm vi phải được ghi vào issue log.
4. **Text test:** Unicode tiếng Việt được giữ nguyên; chuẩn hóa không xóa dấu, phủ định hoặc số liệu.
5. **Missing test:** `sentiment` trống được giữ là null, không tự gán neutral.
6. **Dedup test:** URL có/không có fragment được nhận diện trong bước audit, nhưng URL gốc vẫn giữ.
7. **Reproducibility test:** cùng input, config và seed cho cùng số dòng và cùng phép chia tập.
8. **Leakage test:** không có cùng URL/duplicate cluster ở nhiều partition; vectorizer không fit trên test.
9. **Report consistency test:** tổng số theo nhóm phải khớp tổng số bản ghi được báo cáo.
10. **No-overwrite test:** pipeline không ghi đè dữ liệu Collecting.

---

## 9. Chỉ số đánh giá chất lượng Process

Không đặt trước một tỷ lệ “đẹp” rồi chỉnh dữ liệu để đạt tỷ lệ đó. Báo cáo các chỉ số đo được:
- tỷ lệ hợp lệ schema;
- tỷ lệ thiếu theo cột;
- số ID/URL trùng;
- số văn bản bị gắn cờ theo độ dài;
- số bài được kiểm tra thủ công và cách lấy mẫu;
- precision/recall của lọc liên quan trên tập gán nhãn;
- precision/recall/F1 theo từng chủ đề trên tập nhãn đã kiểm định;
- mức đồng thuận giữa người gán nhãn;
- số bản ghi thay đổi và lý do thay đổi;
- tỷ lệ trùng chéo giữa train/validation/test (mục tiêu: 0 theo khóa/cụm trùng đã xác định).

Các chỉ số mô hình như Accuracy, Macro-F1, Weighted-F1 và confusion matrix thuộc Modeling; Process chỉ chuẩn bị dữ liệu và thiết kế cách đánh giá đáng tin cậy.

---

## 10. Ranh giới giữa Collecting, Process và Modeling

| Giai đoạn | Câu hỏi chính | Đầu vào | Đầu ra |
|---|---|---|---|
| Collecting (đã thực hiện) | Bài báo nào được phát hiện, tải và đưa vào bộ dữ liệu? | Sitemap, URL và trang báo công khai | Raw/metadata, bộ chính, log loại, log trùng, báo cáo thu thập |
| **Process (giai đoạn kế tiếp)** | Dữ liệu có đúng cấu trúc, sạch, nhất quán và nhãn có đáng tin không? | CSV chính + log/báo cáo Collecting | Dữ liệu chuẩn hóa, corpus NLP, nhãn kiểm định, split, báo cáo chất lượng |
| Modeling (sau Process) | Mô hình nào giải quyết được câu hỏi nghiên cứu? | Tập dữ liệu Process đã khóa phiên bản | Baseline, mô hình so sánh, chỉ số đánh giá, phân tích lỗi |
| Evaluation/Reporting | Kết quả có trả lời câu hỏi nghiên cứu và có giới hạn gì? | Kết quả mô hình + phân tích | Kết luận, biểu đồ, hạn chế, hướng phát triển |

---

## 11. Các câu hỏi nghiên cứu phù hợp sau Process

Chỉ chọn những câu hỏi mà dữ liệu hỗ trợ và nêu rõ giới hạn:
1. Tin tức về lao động được phân bố theo thời gian, nguồn báo và 12 nhóm chủ đề như thế nào?
2. Những chủ đề nào tăng/giảm theo tháng hoặc năm? Cần kiểm tra thay đổi nguồn và quy mô thu thập trước khi diễn giải là xu hướng xã hội.
3. Mô hình nào phân loại chủ đề tốt nhất trên tập nhãn đã kiểm định: TF-IDF + Logistic Regression/SVM hay mô hình ngôn ngữ tiếng Việt?
4. Có thể phát hiện các cụm chủ đề tiềm ẩn nào bằng topic modeling, và chuyên gia có diễn giải được chúng không?
5. Có thể phân tích cảm xúc/quan điểm trong tin lao động không, sau khi xây dựng hướng dẫn gán nhãn phù hợp?

Không nên kết luận trực tiếp về tỷ lệ thất nghiệp thực tế, số vụ vi phạm pháp luật hoặc mức độ phổ biến trong toàn xã hội chỉ từ số bài báo; đây là dữ liệu tin tức, chịu ảnh hưởng của lựa chọn biên tập và độ phủ nguồn.

---

## 12. Quy trình chạy và bàn giao

Đề xuất giao diện chạy thống nhất, ví dụ:

```powershell
# Từ thư mục gốc dự án
python -m 5_process.src.01_profile_data
python -m 5_process.src.02_validate_schema
python -m 5_process.src.03_clean_metadata
python -m 5_process.src.04_clean_text
python -m 5_process.src.05_deduplicate_audit
python -m 5_process.src.06_prepare_labels
python -m 5_process.src.07_build_text_views
python -m 5_process.src.08_split_datasets
python -m 5_process.src.09_generate_reports
```

Đây là **đề xuất tên bước**, chưa phải lệnh chạy được ngay. Khi triển khai cần chọn cách tổ chức package Python nhất quán (tên thư mục bắt đầu bằng số có thể gây bất tiện khi import), tạo `pyproject.toml` hoặc dùng các script entrypoint rõ ràng. Không chạy pipeline toàn bộ trước khi hoàn thành unit test và xác nhận cấu hình.

Bàn giao cuối Process gồm:
- mã nguồn và cấu hình;
- hướng dẫn cài môi trường;
- dữ liệu đầu ra và manifest;
- báo cáo chất lượng;
- hướng dẫn tái lập;
- danh sách vấn đề còn tồn tại;
- quyết định đã được người phụ trách duyệt về quy tắc loại/sửa/gán nhãn.

---

## 13. Kết luận và việc nên làm đầu tiên

Bộ Collecting đã có quy mô tốt cho một dự án Data Mining: 12.784 bài, 8 nguồn, có URL gốc, metadata, log loại/trùng và báo cáo chất lượng. Tuy nhiên, **điểm nghẽn lớn nhất trước Modeling không phải là thiếu thuật toán mà là độ tin cậy của nhãn tự động và cách tạo tập đánh giá**.

Thứ tự ưu tiên đề nghị:
1. Khóa đầu vào và tạo hồ sơ dữ liệu có checksum.
2. Kiểm định schema và tạo issue log.
3. Tạo bản văn bản sạch nhưng không ghi đè raw.
4. Kiểm tra thủ công có thiết kế đối với nhãn liên quan/chủ đề.
5. Chỉ sau đó mới chốt corpus và chia train/validation/test để Modeling.

Làm theo thứ tự này sẽ giúp dự án chứng minh được không chỉ rằng dữ liệu đã được thu thập, mà còn rằng quá trình xử lý minh bạch, có thể kiểm tra và có thể tái lập.
