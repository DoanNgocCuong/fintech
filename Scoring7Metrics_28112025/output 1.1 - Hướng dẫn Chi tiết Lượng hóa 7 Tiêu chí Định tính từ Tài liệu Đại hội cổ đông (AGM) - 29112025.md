# Hướng dẫn Chi tiết Lượng hóa 7 Tiêu chí Định tính từ Tài liệu Đại hội cổ đông (AGM)

Bản hướng dẫn này trình bày chi tiết cách thức áp dụng **Mô hình Chấm điểm Dựa trên Quy tắc (Rule-Based Scoring Model)** để chuyển đổi 7 nhóm tiêu chí định tính được trích xuất từ tài liệu Đại hội cổ đông (AGM) thành điểm số có thể đo lường và giải thích được.

**Nguyên tắc cốt lõi:**
1.  **Deterministic (Tính Nhất quán):** Cùng một tính năng trích xuất phải cho ra cùng một điểm số.
2.  **Attributable (Khả năng Giải thích):** Điểm số phải được phân rã và giải thích bằng các tính năng (features) cụ thể trích xuất từ văn bản.
3.  **Rubric-Based (Dựa trên Tiêu chí):** Điểm số được gán dựa trên mức độ cụ thể, minh bạch, và mức độ rủi ro/lợi ích của thông tin được trích xuất.

---

## Bảng Lượng hóa Chi tiết (Rubric Scoring) cho 7 Tiêu chí AGM

Mỗi tiêu chí sẽ được lượng hóa bằng cách gán điểm số (Score) cho các **Tính năng Hành vi (Behavioral Features)** được trích xuất từ văn bản AGM.

### 1. Governance Cứng (Core Governance)

**Mục tiêu Lượng hóa:** Đánh giá mức độ độc lập, minh bạch và sự cân bằng quyền lực trong bộ máy quản trị.

| Tính năng Hành vi (Feature) | Quy tắc Lượng hóa (Rule) | Điểm số (Score) | Giải thích |
| :--- | :--- | :--- | :--- |
| **Tỷ lệ Thành viên Độc lập HĐQT** | Tỷ lệ thành viên độc lập so với tổng số thành viên HĐQT. | **+5** (≥ 30% tổng số) | Đảm bảo tính khách quan và bảo vệ lợi ích cổ đông thiểu số. |
| | | **+2** (10% - 30%) | Đạt mức tối thiểu theo quy định. |
| | | **-5** (< 10% hoặc không có) | Rủi ro quản trị cao, thiếu tính độc lập. |
| **Thay đổi Nhân sự Cấp cao** | Thay đổi đột ngột (từ nhiệm trước thời hạn, miễn nhiệm). | **-10** (Có) | Tín hiệu bất ổn nội bộ, rủi ro điều hành. |
| | | **+3** (Bầu mới/tái cử theo lộ trình) | Ổn định nhân sự. |
| **Thù lao HĐQT/BKS** | Tỷ lệ thù lao so với Lợi nhuận Sau Thuế (LNST). | **-5** (Thù lao > 5% LNST) | Chi phí quản lý quá cao, không hiệu quả. |
| | | **+5** (Thù lao < 1% LNST) | Quản trị tiết kiệm, gắn lợi ích với hiệu quả kinh doanh. |

### 2. Incentive – ESOP & Bonus

**Mục tiêu Lượng hóa:** Đánh giá rủi ro pha loãng (dilution risk) và mức độ gắn kết lợi ích của ban lãnh đạo với cổ đông.

| Tính năng Hành vi (Feature) | Quy tắc Lượng hóa (Rule) | Điểm số (Score) | Giải thích |
| :--- | :--- | :--- | :--- |
| **Tỷ lệ Pha loãng (ESOP)** | Tỷ lệ ESOP so với Vốn Điều lệ hiện tại. | **-10** (Tỷ lệ > 5%) | Pha loãng quá mức, ảnh hưởng lớn đến cổ đông hiện hữu. |
| | | **-3** (Tỷ lệ 1% - 5%) | Pha loãng ở mức chấp nhận được. |
| | | **+5** (Không có ESOP hoặc < 1%) | Không pha loãng. |
| **Điều kiện Vesting (Gắn kết)** | ESOP có gắn với KPI (Lợi nhuận, ROE, Thị giá) rõ ràng không. | **+10** (Có KPI định lượng, cụ thể) | Gắn kết lợi ích dài hạn, có trách nhiệm. |
| | | **-5** (Không có KPI hoặc KPI chung chung) | Rủi ro "chia chác" lợi ích. |
| **Giá Phát hành ESOP** | Giá phát hành so với Thị giá (tại thời điểm AGM). | **-5** (Chiết khấu > 50%) | Rủi ro đạo đức, lợi ích ban lãnh đạo quá lớn. |
| | | **+5** (Chiết khấu < 10% hoặc bằng Thị giá) | Công bằng với cổ đông. |

### 3. Payout – Cổ tức & Phân phối lợi nhuận

**Mục tiêu Lượng hóa:** Đánh giá chính sách phân phối lợi nhuận, sự ổn định và mức độ giữ lại lợi nhuận để tái đầu tư.

| Tính năng Hành vi (Feature) | Quy tắc Lượng hóa (Rule) | Điểm số (Score) | Giải thích |
| :--- | :--- | :--- | :--- |
| **Hình thức Cổ tức** | Ưu tiên Cổ tức Tiền mặt hay Cổ phiếu. | **+5** (Tiền mặt > Cổ phiếu) | Dòng tiền thực, tín hiệu tài chính lành mạnh. |
| | | **-5** (Chỉ Cổ phiếu hoặc Cổ phiếu > Tiền mặt) | Tín hiệu thiếu tiền mặt hoặc muốn tăng vốn ảo. |
| **Tỷ lệ Giữ lại LNST** | Tỷ lệ LNST giữ lại để tái đầu tư. | **+5** (Giữ lại 50% - 80% LNST) | Cân bằng giữa chi trả và tái đầu tư có kỷ luật. |
| | | **-5** (Giữ lại < 20% hoặc > 90%) | Thiếu cơ hội tái đầu tư hoặc quá tham lam giữ lại. |
| **Quỹ Đầu tư Phát triển** | Mức trích Quỹ Đầu tư Phát triển. | **+3** (Có trích quỹ cụ thể) | Cam kết tái đầu tư rõ ràng. |

### 4. Capital Actions – Thay đổi vốn & Phát hành

**Mục tiêu Lượng hóa:** Đánh giá tính cần thiết, hiệu quả và rủi ro pha loãng từ các hoạt động tăng/giảm vốn.

| Tính năng Hành vi (Feature) | Quy tắc Lượng hóa (Rule) | Điểm số (Score) | Giải thích |
| :--- | :--- | :--- | :--- |
| **Mục đích Sử dụng Vốn** | Mục đích tăng vốn có cụ thể và khả thi không. | **+10** (Mục đích rõ ràng, gắn với dự án cụ thể) | Tăng vốn có chiến lược, tạo giá trị. |
| | | **-10** (Mục đích chung chung: "Bổ sung vốn lưu động") | Tăng vốn không rõ ràng, rủi ro sử dụng vốn kém hiệu quả. |
| **Phát hành cho Cổ đông Chiến lược** | Có Lock-in Period (Hạn chế chuyển nhượng) không. | **+5** (Có Lock-in ≥ 3 năm) | Cam kết dài hạn của đối tác chiến lược. |
| | | **-5** (Không có Lock-in hoặc < 1 năm) | Rủi ro đối tác chỉ đầu tư ngắn hạn. |
| **Nguồn Tăng Vốn** | Nguồn tăng vốn từ LNST giữ lại hay Phát hành mới. | **+5** (Từ LNST giữ lại/Thặng dư) | Tăng vốn nội tại, không pha loãng. |
| | | **-5** (Phát hành tiền mặt mới) | Pha loãng, cần đánh giá kỹ mục đích. |

### 5. Ownership & Strategic Stakeholders

**Mục tiêu Lượng hóa:** Đánh giá sự ổn định của cơ cấu sở hữu và chất lượng của các cổ đông lớn/chiến lược.

| Tính năng Hành vi (Feature) | Quy tắc Lượng hóa (Rule) | Điểm số (Score) | Giải thích |
| :--- | :--- | :--- | :--- |
| **Sự ổn định của Cổ đông Lớn** | Có sự thay đổi lớn (mua/bán > 5% cổ phần) trong năm không. | **-5** (Có sự thay đổi lớn) | Tín hiệu bất ổn về cơ cấu sở hữu. |
| | | **+5** (Ổn định, không thay đổi) | Cơ cấu sở hữu vững chắc. |
| **Cam kết Hỗ trợ Cổ đông Chiến lược** | Cổ đông chiến lược cam kết hỗ trợ gì (Kỹ thuật, Công nghệ, Quản trị, Thị trường). | **+10** (Cam kết cụ thể, có giá trị) | Tăng cường năng lực cạnh tranh. |
| | | **-5** (Chỉ cam kết về vốn) | Giá trị gia tăng thấp. |
| **Tỷ lệ Sở hữu Nước ngoài** | Tỷ lệ sở hữu nước ngoài có được đề cập không. | **+3** (Có đề cập, có kế hoạch tăng vốn) | Minh bạch và thu hút vốn ngoại. |

### 6. Kế hoạch Đầu tư & Chiến lược (Tiêu chí Định tính Cao)

**Mục tiêu Lượng hóa:** Đánh giá tính cụ thể, khả thi và tầm nhìn dài hạn của chiến lược.

| Tính năng Hành vi (Feature) | Quy tắc Lượng hóa (Rule) | Điểm số (Score) | Giải thích |
| :--- | :--- | :--- | :--- |
| **Tính Cụ thể của Kế hoạch (Specificity)** | Kế hoạch/Dự án trọng điểm có đủ 3 yếu tố: **Tên + Chi phí + Thời gian** không. | **+10** (Đủ 3/3 yếu tố) | Kế hoạch chi tiết, có thể theo dõi và đánh giá. |
| | | **+5** (Đủ 2/3 yếu tố) | Kế hoạch ở mức trung bình. |
| | | **-5** (Chỉ có Tên/Mục tiêu chung chung) | Kế hoạch mơ hồ, thiếu cam kết thực hiện. |
| **Tầm nhìn Chiến lược** | Kế hoạch có đề cập đến các xu hướng dài hạn (Chuyển đổi số, ESG, Mở rộng thị trường mới) không. | **+5** (Có đề cập cụ thể) | Tầm nhìn vượt ra ngoài năm tài chính hiện tại. |
| | | **-3** (Chỉ tập trung vào mục tiêu ngắn hạn) | Thiếu tầm nhìn chiến lược. |
| **Đầu tư Tài chính** | Chính sách đầu tư tài chính (Trái phiếu CP, Cổ phiếu) có thay đổi kỳ hạn không. | **+3** (Có điều chỉnh kỳ hạn theo rủi ro) | Quản lý tài sản chủ động. |

### 7. Rủi ro & Quản trị Rủi ro (Tiêu chí Định tính Cao)

**Mục tiêu Lượng hóa:** Đánh giá tính chủ động (Proactiveness) và minh bạch (Transparency) trong việc nhận diện và ứng phó rủi ro.

| Tính năng Hành vi (Feature) | Quy tắc Lượng hóa (Rule) | Điểm số (Score) | Giải thích |
| :--- | :--- | :--- | :--- |
| **Báo cáo Ban Kiểm soát (BKS)** | BKS có nêu rõ **Vi phạm/Khuyết điểm** hoặc **Kiến nghị cụ thể** không. | **+10** (Có nêu rõ vi phạm/kiến nghị) | Minh bạch cao, hệ thống kiểm soát nội bộ hoạt động hiệu quả. |
| | | **-5** (Báo cáo chung chung, không có kiến nghị) | BKS hoạt động hình thức, thiếu tính độc lập. |
| **Biện pháp Ứng phó Khủng hoảng** | Có nêu rõ **Chiến lược Phòng thủ** (ví dụ: điều chỉnh danh mục, tăng thanh khoản) khi thị trường biến động không. | **+5** (Có chiến lược cụ thể) | Quản trị rủi ro chủ động. |
| | | **-5** (Chỉ nêu "Tuân thủ quy định pháp luật") | Quản trị rủi ro thụ động. |
| **Hạn mức Rủi ro Giữ lại** | Có đề cập đến Hạn mức Rủi ro Giữ lại (% Vốn Chủ Sở hữu) không. | **+3** (Có đề cập) | Quản lý rủi ro có định lượng. |

---

## Tổng hợp và Tính điểm Cuối cùng

### 1. Công thức Tính điểm (Scorecard Formula)

Điểm số cuối cùng (Total Governance Score) là tổng hợp có trọng số của các Sub-Score từ 7 nhóm tiêu chí.

$$\text{Total Score} = \sum_{i=1}^{7} W_i \times \text{SubScore}_i$$

Trong đó:
*   $\text{SubScore}_i$: Điểm số của nhóm tiêu chí $i$ (ví dụ: Governance Cứng).
*   $W_i$: Trọng số của nhóm tiêu chí $i$.

**Ví dụ về Trọng số Khuyến nghị (Có thể điều chỉnh theo ngành):**

| Nhóm Tiêu chí | Trọng số ($W_i$) | Lý do |
| :--- | :--- | :--- |
| 1. Governance Cứng | 25% | Yếu tố nền tảng, ảnh hưởng trực tiếp đến rủi ro đạo đức. |
| 2. Incentive – ESOP & Bonus | 20% | Ảnh hưởng lớn đến pha loãng và động lực ban lãnh đạo. |
| 3. Payout – Cổ tức | 10% | Quan trọng nhưng dễ lượng hóa hơn các yếu tố khác. |
| 4. Capital Actions | 15% | Ảnh hưởng đến cấu trúc vốn và mục đích sử dụng vốn. |
| 5. Ownership | 5% | Thường ổn định, ít thay đổi. |
| **6. Kế hoạch & Chiến lược** | **15%** | **Yếu tố định tính cao, quyết định tăng trưởng dài hạn.** |
| **7. Rủi ro & Quản trị Rủi ro** | **10%** | **Yếu tố định tính cao, quyết định khả năng chống chịu khủng hoảng.** |
| **Tổng** | **100%** | |

### 2. Quy trình Lượng hóa (Workflow)

1.  **Trích xuất Tính năng (Feature Extraction):** Sử dụng hệ thống IE/LLM để trích xuất tất cả các **Tính năng Hành vi** (ví dụ: "Tỷ lệ ESOP", "Có KPI Vesting không", "Mục đích tăng vốn là gì") từ văn bản AGM.
2.  **Gán Điểm (Rule Application):** Áp dụng các quy tắc trong bảng Rubric Scoring trên để gán điểm số tương ứng cho từng Tính năng.
3.  **Tính Sub-Score:** Tổng hợp điểm số của các Tính năng trong cùng một nhóm tiêu chí để ra Sub-Score (ví dụ: Sub-Score Governance Cứng = $\sum$ Điểm các Tính năng trong nhóm 1).
4.  **Tính Total Score:** Áp dụng công thức trọng số để tính Total Governance Score.
5.  **Giải thích (Attribution):** Trả về Total Score kèm theo danh sách các Tính năng có điểm số cao nhất (Top Positive) và thấp nhất (Top Negative) để giải thích kết quả.

**Ví dụ Output Giải thích (Attribution):**

> **Total Governance Score: 78/100**
>
> *   **Top Positive:**
>     *   (+10 điểm) Kế hoạch đầu tư CNTT có đủ Tên dự án, Chi phí (50 tỷ VNĐ) và Thời gian (2025-2027).
>     *   (+5 điểm) Tỷ lệ thành viên độc lập HĐQT đạt 33%.
> *   **Top Negative:**
>     *   (-10 điểm) ESOP có tỷ lệ pha loãng 6% Vốn Điều lệ.
>     *   (-5 điểm) Báo cáo BKS không có kiến nghị cụ thể nào, chỉ nêu "Hoàn thành nhiệm vụ".

Bằng cách này, chúng ta đã chuyển đổi một tài liệu định tính phức tạp thành một **hệ thống đo lường định lượng, có thể theo dõi và giải thích được**, đáp ứng hoàn toàn yêu cầu về tính chính xác và tính thuyết phục.
