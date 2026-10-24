"""Bộ từ khóa theo 12 nhóm chủ đề (A–L) + quy tắc lọc liên quan.

Prompt gốc nhắc tới bộ từ khóa A–L "kèm theo" nhưng không đính kèm; bộ dưới đây được
xây dựng lại theo đúng 12 nhóm nội dung trong yêu cầu, kèm từ đồng nghĩa/biến thể.
Có thể thay thế danh sách trong TOPICS bằng bộ từ khóa gốc mà không phải sửa code khác.
"""
import re

from common import strip_accents

# Mã nhóm -> (tên nhóm, danh sách từ khóa có dấu, dùng để gán chủ đề & chấm điểm liên quan)
TOPICS = {
    "A": ("Thị trường lao động Việt Nam", [
        "thị trường lao động", "nguồn nhân lực", "thiếu lao động", "thiếu nhân lực", "thiếu công nhân",
        "nhu cầu tuyển dụng", "nhu cầu lao động", "lực lượng lao động", "tạo việc làm", "giải quyết việc làm",
        "cơ hội việc làm", "tìm việc", "tuyển dụng lao động", "cung ứng lao động", "dịch chuyển lao động",
        "tỷ lệ lao động", "chất lượng nguồn nhân lực", "lao động qua đào tạo"]),
    "B": ("Thất nghiệp, mất việc, cắt giảm nhân sự", [
        "thất nghiệp", "mất việc", "cắt giảm lao động", "cắt giảm nhân sự", "cắt giảm nhân viên",
        "cắt giảm công nhân", "giảm giờ làm", "ngừng việc", "nghỉ luân phiên", "giãn việc", "sa thải hàng loạt",
        "tinh giản biên chế", "tinh giản", "dôi dư", "không có việc làm", "thiếu việc làm", "nghỉ chờ việc",
        "cắt giảm việc làm", "giảm lao động"]),
    "C": ("Tiền lương, bảo hiểm, quyền lợi", [
        "tiền lương", "lương tối thiểu", "lương cơ sở", "tăng lương", "nợ lương", "chậm lương", "chậm trả lương",
        "trả lương", "thưởng Tết", "lương tháng 13", "bảo hiểm xã hội", "BHXH", "bảo hiểm thất nghiệp",
        "bảo hiểm y tế", "lương hưu", "hưu trí", "trợ cấp", "chậm đóng", "trốn đóng", "nợ đóng",
        "rút BHXH một lần", "rút bảo hiểm xã hội một lần", "cải cách tiền lương", "thu nhập bình quân",
        "thu nhập của người lao động", "phụ cấp", "chế độ thai sản", "quyền lợi người lao động"]),
    "D": ("Hợp đồng lao động, nghỉ việc, sa thải", [
        "hợp đồng lao động", "chấm dứt hợp đồng", "đơn phương chấm dứt", "sa thải", "nghỉ việc", "thôi việc",
        "trợ cấp thôi việc", "trợ cấp mất việc", "kỷ luật lao động", "thử việc", "nghỉ hưu", "tuổi nghỉ hưu",
        "nghỉ hưu trước tuổi", "nghỉ phép", "nghỉ ốm"]),
    "E": ("Điều kiện làm việc, an toàn lao động", [
        "an toàn lao động", "tai nạn lao động", "vệ sinh lao động", "bệnh nghề nghiệp", "điều kiện làm việc",
        "tăng ca", "làm thêm giờ", "giờ làm việc", "thời giờ làm việc", "môi trường làm việc", "bảo hộ lao động",
        "ngộ độc thực phẩm tại công ty", "suất ăn công nhân", "bữa ăn ca", "nhà trọ công nhân",
        "phòng trọ công nhân", "nhà ở cho công nhân", "nhà ở xã hội cho công nhân"]),
    "F": ("Công đoàn, đình công, tranh chấp lao động", [
        "công đoàn", "đình công", "ngừng việc tập thể", "tranh chấp lao động", "thương lượng tập thể",
        "thỏa ước lao động", "Tổng Liên đoàn Lao động", "Liên đoàn Lao động", "LĐLĐ", "đoàn viên",
        "tổ chức đại diện người lao động", "đối thoại tại nơi làm việc", "Tết Sum vầy", "Tháng Công nhân",
        "Mái ấm Công đoàn", "Chuyến xe Công đoàn"]),
    "G": ("Nhóm lao động dễ bị ảnh hưởng", [
        "lao động nữ", "lao động phổ thông", "lao động tự do", "lao động phi chính thức", "lao động di cư",
        "lao động nhập cư", "lao động lớn tuổi", "lao động trên 35 tuổi", "người khuyết tật", "lao động trẻ em",
        "lao động chưa thành niên", "shipper", "tài xế công nghệ", "xe ôm công nghệ", "giúp việc", "công nhân",
        "sinh viên mới ra trường", "lao động nông thôn", "lao động thời vụ", "người lao động nghèo",
        "lao động yếu thế", "lao động có hoàn cảnh khó khăn"]),
    "H": ("Chính sách việc làm, đào tạo nghề, an sinh xã hội", [
        "đào tạo nghề", "học nghề", "giáo dục nghề nghiệp", "an sinh xã hội", "hỗ trợ người lao động",
        "gói hỗ trợ", "chính sách việc làm", "trung tâm dịch vụ việc làm", "sàn giao dịch việc làm",
        "phiên giao dịch việc làm", "ngày hội việc làm", "vay vốn tạo việc làm", "chuyển đổi nghề",
        "xuất khẩu lao động", "đi làm việc ở nước ngoài", "lao động ở nước ngoài", "chương trình EPS",
        "thực tập sinh kỹ năng", "đào tạo lại", "nâng cao kỹ năng", "kỹ năng nghề"]),
    "I": ("Lừa đảo tuyển dụng, bóc lột lao động", [
        "lừa đảo tuyển dụng", "lừa đảo việc làm", "việc nhẹ lương cao", "bóc lột", "cưỡng bức lao động",
        "lao động cưỡng bức", "mua bán người", "lừa sang Campuchia", "môi giới lao động", "xuất cảnh trái phép",
        "lừa đi xuất khẩu lao động", "cộng tác viên online", "giả mạo nhà tuyển dụng", "tuyển dụng ảo",
        "lừa đảo xuất khẩu lao động", "đặt cọc việc làm", "phí tuyển dụng", "đi lao động", "lừa đảo",
        "chiếm đoạt"]),
    "J": ("Kinh tế và yếu tố tác động đến việc làm", [
        "đơn hàng giảm", "thiếu đơn hàng", "sụt giảm đơn hàng", "doanh nghiệp giải thể", "doanh nghiệp rút lui",
        "dệt may", "da giày", "khu công nghiệp", "doanh nghiệp FDI", "thuế đối ứng", "trí tuệ nhân tạo thay thế",
        "AI thay thế", "tự động hóa", "suy thoái", "phục hồi sản xuất", "lạm phát", "tăng trưởng kinh tế",
        "dịch chuyển chuỗi cung ứng"]),
    "K": ("Pháp luật lao động và thực thi", [
        "Bộ luật Lao động", "pháp luật lao động", "Luật Bảo hiểm xã hội", "Luật Việc làm", "Luật Công đoàn",
        "thanh tra lao động", "xử phạt vi phạm", "vi phạm pháp luật về lao động", "khởi kiện", "khởi tố",
        "tòa án", "hòa giải viên lao động", "Bộ LĐ-TB&XH", "Bộ Lao động - Thương binh và Xã hội",
        "Bộ Nội vụ", "nghị định", "thông tư", "có hiệu lực"]),
    "L": ("Tâm lý người lao động, chất lượng việc làm", [
        "áp lực công việc", "kiệt sức", "burnout", "nhảy việc", "sức khỏe tinh thần", "cân bằng công việc",
        "quiet quitting", "việc làm bền vững", "việc làm thỏa đáng", "chất lượng việc làm", "gắn bó với doanh nghiệp",
        "giữ chân người lao động", "hài lòng với công việc", "căng thẳng", "trầm cảm", "Gen Z", "dân văn phòng",
        "người đi làm"]),
}

# Từ khóa "neo" xác định bài thực sự nói về lao động/việc làm (từ chung như kinh tế, GDP, tên tỉnh chỉ là bổ trợ)
ANCHORS = ["người lao động", "lao động", "việc làm", "công nhân", "thất nghiệp", "tiền lương", "bảo hiểm xã hội",
           "BHXH", "công đoàn", "tuyển dụng", "nhân sự", "nhân viên", "sa thải", "nghỉ việc", "mất việc",
           "đình công", "lương", "NLĐ", "CNLĐ", "shipper", "tài xế công nghệ"]
# Các cụm có "lao động"/"lương" nhưng không mang nghĩa quan hệ lao động -> trừ khi đếm neo
ANCHOR_NOISE = ["Báo Lao Động", "Báo Người Lao Động", "Huân chương Lao động", "Anh hùng Lao động",
                "lao động sáng tạo", "chất lượng", "sản lượng", "năng lượng", "khối lượng", "lương thực",
                "trọng lượng", "lưu lượng", "dung lượng", "số lượng", "lượng", "thương binh", "Lương Cường",
                "Lương Tam Quang", "lao động khổ sai", "tù chung thân"]

# Mẫu slug (không dấu) để lọc nhanh URL ứng viên từ sitemap
SLUG_PATTERNS = [
    r"viec-lam", r"that-nghiep", r"mat-viec", r"cat-giam", r"sa-thai", r"nghi-viec", r"thoi-viec", r"ngung-viec",
    r"giam-gio-lam", r"nghi-luan-phien", r"gian-viec", r"tinh-gian", r"lao-dong", r"cong-nhan", r"cong-doan",
    r"dinh-cong", r"tien-luong", r"(?:tang|no|cham|tra|muc|bang|nhan|giam|cat|bi|mat|tru|om|khat|chi)-luong",
    r"luong-(?:toi-thieu|co-so|huu|thang|thuong|cong-nhan|giao-vien|nhan-vien|bac-si|y-te|cao|thap|tet|"
    r"trung-binh|binh-quan|khoi-diem|ky-su|cong-chuc|vien-chuc|tu|dong|thuc-te|net|gross|tran)",
    r"thu-nhap", r"thuong-tet", r"bhxh", r"bao-hiem-xa-hoi", r"bao-hiem-that-nghiep", r"tro-cap", r"huu-tri",
    r"nghi-huu", r"hop-dong-lao-dong", r"tang-ca", r"lam-them", r"tuyen-dung", r"ung-vien", r"nhan-luc",
    r"nhan-su", r"dao-tao-nghe", r"hoc-nghe", r"nghe-nghiep", r"an-sinh", r"xuat-khau-lao-dong",
    r"viec-nhe-luong-cao", r"boc-lot", r"cuong-buc", r"shipper", r"tai-xe-cong-nghe", r"xe-om-cong-nghe",
    r"giup-viec", r"kiet-suc", r"ap-luc-cong-viec", r"nhay-viec", r"di-lam", r"cong-so", r"van-phong",
    r"(?:no|cham|tron)-dong", r"nhan-vien", r"khu-cong-nghiep", r"tim-viec", r"xin-viec", r"thu-viec",
    r"bien-che", r"doi-du", r"nguoi-di-lam", r"nghe-(?:nghiep|moi)", r"eps", r"thuc-tap-sinh", r"nguoi-lam-thue",
    r"lam-thue", r"phong-tro", r"nha-o-xa-hoi", r"ngay-hoi-viec-lam", r"phien-giao-dich",
]
SLUG_RE = re.compile(r"(?:^|-)(?:" + "|".join(SLUG_PATTERNS) + r")(?:-|$)")

# Tiêu đề loại trừ: tuyển dụng/quảng cáo thông thường, thể thao
EXCLUDE_TITLE_RE = re.compile(
    r"^\s*\[?(?:tuyển dụng|thông báo tuyển dụng|tuyển gấp|tuyển sinh)\b|thông tin quảng cáo|nội dung tài trợ|"
    r"\b(?:cầu thủ|HLV|CLB|V-League|đội tuyển|Ngoại hạng Anh|chuyển nhượng|tiền đạo|tiền vệ|thủ môn|Champions League|"
    r"bóng đá|Cúp|Olympic|Red Bull|Huân chương Lao động|Anh hùng Lao động|Sao Khuê|vinh dự (?:đón )?nhận)\b|"
    r"^\s*(?:Tin tức|Tin nóng|Bản tin|Thời sự) (?:sáng|trưa|chiều|tối|đêm)\b",
    re.IGNORECASE)
EXCLUDE_BODY_MARKERS = ["Thông tin quảng cáo", "Nội dung được tài trợ", "Bài viết được tài trợ", "PR sponsored"]

# Dấu hiệu tin quốc tế (dùng để phát hiện tin nước ngoài không liên quan VN)
FOREIGN_RE = re.compile(
    r"\b(?:Mỹ|Trung Quốc|Nhật Bản|Hàn Quốc|châu Âu|EU|Anh|Pháp|Đức|Nga|Ukraine|Ấn Độ|Singapore|Thái Lan|Úc|"
    r"Canada|Indonesia|Malaysia|Philippines|Campuchia|Lào|Đài Loan|Hong Kong|Israel|Iran|Brazil|Argentina|"
    r"Australia|Mexico|Thổ Nhĩ Kỳ|Saudi|Trung Đông|thế giới|toàn cầu|Phố Wall|Fed|Silicon Valley|Apple|Google|"
    r"Amazon|Meta|Microsoft|Tesla|Samsung|Boeing|Starbucks|Intel|Nike)\b")
VIETNAM_RE = re.compile(r"Việt Nam|\bVN\b|người Việt|lao động Việt|TP\.?HCM|Hà Nội|Bộ LĐ-TB&XH|"
                        r"Tổng LĐLĐ|BHXH Việt Nam")


def slug_of(url):
    path = url.rstrip("/").rsplit("/", 1)[-1]
    path = re.sub(r"\.(?:html?|tpo|vov|aspx)$", "", path)
    return re.sub(r"-(?:post)?\d{6,}$", "", path).lower()


def slug_is_candidate(url, sm_title=""):
    s = slug_of(url)
    if sm_title:
        s = s + "-" + re.sub(r"[^a-z0-9]+", "-", strip_accents(sm_title).lower())
    return bool(SLUG_RE.search(s))


def _count(term, text_low):
    # đếm theo ranh giới từ, không phân biệt hoa thường; kiểm tra chuỗi con trước cho nhanh
    if term.lower() not in text_low:
        return 0
    return len(re.findall(r"(?<![\wÀ-ỹ])" + re.escape(term.lower()) + r"(?![\wÀ-ỹ])", text_low))


def anchor_count(text):
    low = text.lower()
    for n in ANCHOR_NOISE:
        low = low.replace(n.lower(), " ")
    return sum(_count(a, low) for a in ANCHORS)


def topic_hits(text):
    """Trả về {mã nhóm: [từ khóa khớp]} trên văn bản."""
    low = text.lower()
    hits = {}
    for code, (_, kws) in TOPICS.items():
        m = [k for k in kws if _count(k, low)]
        if m:
            hits[code] = m
    return hits


# Từ khóa của nhóm J/K/L mang tính bổ trợ: một mình chúng không đủ xác định bài phù hợp
WEAK_GROUPS = {"J", "K", "L"}
GENERIC_KW = {"công nhân", "trợ cấp", "nghị định", "thông tư", "có hiệu lực", "tòa án", "khởi tố", "khởi kiện",
              "căng thẳng", "trầm cảm", "Gen Z", "lạm phát", "tăng trưởng kinh tế", "suy thoái", "khu công nghiệp",
              "người đi làm", "tinh giản", "Bộ Nội vụ", "giúp việc", "người khuyết tật", "đoàn viên", "nghỉ phép",
              "nghỉ ốm", "bóc lột", "mua bán người", "dệt may", "da giày", "tự động hóa", "hưu trí",
              "bảo hiểm y tế", "phụ cấp", "nghỉ hưu", "khởi kiện", "xử phạt vi phạm", "lừa đảo", "chiếm đoạt"}


def assess(title, sapo, content, url=""):
    """Đánh giá mức độ liên quan. Trả về dict: status, score, topic_primary, topic_secondary, matched_keywords, reason."""
    head = f"{title} {sapo}"
    full = f"{title}\n{sapo}\n{content}"
    if EXCLUDE_TITLE_RE.search(title):
        return {"status": "excluded", "reason": "tiêu đề tuyển dụng/quảng cáo/thể thao"}
    if any(m.lower() in full.lower() for m in EXCLUDE_BODY_MARKERS):
        return {"status": "excluded", "reason": "nội dung quảng cáo/tài trợ"}
    if "/the-thao/" in url or "/bong-da/" in url or "/giai-tri/" in url:
        return {"status": "excluded", "reason": "chuyên mục thể thao/giải trí"}

    a_head, a_full = anchor_count(head), anchor_count(full)
    th_head, th_full = topic_hits(head), topic_hits(full)
    strong_head = {k for c, ks in th_head.items() for k in ks if c not in WEAK_GROUPS and k not in GENERIC_KW}
    strong_full = {k for c, ks in th_full.items() for k in ks if c not in WEAK_GROUPS and k not in GENERIC_KW}

    # Tin quốc tế: tiêu đề có yếu tố nước ngoài nhưng thân bài hầu như không nhắc tới Việt Nam
    vn_mentions = len(VIETNAM_RE.findall(full))
    if (FOREIGN_RE.search(title) or "Trump" in title) and vn_mentions < 2:
        return {"status": "excluded", "reason": "tin quốc tế, không liên hệ người lao động Việt Nam"}

    words = max(len(content.split()), 1)
    density = a_full / words * 1000  # neo / 1000 từ
    score = 3 * len(strong_head) + 2 * min(a_head, 3) + min(len(strong_full), 8) + min(density, 15) / 3

    if (strong_head or a_head) and a_full >= 3 and len(strong_full) >= 1:
        status = "relevant"
    elif a_full >= 6 and len(strong_full) >= 2 and density >= 6:
        status = "relevant"
    elif a_head and a_full >= 4 and th_full:  # tiêu đề nêu rõ lao động/việc làm, thân bài có từ khóa bổ trợ
        status = "relevant"
    elif a_full >= 3 and strong_full:
        status = "borderline"
    else:
        return {"status": "excluded", "reason": f"không đủ nội dung lao động (neo={a_full}, kw={len(strong_full)})"}

    # Chủ đề: ưu tiên nhóm khớp ở tiêu đề/sapo, rồi theo số từ khóa khớp toàn bài
    def rank(code):
        return (len(th_head.get(code, [])) * 3 + len(th_full.get(code, []))
                - (2 if code in WEAK_GROUPS else 0) - (1 if code == "G" and th_full[code] == ["công nhân"] else 0))
    codes = sorted(th_full, key=rank, reverse=True)
    primary = codes[0] if codes else ""
    secondary = [c for c in codes[1:3] if rank(c) >= 2]
    kws = []
    for c in codes:
        for k in th_full[c]:
            if k not in kws:
                kws.append(k)
    return {"status": status, "score": round(score, 2), "topic_primary": primary,
            "topic_secondary": secondary, "matched_keywords": kws[:15],
            "reason": f"neo={a_full}, kw_mạnh={len(strong_full)}, mật_độ={density:.1f}"}
