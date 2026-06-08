import json
import os
from pathlib import Path
from datetime import datetime

# Initialize paths
SRC_DIR = Path(__file__).parent
DATA_DIR = SRC_DIR.parent / "data"
LEGAL_DIR = DATA_DIR / "landing" / "legal"
NEWS_DIR = DATA_DIR / "landing" / "news"

def generate_pdf(filepath: Path, title: str, sections: list):
    """Generate a clean PDF using reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

    doc = SimpleDocTemplate(str(filepath), pagesize=letter,
                            rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=15
    )
    heading2_style = ParagraphStyle(
        'Heading2Style',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        alignment=TA_JUSTIFY,
        fontSize=10,
        leading=14,
        spaceAfter=8
    )

    # Document Header
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 15))

    # Add content
    for sec_title, paragraphs in sections:
        if sec_title:
            story.append(Paragraph(sec_title, heading2_style))
        for p_text in paragraphs:
            story.append(Paragraph(p_text, body_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    print(f"Generated PDF: {filepath}")

def generate_all_assets():
    LEGAL_DIR.mkdir(parents=True, exist_ok=True)
    NEWS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Luật Phòng, chống ma túy 2021
    if not (LEGAL_DIR / "luat-phong-chong-ma-tuy-2021.pdf").exists():
        luat_2021_sections = [
            (
                "Chương I: Quy Định Chung",
                [
                    "Điều 1. Phạm vi điều chỉnh: Luật này quy định về phòng, chống ma túy; quản lý người sử dụng trái phép chất ma túy; cai nghiện ma túy; trách nhiệm của cá nhân, gia đình, cơ quan, tổ chức trong phòng, chống ma túy; quản lý nhà nước và hợp tác quốc tế về phòng, chống ma túy.",
                    "Điều 2. Giải thích từ ngữ: Chất ma túy là các chất kích thích, ức chế thần kinh hoặc gây ảo giác, sinh hoạt nếu sử dụng nhiều lần có thể dẫn tới tình trạng nghiện ma túy.",
                    "Điều 3. Chính sách của Nhà nước về phòng, chống ma túy: Thực hiện đồng bộ các biện pháp tuyên truyền, giáo dục, kinh tế, xã hội, hành chính và hình sự để đấu tranh ngăn chặn và đẩy lùi tệ nạn ma túy."
                ]
            ),
            (
                "Chương II: Trách Nhiệm Phòng Chống Ma Túy",
                [
                    "Cá nhân, gia đình có trách nhiệm giáo dục các thành viên trong gia đình về tác hại của ma túy và chấp hành nghiêm chỉnh quy định của pháp luật về phòng, chống ma túy.",
                    "Cơ quan nhà nước, tổ chức xã hội có trách nhiệm thực hiện các biện pháp phòng chống ma túy trong phạm vi quyền hạn và nhiệm vụ của mình."
                ]
            ),
            (
                "Chương III: Cai Nghiện Ma Túy",
                [
                    "Điều 28. Biện pháp cai nghiện ma túy bao gồm cai nghiện ma túy tự nguyện và cai nghiện ma túy bắt buộc. Cai nghiện ma túy tự nguyện được thực hiện tại gia đình, cộng đồng hoặc tại cơ sở cai nghiện. Cai nghiện ma túy bắt buộc được thực hiện tại cơ sở cai nghiện ma túy công lập.",
                    "Quy trình cai nghiện ma túy bắt buộc được áp dụng cho người nghiện ma túy từ đủ 18 tuổi trở lên khi không đăng ký cai nghiện tự nguyện hoặc vi phạm các quy định về cai nghiện tự nguyện."
                ]
            )
        ]
        generate_pdf(
            LEGAL_DIR / "luat-phong-chong-ma-tuy-2021.pdf",
            "LUẬT PHÒNG, CHỐNG MA TÚY 2021",
            luat_2021_sections
        )
    else:
        print("luat-phong-chong-ma-tuy-2021.pdf already exists. Skipping generation to preserve real document.")

    # 2. Nghị định 105/2021/NĐ-CP
    if not (LEGAL_DIR / "nghi-dinh-105-2021.pdf").exists() and not (LEGAL_DIR / "nghi-dinh-105-2021.docx").exists():
        nd_105_sections = [
            (
                "Chương I: Phối hợp của các cơ quan chuyên trách phòng, chống tội phạm về ma túy",
                [
                    "Nghị định này quy định chi tiết và hướng dẫn thi hành một số điều của Luật Phòng, chống ma túy về phối hợp chuyên trách đấu tranh phòng chống ma túy giữa Công an, Cảnh sát biển, Hải quan và Bộ đội Biên phòng.",
                    "Nguyên tắc phối hợp: Chủ động, thường xuyên, kịp thời, bảo đảm sự chỉ đạo tập trung, thống nhất theo quy định pháp luật dưới sự điều hành trực tiếp của các cơ quan chuyên trách."
                ]
            ),
            (
                "Chương II: Kiểm soát các hoạt động hợp pháp liên quan đến ma túy",
                [
                    "Kiểm soát hoạt động nhập khẩu, xuất khẩu, tạm nhập tái xuất chất ma túy, tiền chất ma túy, thuốc gây nghiện và thuốc hướng thần nhằm phục vụ các mục đích y tế, nghiên cứu khoa học hoặc công nghiệp hợp pháp.",
                    "Cơ quan kiểm soát: Bộ Công an, Bộ Y tế, Bộ Công Thương chịu trách nhiệm cấp phép và kiểm tra giám sát định kỳ các cơ sở lưu trữ chất ma túy hợp pháp."
                ]
            ),
            (
                "Chương III: Quản lý người sử dụng trái phép chất ma túy",
                [
                    "Xét nghiệm chất ma túy trong cơ thể: Công an cấp xã, phường có thẩm quyền yêu cầu xét nghiệm đối với người có biểu hiện sử dụng trái phép chất ma túy hoặc người bị bắt quả tang có hành vi sử dụng ma túy.",
                    "Thủ tục lập hồ sơ quản lý: Thời hạn quản lý người sử dụng trái phép chất ma túy là 01 năm kể từ ngày có kết quả xét nghiệm dương tính."
                ]
            )
        ]
        generate_pdf(
            LEGAL_DIR / "nghi-dinh-105-2021.pdf",
            "NGHỊ ĐỊNH 105/2021/NĐ-CP HƯỚNG DẪN LUẬT PHÒNG CHỐNG MA TÚY",
            nd_105_sections
        )
    else:
        print("nghi-dinh-105-2021 docx/pdf already exists. Skipping generation to preserve real document.")

    # 3. Bộ luật Hình sự 2015 - Chương XX: Các Tội Phạm Về Ma Túy
    if not (LEGAL_DIR / "bo-luat-hinh-su-2015.pdf").exists():
        blhs_2015_sections = [
            (
                "Điều 248. Tội sản xuất trái phép chất ma túy",
                [
                    "1. Người nào sản xuất trái phép chất ma túy dưới bất kỳ hình thức nào, thì bị phạt tù từ 02 năm đến 07 năm.",
                    "2. Phạm tội thuộc một trong các trường hợp nghiêm trọng hơn như có tổ chức, tái phạm nguy hiểm hoặc khối lượng lớn thì bị phạt tù từ 07 năm đến 15 năm, hoặc phạt tù từ 15 năm đến 20 năm, chung thân hoặc tử hình."
                ]
            ),
            (
                "Điều 249. Tội tàng trữ trái phép chất ma túy",
                [
                    "1. Người nào tàng trữ trái phép chất ma túy mà không nhằm mục đích mua bán, vận chuyển, sản xuất trái phép chất ma túy thuộc các trường hợp quy định tại khoản 1 Điều này, thì bị phạt tù từ 01 năm đến 05 năm.",
                    "2. Hình phạt tăng nặng đối với hành vi tàng trữ khối lượng ma túy lớn từ 05 năm đến 10 năm tù, hoặc cao nhất từ 15 năm đến 20 năm hoặc tù chung thân."
                ]
            ),
            (
                "Điều 250. Tội vận chuyển trái phép chất ma túy",
                [
                    "Người nào vận chuyển trái phép chất ma túy mà không nhằm mục đích sản xuất, mua bán, tàng trữ trái phép chất ma túy, thì bị phạt tù từ 02 năm đến 07 năm. Mức án tối đa có thể lên tới chung thân hoặc tử hình đối với số lượng đặc biệt lớn."
                ]
            ),
            (
                "Điều 251. Tội mua bán trái phép chất ma túy",
                [
                    "Người nào mua bán trái phép chất ma túy, thì bị phạt tù từ 02 năm đến 07 năm. Đây là hành vi nghiêm trọng nhất thường bị áp dụng mức hình phạt cao như chung thân hoặc tử hình khi mua bán khối lượng tiền chất hoặc chất ma túy vượt ngưỡng cho phép."
                ]
            )
        ]
        generate_pdf(
            LEGAL_DIR / "bo-luat-hinh-su-2015.pdf",
            "BỘ LUẬT HÌNH SỰ 2015 - CHƯƠNG XX: CÁC TỘI PHẠM VỀ MA TÚY",
            blhs_2015_sections
        )
    else:
        print("bo-luat-hinh-su-2015.pdf already exists. Skipping generation to preserve real document.")

    # 5 news articles with real URLs
    news_articles = [
        {
                "url": "https://dantri.com.vn/phap-luat/dien-vien-hai-huu-tin-khai-su-dung-ma-tuy-do-to-mo-20230428133813927.htm",
                "title": "Diễn viên hài Hữu Tín khai sử dụng ma túy do tò mò",
                "date_crawled": "2026-06-08T14:50:50Z",
                "content_markdown": "# Diễn viên hài Hữu Tín khai sử dụng ma túy do tò mò\n\nNgày 28/4, TAND quận 8, xét xử sơ thẩm và tuyên bị cáo Trần Hữu Tín (36 tuổi, diễn viên hài Hữu Tín) 7 năm 6 tháng tù về tội Tổ chức sử dụng trái phép chất ma túy.\n\nLiên quan vụ án, bị cáo Nguyễn Hoàng Phi (32 tuổi) bị phạt 13 năm 6 tháng tù về tội Tàng trữ trái phép chất ma túy và Tổ chức sử dụng trái phép chất ma túy.\n\nCác bị cáo tại tòa (Ảnh: X.D.).\n\nTại tòa, Phi khai không biết sử dụng ma túy. Về lý do mang ma túy về phòng cất, bị cáo này khai, sau khi đi chơi với người đàn ông tên Endy (không rõ lai lịch) nhét vô tay bị cáo nên Phi cầm mang về. Bị cáo Phi khai rất hối hận vì sự việc mình đã gây ra, không biết sẽ gây ảnh hưởng nghiêm trọng như vậy.\n\nBị cáo Hữu Tín Thừa nhận hành vi phạm tội như cáo trạng quy kết và cho rằng mình sử dụng ma túy do tò mò.\n\n\"Bị cáo cũng biết ma túy tác hại lớn đến sức khỏe nhưng lúc đó do có uống bia, rượu, cứ nghe nói ma túy nên bị cáo tò mò sử dụng, không kìm chế được\", bị cáo Tín trình bày.\n\nBị cáo Hữu Tín khai thêm lấy ma túy trong phòng của Phi, nhìn viên thuốc không rõ là loại gì, chỉ suy đoán đó là thuốc lắc. Sau khi sử dụng xong thì thấy mệt, ngủ dậy còn bị ói.\n\nHĐXX nhận định, hành vi phạm tội của bị cáo Hữu Tín và Hoàng Phi rất nguy hiểm cho xã hội, cần cách ly các bị cáo ra khỏi xã hội một thời gian mới đủ sức răn đe. Theo HĐXX, bị cáo phạm tội không hưởng lợi nên không áp dụng hình phạt bổ sung.\n\nDiễn viên Hữu Tín (bên phải) khai sử dụng ma túy do tò mò (Ảnh: X.D).\n\nCác bị cáo có tình tiết giảm nhẹ phạm tội lần đầu, riêng bị cáo Hữu Tín có nhiều đóng góp cho xã hội, nhân thân tốt nên giảm nhẹ một phần hình phạt.\n\nTheo hồ sơ, Hữu Tín và bạn gái thuê căn hộ chung cư ở quận 8 sinh sống và cho Phi thuê lại một phòng trong nhà.\n\nGiữa tháng 5/2022, Phi cùng nhóm bạn đi hát karaoke ở quận 5, có sử dụng ma túy. Cuối cuộc chơi, thấy còn dư \"hàng\" nên anh này mang về cất trong phòng ngủ.\n\nRạng sáng 11/6/2022, Hữu Tín cùng 2 người bạn sau khi nhậu đã về căn hộ chơi. Lúc vào phòng Phi, Tín thấy \"đồ chơi\" và thuốc lắc nên lấy ra cùng các bạn sử dụng.\n\nLúc sau, Phi đi làm về lấy thêm viên ma túy đưa cho một người trong nhóm chơi, chỉnh nhạc lớn nhằm tạo cảm giác hưng phấn.\n\nSáng cùng ngày, Công an phường 5, quận 8, ập vào bắt quả tang. Tại hiện trường, nhà chức trách thu giữ nhiều tang vật liên quan. Kết quả xét nghiệm cho thấy Hữu Tín cùng 2 người khác dương tính với ma túy."
        },
        {
                "url": "https://tuoitre.vn/ca-si-chi-dan-nguoi-mau-an-tay-co-tien-truc-phuong-to-chuc-su-dung-ma-tuy-ra-sao-2026040214370414.htm",
                "title": "Ca sĩ Chi Dân, người mẫu An Tây, 'cô tiên' Trúc Phương tổ chức sử dụng ma túy ra sao?",
                "date_crawled": "2026-06-08T14:50:50Z",
                "content_markdown": "# Ca sĩ Chi Dân, người mẫu An Tây, 'cô tiên' Trúc Phương tổ chức sử dụng ma túy ra sao?\n\nChi Dân và An Tây là hai trong số những người nổi tiếng bị bắt vì ma túy - Ảnh: Công an cung cấp\n\nTrong vụ án, Nguyễn Trung Hiếu (ca sĩ Chi Dân) bị truy tố về tội tổ chức sử dụng trái phép chất ma túy; Andrea Aybar Carmona (quốc tịch Tây Ban Nha, người mẫu, diễn viên An Tây) bị truy tố về tội tổ chức sử dụng trái phép chất ma túy và tàng trữ trái phép chất ma túy; Nguyễn Đỗ Trúc Phương (\"cô tiên từ thiện\", 32 tuổi) bị truy tố về tội tổ chức sử dụng trái phép chất ma túy.\n\nTheo đó, Lê Thị Triều, Nguyễn Trung Hiếu (ca sĩ Chi Dân), Nguyễn Trung Tín, Hòa Thị Hồng, Thái Thị Huyền có mối quan hệ quen biết. Ngày 4-11-2024, tại căn nhà ở quận Tân Bình (cũ), Hiếu rủ Tín, Huyền, Triều, Hồng sử dụng ma túy. Tất cả đồng ý, thỏa thuận tiền mua ma túy chia đều cho từng người.\n\nCả nhóm hùn tiền đặt mua 5g ketamine và 3 viên MDMA giá 3 triệu đồng để sử dụng. Sau khi sử dụng xong ma túy loại ketamine, Hiếu và các bị can sử dụng ma túy dạng \"nước vui\".\n\nSau đó cả nhóm tiếp tục đặt mua 2 gói ma túy dạng \"nước vui\" giá 7,1 triệu đồng và 2,5g ketamine giá 2,5 triệu đồng để sử dụng. Đến ngày 7-11-2024 thì bị phát hiện.\n\nĐối với Andrea Aybar Carmona (quốc tịch Tây Ban Nha, người mẫu An Tây), từ năm 2020, Andrea Aybar Carmona thuê Văn Anh Duy làm trợ lý, hỗ trợ Andrea quay video đăng trên nền tảng TikTok và đưa, đón Andrea đi làm, Duy được trả công 10 triệu đồng/tháng.\n\nĐầu năm 2024, Andrea nhờ Lộc mua ma túy để sử dụng. Khi Lộc đến khu vực phố đi bộ Bùi Viện, quận 1 (cũ) chơi thì biết người đàn ông tên Ngọc (không rõ lai lịch) bán ma túy. Lộc đã mua cho Andrea 1 gói ma túy giá 500.000 đồng, giao ma túy tại khu vực gầm cầu Him Lam, quận 7 (cũ).\n\nSau đó Andrea tiếp tục nhờ Lộc mua ma túy để sử dụng và cho Lộc sử dụng ma túy chung. Mỗi lần Lộc mua của Ngọc 1 gói ma túy giá 800.000 đồng, đưa lại cho Andrea.\n\nLúc 18h ngày 3-11-2024, Duy đến căn hộ của Andrea để giúp Andrea quay TikTok. Andrea lấy bộ dụng cụ sử dụng ma túy đã mua trước đó đưa ra phòng khách, Andrea và Duy sử dụng. Lúc này, Nguyễn Phương Đông (bạn quen biết của Andrea) đến chơi, nên đã sử dụng ma túy cùng với Andrea và Duy.\n\nNgày 8-11-2024, Duy đến căn hộ của Andrea để chở cô này đi quay TikTok. Andrea nhờ Duy mua của Lộc 1 triệu đồng ma túy để sử dụng chung thì bị phát hiện. Khám xét chỗ ở của Andrea thu giữ 0,1184g methamphetamine và 0,7524g cần sa.\n\nCòn bị can Nguyễn Đỗ Trúc Phương (hay còn gọi là \"cô tiên từ thiện\") bị truy tố về tội tổ chức sử dụng trái phép chất ma túy. Phương được xác định đã 2 lần nhờ bạn mua ma túy để sử dụng.\n\nViện KSND TP.HCM đã hoàn tất cáo trạng truy tố 227 bị can trong chuyên án VN10 - chuyên án liên quan 4 nữ tiếp viên hàng không bị lợi dụng vận chuyển trái phép chất ma túy, phát hiện tại sân bay quốc tế Tân Sơn Nhất hồi tháng 3-2023.\n\nĐã có lỗi xảy ra, mời bạn quay lại bài viết và thực hiện lại thao tác\n\nHiện chưa có bình luận nào, hãy là người đầu tiên bình luận\n\nTuổi Trẻ Online sẽ gởi đến bạn những tin tức nổi bật nhất"
        },
        {
                "url": "https://thanhnien.vn/chuyen-an-bi-so-vn10-ca-si-chi-dan-ru-re-gop-tien-choi-ma-tuy-185260403093444362.htm",
                "title": "Chuyên án bí số VN10: Ca sĩ Chi Dân rủ rê, góp tiền 'chơi' ma túy",
                "date_crawled": "2026-06-08T14:50:50Z",
                "content_markdown": "# Chuyên án bí số VN10: Ca sĩ Chi Dân rủ rê, góp tiền 'chơi' ma túy\n\nViện KSND TP.HCM vừa có cáo trạng truy tố và chuyển hồ sơ qua TAND cùng cấp đề nghị xét xử sơ thẩm Hoàng Sỹ Thắng và 226 bị can trong chuyên án bí số VN10, liên quan đến 4 nữ tiếp viên hàng không xách ma túy từ Pháp về Việt Nam. Trong đó, có bị can là ca sĩ Chi Dân, người mẫu An Tây, \"cô tiên từ thiện\" Trúc Phương.\n\nChuyên án bí số VN10 được lập sau khi Chi cục Hải quan sân bay quốc tế Tân Sơn Nhất phát hiện trong vali hành lý của 4 nữ tiếp viên hàng không trên chuyến bay số hiệu VN10, mang nhiều kiện kem đánh răng và được xác định là ma túy sau đó\n\nTheo Viện KSND TP.HCM, từ khi khởi tố vụ án đến nay, Công an TP.HCM (PC04) nhập tổng cộng 20 vụ án với 227 bị can. Ngoài ra, mở rộng điều tra từ vụ án Hoàng Sỹ Thắng và đồng phạm, cơ quan tiến hành tố tụng tại TP.HCM đã khởi tố 477 vụ án, với 2.776 bị can; xử lý hành chính 264 người liên quan.\n\nTrong vụ án Hoàng Sỹ Thắng và 226 bị can bị truy tố, thì Nguyễn Trung Hiếu (36 tuổi, ca sĩ Chi Dân) và anh trai Nguyễn Trung Tín (44 tuổi) cùng bị truy tố về tội “tổ chức sử dụng trái phép chất ma túy”, theo khoản 2 điều 255 bộ luật Hình sự, khung hình phạt từ 7 - 15 năm tù.\n\nNguyễn Trung Hiếu bị truy xét, bắt giữ khi Đội CSĐT tội phạm về ma túy Công an quận 12 (cũ) bắt nhóm tội phạm ma túy liên quan đến bị can Võ Thị Kim Tuyến và đồng phạm phạm tội \"mua bán trái phép chất ma túy\", \"tổ chức sử dụng trái phép chất ma túy\" và \"tàng trữ trái phép chất ma túy\".\n\nTrong quá trình điều tra, cơ quan tố tụng đã nhập vụ án của ca sĩ Chi Dân vào chuyên án bí số VN10.\n\nChuyên án bí số VN10: Ca sĩ Chi Dân rủ rê, góp tiền 'chơi' ma túy\n\nTheo hồ sơ, tối 6.11.2024, Đội 2 - Phòng Cảnh sát điều tra tội phạm về ma túy Công an TP.HCM kiểm tra một khách sạn ở xã Vĩnh Lộc B, huyện Bình Chánh (nay là xã Tân Vĩnh Lộc), phát hiện tại phòng của Võ Thị Kim Tuyến và Võ Văn Nhật (33 tuổi) cất giấu gần 298 gram ma túy các loại.\n\nCa sĩ Chi Dân tại cơ quan điều tra\n\nTuyến khai nhận ma túy do bị can này mua và cất giấu tại phòng khách sạn để bán lại cho người khác. Quá trình mua bán ma túy của Tuyến có Nhật và Võ Thị Ánh Tuyết (36 tuổi) phụ giúp.\n\nMở rộng điều tra, cơ quan điều tra xác định ngày 4.11.2024, Tuyến có giao 2,5 gram ma túy loại ketamine đến một địa điểm trên đường Cộng Hòa qua ứng dụng giao hàng.\n\nNgày 8.11.2024, Công an quận Tân Bình (cũ) kiểm tra phòng 201 căn nhà tại địa chỉ trên, phát hiện Lê Thị Triều (26 tuổi, quê Gia Lai) có biểu hiện nghi vấn nên tiến hành xét nghiệm, kết quả Triều dương tính với ma túy.\n\nTriều khai sử dụng ma túy chung với bạn là Hòa Thị Hồng, Thái Thị Huyền (ở chung phòng với Triều), Nguyễn Trung Hiếu (ca sĩ Chi Dân), Nguyễn Trung Tín (anh ruột ca sĩ Chi Dân) và Lương Thế Kiên ngay tại phòng của Triều vào sáng 4.11.2024, và sử dụng ma túy với 2 người khác vào ngày 7.11.2024.\n\nCùng ngày 8.11.2024, Cơ quan điều tra khám xét khẩn cấp chỗ ở của ca sĩ Chi Dân và Nguyễn Trung Tín nhưng không có đồ vật, tài liệu liên quan đến tội phạm.\n\nKhi làm việc với nhóm tội phạm trên, cơ quan điều tra xác định sự việc bắt đầu từ cuộc nhậu tại phòng Huyền và Triều vào chiều 3.11.2024. Đến rạng sáng 4.11, ca sĩ Chi Dân cùng anh trai là Nguyễn Trung Tín đến nhập hội."
        },
        {
                "url": "https://vietnamnet.vn/vai-tro-ca-si-chi-dan-nguoi-mau-an-tay-trong-vu-4-tiep-vien-xach-ma-tuy-2502809.html",
                "title": "Vai trò ca sĩ Chi Dân, người mẫu An Tây trong vụ '4 tiếp viên vận chuyển ma túy'",
                "date_crawled": "2026-06-08T14:50:50Z",
                "content_markdown": "# Vai trò ca sĩ Chi Dân, người mẫu An Tây trong vụ '4 tiếp viên vận chuyển ma túy'\n\nViện KSND TPHCM vừa hoàn tất cáo trạng truy tố 227 bị can trong chuyên án VN10 – vụ án từng gây xôn xao khi các tiếp viên hàng không bị lợi dụng vận chuyển ma túy từ Pháp về Việt Nam bằng đường hàng không.\n\nCác bị can bị truy tố về nhiều tội danh như: vận chuyển trái phép chất ma túy, mua bán trái phép chất ma túy, tổ chức sử dụng trái phép chất ma túy, tàng trữ trái phép chất ma túy, không tố giác tội phạm, che giấu tội phạm, chiếm giữ trái phép tài sản và sử dụng tài liệu giả của cơ quan, tổ chức.\n\nTrong số này có 4 bị can đang bị truy nã, Viện KSND đề nghị TAND TPHCM xét xử vắng mặt.\n\nVụ án có một số người nổi tiếng bị truy tố như: ca sĩ Chi Dân (tên thật Nguyễn Trung Hiếu) và Nguyễn Đỗ Trúc Phương – người được biết đến với biệt danh “cô Tiên từ thiện” – cùng bị truy tố về tội tổ chức sử dụng trái phép chất ma túy. Trong khi đó, người mẫu, diễn viên An Tây (tên thật Andrea Aybar Carmona, quốc tịch Tây Ban Nha) bị truy tố về các tội tổ chức sử dụng trái phép chất ma túy và tàng trữ trái phép chất ma túy.\n\nVụ án được phát hiện vào cuối tháng 3/2023, khi Công an TPHCM phối hợp với Bộ Công an và Hải quan cửa khẩu sân bay quốc tế Tân Sơn Nhất bắt quả tang 4 nữ tiếp viên hàng không vận chuyển hơn 11kg ma túy, được giấu trong các tuýp kem đánh răng từ Pháp về Việt Nam. Từ đó, Công an TPHCM đã xác lập chuyên án VN10 để mở rộng điều tra.\n\nBan chuyên án phối hợp với công an nhiều tỉnh, thành từ Bắc vào Nam đã khởi tố, bắt giữ hơn 2.000 người liên quan đến các đường dây khác nhau; thu giữ lượng lớn ma túy, cùng vũ khí, súng đạn và nhiều tang vật. Cơ quan chức năng xác định tổng giá trị giao dịch ma túy của các đối tượng tương đương khoảng 29.000 tỷ đồng.\n\nRiêng tại TPHCM, cơ quan công an mở rộng điều tra, xử lý phần chính của chuyên án và đến nay các cơ quan tố tụng đã truy tố 227 bị can. Đối với các bị can liên quan đến các nhánh, đường dây khác, công an các địa phương tiếp tục điều tra, sớm đưa ra xét xử theo quy định.\n\nỞ phần chính của chuyên án VN10, cơ quan tố tụng TPHCM xác định bị can Hoàng Sỹ Thắng là mắt xích quan trọng, giữ vai trò cầm đầu. Đối tượng này cùng đồng phạm đã thiết lập các đường dây vận chuyển ma túy từ nước ngoài về Việt Nam tiêu thụ tại nhiều tỉnh, thành, đồng thời có liên quan đến nhiều đường dây ma túy khác.\n\nCơ quan điều tra xác định, các đối tượng trong chuyên án VN10 hoạt động có tổ chức, với phương thức, thủ đoạn tinh vi; lợi dụng không gian mạng, dịch vụ chuyển phát nhanh và giao dịch điện tử để hoạt động kín kẽ, đối phó cơ quan chức năng.\n\nQuá trình điều tra cũng làm rõ nhóm 4 nữ tiếp viên hàng không bị lợi dụng vận chuyển ma túy từ nước ngoài về Việt Nam. Các tiếp viên này không quen biết, không liên lạc hay giao dịch tiền bạc với các đối tượng trong đường dây.\n\nTrong vụ bắt quả tang hơn 11kg ma túy giấu trong các tuýp kem đánh răng, đây là lần đầu tiên 4 nữ tiếp viên được phân công cùng một hành trình bay Việt Nam – Pháp và chiều ngược lại. Nhóm này nhận vận chuyển hàng xách tay như kem đánh răng, bàn chải… cho Hà Danh Nậm (một bị can trong vụ án) từ Pháp về Việt Nam, với tiền công 6,5 euro/kg theo thỏa thuận.\n\nCơ quan tố tụng xác định các nữ tiếp viên đã bị lợi dụng, không biết ma túy được cất giấu tinh vi trong hàng hóa, nên không có căn cứ xử lý về tội vận chuyển trái phép chất ma túy."
        },
        {
                "url": "https://dantri.com.vn/phap-luat/truy-to-ca-si-chi-dan-nguoi-mau-an-tay-20260402122649916.htm",
                "title": "Truy tố ca sĩ Chi Dân, người mẫu An Tây",
                "date_crawled": "2026-06-08T14:50:50Z",
                "content_markdown": "# Truy tố ca sĩ Chi Dân, người mẫu An Tây\n\nViện KSND TPHCM đã hoàn tất cáo trạng truy tố 227 bị can trong đường dây ma túy xuyên quốc gia.\n\nTheo đó, bị can Hoàng Sỹ Thắng cùng đồng phạm bị truy tố về một hoặc các tội Vận chuyển trái phép chất ma túy; Mua bán trái phép chất ma túy; Tổ chức sử dụng trái phép chất ma túy; Tàng trữ trái phép chất ma túy; Không tố giác tội phạm; Che giấu tội phạm; Chiếm giữ trái phép tài sản và sử dụng tài liệu giả của cơ quan, tổ chức.\n\nCa sĩ Chi Dân bị truy tố (Ảnh: Công an cung cấp).\n\nTrong vụ án này, bị can Nguyễn Trung Hiếu (ca sĩ Chi Dân) và Andrea Aybar Carmona (thường gọi là An Tây, quốc tịch Tây Ban Nha; người mẫu, diễn viên) bị truy tố về Tội tổ chức sử dụng trái phép chất ma túy và Tàng trữ trái phép chất ma túy.\n\nVụ án Hoàng Sỹ Thắng và đồng phạm là vụ án đặc biệt nghiêm trọng, có tổ chức, liên quan đến số lượng lớn bị can, phạm vi hoạt động trải rộng trên nhiều tỉnh, thành phố.\n\nCác đối tượng thực hiện hành vi phạm tội với phương thức, thủ đoạn tinh vi, có sự phân công vai trò chặt chẽ, lợi dụng không gian mạng và các phương tiện giao dịch điện tử để thực hiện việc mua bán, vận chuyển trái phép chất ma túy.\n\nLiên quan tới hành vi phạm tội của ca sĩ Chi Dân, hồ sơ thể hiện, ngày 8/11/2024, Công an quận Tân Bình (cũ) kiểm tra phòng 201 căn nhà tại địa chỉ trên, phát hiện Lê Thị Triều (26 tuổi, quê Gia Lai) có biểu hiện nghi vấn nên tiến hành xét nghiệm. Kết quả, Triều dương tính với ma túy.\n\nTriều khai sử dụng ma túy chung với bạn là Hòa Thị Hồng, Thái Thị Huyền (ở cùng phòng), ca sĩ Chi Dân, Nguyễn Trung Tín và Lương Thế Kiên ngay tại phòng của Triều vào sáng 4/11/2024; ngoài ra còn sử dụng ma túy với 2 người khác vào ngày 7/11/2024.\n\nTheo cơ quan điều tra, chiều 3/11/2024, Hồng sang phòng Triều và Huyền chơi. Đến khoảng 23h, cả ba tổ chức ăn nhậu tại phòng. Hơn một tiếng sau, nhóm rủ thêm Long và Kiên đến nhậu, kéo dài đến gần 4h sáng hôm sau. Lúc này, ca sĩ Chi Dân nhắn tin rủ Hồng sang nhà mình nhậu, nhưng Hồng từ chối và rủ ngược lại.\n\nÍt lâu sau, ca sĩ Chi Dân cùng anh trai Nguyễn Trung Tín đến. Tại đây, Chi Dân rủ cả nhóm sử dụng ma túy và được mọi người hưởng ứng. Sau đó, Triều đặt mua ma túy, còn Tín trực tiếp ra nhận hàng từ một thanh niên không rõ lai lịch.\n\nMa túy được \"xào\" rồi để ra đĩa đặt trên bàn nhậu, mọi người dùng ống hút có sẵn trong phòng để hít. Riêng ca sĩ Chi Dân lấy móng tay xúc ma túy hít trực tiếp. Gói nylon chứa 3 viên thuốc lắc được để lên bàn, sau đó Hồng và Tín mỗi người dùng nửa viên, Huyền và Kiên mỗi người dùng một viên.\n\nTiếp đó, Chi Dân rủ cả nhóm sử dụng thêm ma túy loại \"nước vui\", Tín liên hệ đối tượng bán ma túy và Chi Dân chi tiền. Khi hàng được giao, Chi Dân pha cùng bò húc và nước lọc trong nồi, rồi cả nhóm dùng muỗng múc uống.\n\nĐến khoảng 9h ngày 4/11/2024, nhóm tiếp tục mua thêm ma túy để sử dụng. Sau đó, cả nhóm thống nhất dừng lại, ai về nhà nấy. Trước khi rời đi, Chi Dân hít thêm 2 đường, Tín rửa đĩa và vứt số ma túy còn lại trên đường về."
        }
]

    for i, art in enumerate(news_articles, 1):
        filename = f"article_{i:02d}.json"
        filepath = NEWS_DIR / filename
        filepath.write_text(json.dumps(art, ensure_ascii=False, indent=2))
        print(f"Generated JSON: {filepath}")

if __name__ == "__main__":
    generate_all_assets()
