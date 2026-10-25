# Báo cáo sơ bộ kiểm định chất lượng nhãn

**Trạng thái:** Bản đánh giá sơ bộ có hỗ trợ AI, chưa phải xác nhận cuối
cùng của người kiểm định.\
**Ngày lập bản nháp:** 2026-10-25\
**Nguồn mẫu:** `3_du_lieu_phu/borderline_for_review.csv`\
**File đầu ra:** `manual_label_sample_ai_preliminary.csv`

## 1. Phạm vi

-   Số bài trong mẫu: **56**
-   Số chủ đề gốc được đại diện: **12**
-   Các nhãn thủ công đề xuất được điền vào các cột riêng; các cột gốc
    được giữ nguyên.
-   Mẫu này được chọn từ danh sách `borderline_auto`, nên không đại diện
    thống kê cho toàn bộ dataset 12.784 bài.

## 2. Phân bố nhãn liên quan sơ bộ

-   **Relevant:** 12 bài`\n`{=tex}- **Borderline:** 13 bài`\n`{=tex}-
    **Not relevant:** 31 bài`\n`{=tex}- **Uncertain:** 0 bài`\n`{=tex}
    \## 3. Nhận xét chính

-   Một số bài có chủ đề gốc không khớp rõ với nội dung bài, đặc biệt
    các bài về nhà ở xã hội, thuế nói chung, hoạt động nghi lễ/chính
    trị, hoặc tin doanh nghiệp không bàn về việc làm.

-   Các bài về thiếu hụt nhân lực, biên chế, hợp đồng với người nghỉ
    hưu, tuổi nghỉ hưu và sức khỏe tâm thần liên quan công việc có vẻ
    phù hợp hơn với phạm vi lao động.

-   Nhóm bài về khu công nghiệp và phát triển kinh tế thường chỉ liên hệ
    gián tiếp với việc làm; cần tiêu chí thống nhất về việc có giữ các
    bài chỉ nói đến tác động kinh tế tiềm năng hay không.

-   Nhãn `Not relevant` đi kèm
    `topic_manual = Không áp dụng - ngoài phạm vi lao động` để thể hiện
    rằng chủ đề A--L không nên gán cho bài ngoài phạm vi. Nếu schema nội
    bộ yêu cầu topic_manual chỉ nhận mã A--L, hãy đổi quy ước này trước
    khi nhập chính thức.

## 4. Các trường hợp Borderline cần ưu tiên hội ý

-   `VNLAB-B00076` --- HUFLIT đạt chuẩn kiểm định chất lượng cơ sở giáo
    dục chu kỳ 2 (nhãn gốc: A - Thị trường lao động Việt Nam; chủ đề đề
    xuất: A - Thị trường lao động Việt Nam)`\n`{=tex}- `VNLAB-B00197`
    --- Chuyển đổi số khu vực công: Khi hạ tầng cũ, nhân lực yếu cản
    bước tiến số hóa (nhãn gốc: B - Thất nghiệp, mất việc, cắt giảm nhân
    sự; chủ đề đề xuất: A - Thị trường lao động Việt Nam)`\n`{=tex}-
    `VNLAB-B00001` --- Cà Mau có 300 cán bộ y tế nghỉ hưu và tình nguyện
    viên hỗ trợ điều trị F0 tại nhà (nhãn gốc: D - Hợp đồng lao động,
    nghỉ việc, sa thải; chủ đề đề xuất: D - Hợp đồng lao động, nghỉ
    việc, sa thải)`\n`{=tex}- `VNLAB-B00023` --- Sơn La tôn vinh trí
    thức tiêu biểu, điển hình lao động sáng tạo (nhãn gốc: F - Công
    đoàn, đình công, tranh chấp lao động; chủ đề đề xuất: L - Tâm lý
    người lao động, chất lượng việc làm)`\n`{=tex}- `VNLAB-B00016` ---
    Thu hút đầu tư vào các khu công nghiệp (nhãn gốc: F - Công đoàn,
    đình công, tranh chấp lao động; chủ đề đề xuất: J - Kinh tế và yếu
    tố tác động đến việc làm)`\n`{=tex}- `VNLAB-B00031` --- Những khoảnh
    khắc '5 sao' của các bác tài xe công nghệ (nhãn gốc: G - Nhóm lao
    động dễ bị ảnh hưởng; chủ đề đề xuất: G - Nhóm lao động dễ bị ảnh
    hưởng)`\n`{=tex}- `VNLAB-B00138` --- Phụ nữ và trẻ em Thải Giàng
    Phố: Từ tăng cường vai trò, tiếng nói đến cải thiện thu nhập gia
    đình (nhãn gốc: H - Chính sách việc làm, đào tạo nghề, an sinh xã
    hội; chủ đề đề xuất: G - Nhóm lao động dễ bị ảnh hưởng)`\n`{=tex}-
    `VNLAB-B00155` --- Hà Nam trao giấy phép Đầu tư Dự án xây dựng kết
    cấu hạ tầng Khu Công nghiệp Đồng Văn VI (nhãn gốc: H - Chính sách
    việc làm, đào tạo nghề, an sinh xã hội; chủ đề đề xuất: J - Kinh tế
    và yếu tố tác động đến việc làm)`\n`{=tex}- `VNLAB-B00261` --- Thái
    Nguyên: Chính thức khởi công Khu công nghiệp Thanh Bình Giai đoạn II
    (nhãn gốc: J - Kinh tế và yếu tố tác động đến việc làm; chủ đề đề
    xuất: J - Kinh tế và yếu tố tác động đến việc làm)`\n`{=tex}-
    `VNLAB-B00213` --- Khu công nghiệp thu hút đầu tư, phát triển kinh
    tế địa phương (nhãn gốc: J - Kinh tế và yếu tố tác động đến việc
    làm; chủ đề đề xuất: J - Kinh tế và yếu tố tác động đến việc
    làm)`\n`{=tex}- `VNLAB-B00108` --- Bắc Ninh: Thành lập chi bộ đảng
    đầu tiên trong doanh nghiệp tư nhân tại khu công nghiệp (nhãn gốc:
    J - Kinh tế và yếu tố tác động đến việc làm; chủ đề đề xuất: J -
    Kinh tế và yếu tố tác động đến việc làm)`\n`{=tex}- `VNLAB-B00037`
    --- Đột phá từ chuyển dịch cơ cấu công nghiệp chế biến, chế tạo
    (nhãn gốc: J - Kinh tế và yếu tố tác động đến việc làm; chủ đề đề
    xuất: J - Kinh tế và yếu tố tác động đến việc làm)`\n`{=tex}-
    `VNLAB-B00064` --- Nhiều "nghịch lý" cho thấy nền kinh tế khô hạn,
    doanh nghiệp kiệt sức (nhãn gốc: L - Tâm lý người lao động, chất
    lượng việc làm; chủ đề đề xuất: J - Kinh tế và yếu tố tác động đến
    việc làm)`\n`{=tex} \## 5. Giới hạn

-   Đây là đánh giá sơ bộ do AI hỗ trợ dựa trên tiêu đề và nội dung có
    trong file; cần người kiểm định đọc và xác nhận từng bài.

-   Chưa có bộ quy tắc chính thức hoặc nhãn chuẩn đối chiếu để tính độ
    chính xác, precision/recall, Cohen's kappa hay mức đồng thuận giữa
    người gán nhãn.

-   Kết quả từ mẫu 56 bài không thể suy rộng trực tiếp ra toàn bộ dữ
    liệu.

-   Trước khi chốt báo cáo, cần xác nhận tiêu chí ranh giới giữa
    Relevant và Borderline, cũng như việc các chủ đề A--L có bắt buộc
    gán cho mọi bài hay không.

## 6. Bước tiếp theo

1.  Người kiểm định rà soát từng dòng và sửa các đề xuất chưa đồng ý.
2.  Thay `reviewer_id = AI_preliminary_review` bằng mã người kiểm định
    thật sau khi họ xác nhận từng dòng; cập nhật `review_date` theo ngày
    xác nhận.
3.  Sau khi được người kiểm định xác nhận, lưu bản chính thức thành
    `5_process/data/processed/manual_label_sample.csv`.
4.  Cập nhật báo cáo này bằng số liệu đã xác nhận và ví dụ sai nhãn thực
    tế.
