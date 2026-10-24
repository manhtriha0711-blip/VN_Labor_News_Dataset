# ĐỌC TRƯỚC – Bộ dữ liệu tin tức lao động Việt Nam

**12.784 bài báo tiếng Việt** về việc làm, thất nghiệp và quyền lợi người lao động tại Việt Nam,
đăng từ **01/01/2022 đến 23/10/2026**, lấy từ **8 báo**: VnEconomy, Thanh Niên, VietNamNet, Tuổi Trẻ,
Sài Gòn Giải Phóng, Nhân Dân, Tiền Phong, Dân Trí. Mỗi dòng là 1 bài báo thật, có link gốc để kiểm tra.

## Mở file nào?

| Muốn làm gì | Mở file |
|---|---|
| Xem thử dữ liệu trông thế nào | `1_du_lieu_chinh/xem_nhanh_200_bai.xlsx` (nhẹ, mở ngay) |
| **Xử lý bằng Python** | `1_du_lieu_chinh/vn_labor_news_dataset.csv` ← **dùng file này** |
| Xem toàn bộ bằng Excel | `1_du_lieu_chinh/vn_labor_news_dataset.xlsx` (17 MB, mở hơi lâu) |
| Xem số bài theo nguồn / năm / chủ đề | `2_thong_ke_bao_cao/thong_ke.xlsx` |
| Báo cáo chất lượng đầy đủ | `2_thong_ke_bao_cao/data_quality_report.md` |

Thư mục `3_du_lieu_phu` và `4_ma_nguon` chỉ cần khi muốn kiểm tra lại hoặc thu thập thêm.

## Đọc dữ liệu bằng Python

```python
import pandas as pd
df = pd.read_csv("1_du_lieu_chinh/vn_labor_news_dataset.csv")   # đã là UTF-8, không cần thêm encoding
print(df.shape)            # (12784, 16)
df["publish_date"] = pd.to_datetime(df["publish_date"])
```

> Không mở file CSV bằng Excel rồi bấm Lưu: Excel có thể làm hỏng dấu tiếng Việt và cắt nội dung dài.

## Các cột

| Cột | Ý nghĩa |
|---|---|
| `article_id` | Mã bài, ví dụ `VNLAB-000001` |
| `title` | Tiêu đề |
| `content` | Đoạn tóm tắt + toàn bộ nội dung bài (đã bỏ chú thích ảnh, quảng cáo, "tin liên quan") |
| `publish_date` | Ngày đăng (YYYY-MM-DD) |
| `source_name` | Tên báo |
| `source_url` | Link gốc của bài |
| `topic_primary` | Chủ đề chính, 1 trong 12 nhóm A–L (bảng dưới) |
| `topic_secondary` | Chủ đề phụ (có thể trống) |
| `matched_keywords` | Các từ khóa tìm thấy trong bài, cách nhau bởi `; ` |
| `location` | Tỉnh/thành được nhắc nhiều nhất (tối đa 3), hoặc "Toàn quốc/không xác định" |
| `sentiment` | **Đang trống**, chưa phân tích cảm xúc (việc của nhóm) |
| `relevance_status` | Luôn là `relevant_auto` trong file chính |
| `collection_date` | Ngày thu thập |
| `data_quality_note` | Ghi chú chất lượng (ví dụ: nội dung ngắn, bài có nêu cáo buộc vi phạm) |
| `relevance_score` | Điểm mức độ liên quan (càng cao càng đúng chủ đề) |
| `word_count` | Số từ của nội dung |

## 12 nhóm chủ đề

| Mã | Chủ đề | Số bài |
|---|---|---|
| A | Thị trường lao động Việt Nam | 1.999 |
| B | Thất nghiệp, mất việc, cắt giảm nhân sự | 506 |
| C | Tiền lương, bảo hiểm, quyền lợi | 4.321 |
| D | Hợp đồng lao động, nghỉ việc, sa thải | 1.021 |
| E | Điều kiện làm việc, an toàn lao động | 421 |
| F | Công đoàn, đình công, tranh chấp lao động | 1.617 |
| G | Nhóm lao động dễ bị ảnh hưởng | 1.305 |
| H | Chính sách việc làm, đào tạo nghề, an sinh xã hội | 895 |
| I | Lừa đảo tuyển dụng, bóc lột lao động | 325 |
| J | Kinh tế và yếu tố tác động đến việc làm | 81 |
| K | Pháp luật lao động và thực thi | 248 |
| L | Tâm lý người lao động, chất lượng việc làm | 45 |

## Lưu ý khi xử lý

1. **Chủ đề được gán tự động bằng từ khóa.** Kiểm tra tay thấy khoảng **85–90%** bài đúng chủ đề.
   Nếu dùng `topic_primary` làm nhãn để huấn luyện mô hình thì nên kiểm tra tay thêm.
2. **Lệch chủ đề:** nhóm C chiếm khoảng 1/3, còn nhóm J và L rất ít. Cần lưu ý khi làm phân loại
   (cân bằng lớp, hoặc gộp nhóm).
3. **Dân Trí chỉ chiếm khoảng 2%**, vì việc tải bị dừng sớm do máy chủ phản hồi chậm. Link Dân Trí có thể tạm không mở được.
4. Cột `sentiment` đang trống, chưa có nhãn cảm xúc.
5. Bài có chữ "nợ lương", "trốn đóng BHXH"… **không có nghĩa doanh nghiệp đã bị kết luận vi phạm**,
   chỉ là báo chí phản ánh.
6. Nội dung bài báo thuộc bản quyền các tòa soạn: chỉ dùng cho môn học, không đăng tải lại công khai.

## Gợi ý việc tiếp theo

- Tiền xử lý: tách từ tiếng Việt (`underthesea` hoặc `pyvi`), bỏ stopword, chữ thường.
- EDA: số bài theo tháng/năm, theo nguồn, theo chủ đề, theo tỉnh; từ khóa nổi bật theo từng năm.
- Mô hình: phân cụm / topic modeling (LDA, BERTopic), phân loại chủ đề (TF-IDF + SVM, PhoBERT),
  phân tích cảm xúc (gán nhãn tay một tập nhỏ trước).
