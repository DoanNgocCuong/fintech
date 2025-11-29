# Ontology Subgraph ĐHĐCĐ (AGM Subgraph per Year)

**Phiên bản:** v1.1  
**Phạm vi:** Mô hình hoá các thông tin trích xuất từ tài liệu ĐHĐCĐ theo **từng năm**, dựa trên bộ **7 nhóm tiêu chí**.  
**Scope node/edge trong subgraph này:**

- Node: `Industry`, `Company`, `AGM_Year`, `AGM_Group`
- Edge: `BELONGS_TO`, `HAS_AGM`, `HAS_CRITERIA_GROUP`

> Các node khác như `FS_Year`, `AGM_Document`, `AGM_Fact`, `Topic`… được xem là thuộc các subgraph/phase khác, **không nằm trong ontology v1.1** này.


---

## 1. Node Types (Labels & Properties)

### 1.1. `Industry`

> Node ngành – làm cha cho nhiều công ty, dùng chung toàn KG và được tham chiếu trong subgraph ĐHĐCĐ.

- **Label:** `Industry`
- **Khóa logic:** `code`

| Field           | Type    | Required | Mô tả                                                       | Ví dụ                     |
|-----------------|---------|----------|-------------------------------------------------------------|---------------------------|
| `code`          | string  | Yes      | Mã ngành chuẩn hoá                                         | `"INS_NONLIFE"`           |
| `name_vi`       | string  | Yes      | Tên ngành tiếng Việt                                       | `"Bảo hiểm phi nhân thọ"` |
| `name_en`       | string  | No       | Tên ngành tiếng Anh                                        | `"Non-life Insurance"`    |
| `sector_code`   | string  | No       | Mã sector rộng hơn                                         | `"FINANCIALS"`            |
| `description`   | string  | No       | Mô tả ngắn về phạm vi ngành                                | `"Doanh nghiệp bảo hiểm..."` |
| `created_at`    | datetime| No       | Thời điểm tạo node                                         | `"2025-11-24T21:00:00"`   |

**Ví dụ node `Industry`:**

```json
{
  "label": "Industry",
  "code": "INS_NONLIFE",
  "name_vi": "Bảo hiểm phi nhân thọ",
  "name_en": "Non-life Insurance",
  "sector_code": "FINANCIALS",
  "description": "Bao gồm các doanh nghiệp bảo hiểm phi nhân thọ niêm yết tại Việt Nam."
}
```

---

### 1.2. `Company`

> Node doanh nghiệp – trung tâm liên kết giữa subgraph BCTC, ĐHĐCĐ, giá cổ phiếu,…

- **Label:** `Company`
- **Khóa logic:** `code`

| Field           | Type    | Required | Mô tả                                           | Ví dụ                            |
|-----------------|---------|----------|-------------------------------------------------|----------------------------------|
| `code`          | string  | Yes      | Mã cổ phiếu / mã công ty                        | `"MIG"`                          |
| `name_vi`       | string  | Yes      | Tên đầy đủ tiếng Việt                           | `"CTCP Bảo hiểm Quân đội"`       |
| `name_en`       | string  | No       | Tên tiếng Anh                                   | `"Military Insurance Corporation"` |
| `exchange`      | string  | No       | Sàn niêm yết                                    | `"HOSE"`                         |
| `industry_code` | string  | No       | Tham chiếu `Industry.code`                     | `"INS_NONLIFE"`                  |
| `listed_since`  | int     | No       | Năm niêm yết                                    | `2011`                           |
| `country`       | string  | No       | Quốc gia                                        | `"VN"`                           |
| `website`       | string  | No       | Website IR/chính thức                           | `"https://www.mig.vn"`           |
| `created_at`    | datetime| No       | Thời điểm tạo node                              | `"2025-11-24T21:05:00"`          |

**Ví dụ node `Company`:**

```json
{
  "label": "Company",
  "code": "MIG",
  "name_vi": "CTCP Bảo hiểm Quân đội",
  "name_en": "Military Insurance Corporation",
  "exchange": "HOSE",
  "industry_code": "INS_NONLIFE",
  "listed_since": 2011,
  "country": "VN",
  "website": "https://www.mig.vn"
}
```

---

### 1.3. `AGM_Year` (ĐHĐCĐ theo năm)

> Một node đại diện cho **một kỳ ĐHĐCĐ** của một công ty trong một năm tài chính.

- **Label:** `AGM_Year`
- **Khóa logic:** `(company_code, year)`

| Field             | Type      | Required | Mô tả                                                                 | Ví dụ                               |
|-------------------|-----------|----------|-----------------------------------------------------------------------|-------------------------------------|
| `company_code`    | string    | Yes      | Mã công ty, để join nhanh với `Company.code`                          | `"MIG"`                             |
| `year`            | int       | Yes      | Năm tài chính                                                         | `2023`                              |
| `meeting_date`    | date      | No       | Ngày tổ chức ĐHĐCĐ (ISO: YYYY-MM-DD)                                  | `"2024-04-20"`                      |
| `meeting_type`    | string    | No       | Loại họp: `"thuong_nien"` / `"bat_thuong"`                            | `"thuong_nien"`                     |
| `source_urls`     | list<str> | No       | Danh sách link tài liệu ĐHĐCĐ (PDF, web, file scan…)                  | `["https://ir.mig.vn/AGM2023.pdf"]` |
| `raw_doc_ids`     | list<str> | No       | ID nội bộ của các file thô (trong kho document / vector store)       | `["doc_MIG_AGM_2023_main"]`         |
| `summary`         | string    | No       | Tóm tắt 1–3 câu về nội dung chính                                     | `"Thông qua kế hoạch LN 2024..."`   |
| `extract_version` | string    | No       | Phiên bản pipeline extractor áp dụng                                  | `"AGM_extractor_v3"`                |
| `created_at`      | datetime  | No       | Thời điểm tạo node trong KG                                           | `"2025-11-24T21:30:00"`             |

**Ví dụ node `AGM_Year`:**

```json
{
  "label": "AGM_Year",
  "company_code": "MIG",
  "year": 2023,
  "meeting_date": "2024-04-20",
  "meeting_type": "thuong_nien",
  "source_urls": ["https://ir.mig.vn/AGM2023_full.pdf"],
  "raw_doc_ids": ["MIG_AGM_2023_main"],
  "summary": "ĐHĐCĐ thông qua kế hoạch lợi nhuận 2024 tăng 15%, ESOP cho HĐQT/Ban điều hành và cổ tức tiền mặt 15%.",
  "extract_version": "AGM_extractor_v3"
}
```

---

### 1.4. `AGM_Group` (Nhóm tiêu chí ĐHĐCĐ)

> Mỗi node `AGM_Group` đại diện cho **một trong 7 nhóm tiêu chí** được trích xuất từ ĐHĐCĐ, cho một công ty trong một năm.

- **Label:** `AGM_Group`
- **Khóa logic:** `(company_code, year, group_code)`

| Field           | Type      | Required | Mô tả                                                                 | Ví dụ                                      |
|-----------------|-----------|----------|-----------------------------------------------------------------------|--------------------------------------------|
| `company_code`  | string    | Yes      | Mã công ty                                                            | `"MIG"`                                    |
| `year`          | int       | Yes      | Năm tài chính                                                         | `2023`                                     |
| `group_code`    | int       | Yes      | Mã nhóm tiêu chí (1–7)                                               | `1`                                        |
| `group_name`    | string    | Yes      | Tên nhóm tiêu chí                                                    | `"Governance cứng"`                        |
| `score`         | float     | No       | Điểm chấm tổng quan 0–100 (nếu có bước scoring)                      | `78.5`                                     |
| `score_band`    | string    | No       | Nhãn phân loại: `"good" / "average" / "bad"`                         | `"good"`                                   |
| `data_json`     | string    | Yes      | JSON chi tiết các field được extract theo đúng cấu trúc từng nhóm   | (xem ví dụ từng nhóm bên dưới)            |
| `notes`         | string    | No       | Ghi chú (cảnh báo, flag, nghi vấn…)                                  | `"ESOP có nguy cơ pha loãng cao"`         |
| `created_at`    | datetime  | No       | Thời điểm tạo node                                                   | `"2025-11-24T21:45:00"`                    |

#### 1.4.1. Mapping `group_code` ↔ `group_name`

| `group_code` | `group_name` (gợi ý)                                   |
|--------------|--------------------------------------------------------|
| 1            | Governance cứng (HĐQT, BKS, nhân sự cấp cao, thù lao)  |
| 2            | Incentive – ESOP & Quỹ khen thưởng/phúc lợi            |
| 3            | Payout – Cổ tức & phân phối lợi nhuận                  |
| 4            | Capital Actions – Thay đổi vốn & các đợt phát hành     |
| 5            | Ownership & Strategic Stakeholders – Cổ đông lớn, sở hữu chéo |
| 6            | Kế hoạch đầu tư & Chiến lược                            |
| 7            | Rủi ro & Quản trị rủi ro                                |

---

## 2. Ví dụ chi tiết `AGM_Group.data_json` cho 7 nhóm

### 2.1. Nhóm 1 – Governance cứng (`group_code = 1`)

```json
{
  "board_of_directors": [
    {
      "name": "Nguyen Van A",
      "role": "Chu tich HĐQT",
      "status": "tai_cu",
      "term_from": 2023,
      "term_to": 2028,
      "vote_pct": 96.5,
      "rep_shareholder": "MB Bank",
      "other_positions": ["Chu tich cong ty XYZ"],
      "independent": false
    }
  ],
  "supervisory_board": [
    {
      "name": "Tran Thi B",
      "role": "Truong BKS",
      "term_from": 2023,
      "term_to": 2028,
      "vote_pct": 93.2,
      "remarks": "Khong co y kien ngoai tru"
    }
  ],
  "senior_changes": [
    {
      "person": "Le Van C",
      "position": "Tong giam doc",
      "change_type": "bo_nhiem",
      "reason": "Thay the TGĐ nhiem ky truoc",
      "vote_pct": 90.1,
      "sudden_flag": true
    }
  ],
  "compensation": {
    "total_comp": 25000000000,
    "as_pct_profit": 0.06,
    "split": {
      "board": 18000000000,
      "supervisory": 7000000000
    },
    "allowances": 2000000000,
    "other_expenses": 1000000000,
    "yoy_change_pct": 0.15
  }
}
```

**Ví dụ node đầy đủ cho nhóm 1:**

```json
{
  "label": "AGM_Group",
  "company_code": "MIG",
  "year": 2023,
  "group_code": 1,
  "group_name": "Governance cứng",
  "score": 80.0,
  "score_band": "good",
  "data_json": "{...JSON như trên...}",
  "notes": "HĐQT ổn định, không thay đổi đột biến."
}
```

---

### 2.2. Nhóm 2 – Incentive – ESOP & Quỹ (`group_code = 2`)

```json
{
  "esop_programs": [
    {
      "approve_year": 2022,
      "execute_year": 2023,
      "shares": 5000000,
      "percent_charter_capital": 0.05,
      "issue_price": 10000,
      "market_price_at_approval": 22000,
      "discount_pct": 0.545,
      "vesting_conditions": "Giu vi tri quan ly 3 nam, dat ke hoach LN",
      "beneficiaries": ["Thanh vien HĐQT", "Ban TGĐ"],
      "lockup_period_years": 3,
      "listing_date": "2024-01-15"
    }
  ],
  "bonus_welfare_dev_funds": {
    "lnst_year": 500000000000,
    "bonus_fund": { "amount": 20000000000, "pct_LNST": 0.04 },
    "welfare_fund": { "amount": 5000000000, "pct_LNST": 0.01 },
    "dev_invest_fund": { "amount": 10000000000, "pct_LNST": 0.02 },
    "next_year_provision": 2000000000
  },
  "staff_and_admin_costs": {
    "admin_expense": 100000000000,
    "staff_expense": 60000000000,
    "yoy_growth_pct": 0.12,
    "staff_expense_ratio_to_premium": 0.08
  }
}
```

**Ví dụ node nhóm 2:**

```json
{
  "label": "AGM_Group",
  "company_code": "MIG",
  "year": 2023,
  "group_code": 2,
  "group_name": "Incentive – ESOP & Quỹ",
  "score": 70.0,
  "score_band": "average",
  "data_json": "{...JSON như trên...}",
  "notes": "ESOP gia giam sau so voi thi truong."
}
```

---

### 2.3. Nhóm 3 – Payout – Cổ tức & phân phối LNST (`group_code = 3`)

```json
{
  "cash_dividend": {
    "pct_par": 0.15,
    "total_cash": 150000000000,
    "payment_schedule": "Q3/2024",
    "record_date": "2024-08-10",
    "ex_rights_date": "2024-08-08"
  },
  "stock_dividend": {
    "pct": 0.1,
    "shares_issued": 10000000,
    "source": "LNST_chua_phan_phoi",
    "execution_time": "2024-09",
    "dilution_pct": 0.091
  },
  "profit_distribution": {
    "lnst_year": 500000000000,
    "total_distributed": 350000000000,
    "retained": 150000000000,
    "payout_ratio": 0.7
  },
  "fund_allocations": {
    "financial_reserve_fund": 20000000000,
    "other_funds": [
      { "name": "Quy du phong rui ro nghiep vu", "amount": 30000000000 }
    ]
  }
}
```

**Ví dụ node nhóm 3:**

```json
{
  "label": "AGM_Group",
  "company_code": "MIG",
  "year": 2023,
  "group_code": 3,
  "group_name": "Payout – Cổ tức & phân phối lợi nhuận",
  "score": 75.0,
  "score_band": "average",
  "data_json": "{...JSON như trên...}",
  "notes": "Payout ratio cao, may be khong ben vung neu LN suy giam."
}
```

---

### 2.4. Nhóm 4 – Capital Actions – Thay đổi vốn (`group_code = 4`)

```json
{
  "charter_capital_before": 3000000000000,
  "charter_capital_after": 3500000000000,
  "capital_change_pct": 0.1667,
  "issues": [
    {
      "type": "right_issue",
      "shares": 30000000000,
      "issue_price": 10000,
      "market_price_at_announcement": 22000,
      "ratio_old_new": "2:1",
      "purpose": "Tang von, bo sung von hoat dong kinh doanh",
      "expected_timeline": "2024-10"
    },
    {
      "type": "private_placement",
      "shares": 1000000000,
      "investors": ["Nha dau tu chien luoc A"],
      "lockup_period_years": 3
    }
  ],
  "treasury_shares": {
    "before": 1000000,
    "after": 500000,
    "avg_buyback_price": 18000
  }
}
```

**Ví dụ node nhóm 4:**

```json
{
  "label": "AGM_Group",
  "company_code": "MIG",
  "year": 2023,
  "group_code": 4,
  "group_name": "Capital Actions – Thay đổi vốn & phát hành",
  "score": 68.0,
  "score_band": "average",
  "data_json": "{...JSON như trên...}",
  "notes": "Right issue co kha nang pha loang neu ke hoach su dung von khong ro rang."
}
```

---

### 2.5. Nhóm 5 – Ownership & Strategic Stakeholders (`group_code = 5`)

```json
{
  "major_shareholders": [
    {
      "name": "MB Bank",
      "type": "to_chuc",
      "ownership_pct": 0.35,
      "change_pct_vs_last_year": 0.02
    },
    {
      "name": "Nha dau tu A",
      "type": "ca_nhan",
      "ownership_pct": 0.07,
      "change_pct_vs_last_year": -0.01
    }
  ],
  "parent_company": {
    "name": "MB Bank",
    "ownership_pct": 0.35,
    "control_type": "co_anh_huong_dang_ke"
  },
  "cross_holdings": [
    {
      "related_company": "Cong ty lien ket X",
      "ownership_pct": 0.2,
      "nature": "dau tu chien luoc"
    }
  ],
  "foreign_ownership": {
    "total_pct": 0.1,
    "limit_pct": 0.49
  }
}
```

**Ví dụ node nhóm 5:**

```json
{
  "label": "AGM_Group",
  "company_code": "MIG",
  "year": 2023,
  "group_code": 5,
  "group_name": "Ownership & Strategic Stakeholders",
  "score": 82.0,
  "score_band": "good",
  "data_json": "{...JSON như trên...}",
  "notes": "Co dong chien luoc on dinh, ty le so huu ngoai con du room."
}
```

---

### 2.6. Nhóm 6 – Kế hoạch đầu tư & Chiến lược (`group_code = 6`)

```json
{
  "business_plan": {
    "target_premium_growth_pct": 0.15,
    "target_profit_growth_pct": 0.18,
    "key_segments": ["Bao hiem xe co gioi", "Bao hiem suc khoe"],
    "distribution_strategy": ["Mo rong kenh bancassurance", "Tang cuong kenh online"]
  },
  "investment_projects": [
    {
      "name": "He thong core insurance moi",
      "capex": 200000000000,
      "timeline": "2024-2026",
      "expected_roi": 0.18
    },
    {
      "name": "Mo rong mang luoi chi nhanh",
      "capex": 50000000000,
      "timeline": "2024-2025",
      "expected_roi": 0.15
    }
  ],
  "digital_transformation": {
    "initiatives": ["Mobile app khach hang", "He thong CRM moi"],
    "budget": 30000000000
  }
}
```

**Ví dụ node nhóm 6:**

```json
{
  "label": "AGM_Group",
  "company_code": "MIG",
  "year": 2023,
  "group_code": 6,
  "group_name": "Kế hoạch đầu tư & Chiến lược",
  "score": 85.0,
  "score_band": "good",
  "data_json": "{...JSON như trên...}",
  "notes": "Ke hoach tang truong cao, tap trung so hoa va mo rong kenh."
}
```

---

### 2.7. Nhóm 7 – Rủi ro & Quản trị rủi ro (`group_code = 7`)

```json
{
  "underwriting_risk": {
    "loss_ratio_recent": 0.52,
    "loss_ratio_target": 0.5,
    "comment": "Loss ratio tang nhe do claim suc khoe gia tang."
  },
  "market_risk": {
    "bond_portfolio_duration": 4.5,
    "equity_pct_of_investment": 0.25,
    "stress_test_comment": "Danh muc co kha nang chiu duoc giam 10% thi truong chung."
  },
  "liquidity_risk": {
    "cash_and_equivalents": 300000000000,
    "short_term_obligations": 150000000000,
    "liquidity_ratio": 2.0
  },
  "operational_risk": {
    "major_incidents": 0,
    "internal_control_notes": "He thong KSNB duoc BKS danh gia la phu hop."
  },
  "reinsurance_program": {
    "retention_limit": 5000000000,
    "main_reinsurers": ["Swiss Re", "Munich Re"],
    "comment": "Chuong trinh tai bao hiem on dinh, doi tac rating cao."
  }
}
```

**Ví dụ node nhóm 7:**

```json
{
  "label": "AGM_Group",
  "company_code": "MIG",
  "year": 2023,
  "group_code": 7,
  "group_name": "Rủi ro & Quản trị rủi ro",
  "score": 78.0,
  "score_band": "good",
  "data_json": "{...JSON như trên...}",
  "notes": "Loss ratio tang nhe, nhung chuong trinh tai bao hiem vung."
}
```

---

## 3. Edge Types (Relationships)

Ontology v1.1 định nghĩa **3 loại quan hệ** trong subgraph ĐHĐCĐ:

1. `(:Company)-[:BELONGS_TO]->(:Industry)`  
2. `(:Company)-[:HAS_AGM]->(:AGM_Year)`  
3. `(:AGM_Year)-[:HAS_CRITERIA_GROUP]->(:AGM_Group)`  

Không có edge nào khác trong scope của file này.

---

### 3.1. `(:Company)-[:BELONGS_TO]->(:Industry)`

- **Tên:** `BELONGS_TO`
- **Từ:** `Company`
- **Đến:** `Industry`
- **Cardinality:**  
  - 1 `Company` → 1 `Industry` (thường là 1, nếu mô hình đơn giản).  
  - 1 `Industry` ← 0..N `Company`.

**Ý nghĩa:**  
Công ty X thuộc ngành Y.

**Thuộc tính (relationship):**  
Không dùng thuộc tính; chỉ là quan hệ phân loại.

**Ví dụ Cypher:**

```cypher
MERGE (i:Industry {code: "INS_NONLIFE"})
ON CREATE SET
  i.name_vi = "Bảo hiểm phi nhân thọ";

MERGE (c:Company {code: "MIG"})
ON CREATE SET
  c.name_vi = "CTCP Bảo hiểm Quân đội";

MERGE (c)-[:BELONGS_TO]->(i);
```

---

### 3.2. `(:Company)-[:HAS_AGM]->(:AGM_Year)`

- **Tên:** `HAS_AGM`
- **Từ:** `Company`
- **Đến:** `AGM_Year`
- **Cardinality:**  
  - 1 `Company` → 0..N `AGM_Year`.  
  - 1 `AGM_Year` → đúng 1 `Company`.

**Ý nghĩa:**  
Công ty X có kỳ ĐHĐCĐ năm Y.

**Thuộc tính (relationship):**  
Không cần thuộc tính, vì `year` đã nằm trong node `AGM_Year`.

**Ví dụ Cypher:**

```cypher
MATCH (c:Company {code: "MIG"})
MERGE (ag23:AGM_Year {company_code: "MIG", year: 2023})
ON CREATE SET
  ag23.meeting_date = "2024-04-20",
  ag23.meeting_type = "thuong_nien";

MERGE (c)-[:HAS_AGM]->(ag23);
```

---

### 3.3. `(:AGM_Year)-[:HAS_CRITERIA_GROUP]->(:AGM_Group)`

- **Tên:** `HAS_CRITERIA_GROUP`
- **Từ:** `AGM_Year`
- **Đến:** `AGM_Group`
- **Cardinality:**  
  - 1 `AGM_Year` → 0..7 `AGM_Group`.  
  - 1 `AGM_Group` → đúng 1 `AGM_Year`.

**Ý nghĩa:**  
Kỳ ĐHĐCĐ năm Y của công ty X có nhóm tiêu chí Z (Governance, ESOP, Payout…).

**Thuộc tính (relationship):**  
Không dùng thuộc tính; mọi thông tin nằm trong `AGM_Group`.

**Ví dụ Cypher:**

```cypher
MATCH (ag23:AGM_Year {company_code: "MIG", year: 2023})

// Nhóm 1 - Governance cứng
MERGE (g1:AGM_Group {
  company_code: "MIG",
  year: 2023,
  group_code: 1
})
ON CREATE SET
  g1.group_name = "Governance cứng";

MERGE (ag23)-[:HAS_CRITERIA_GROUP]->(g1);

// Nhóm 3 - Payout
MERGE (g3:AGM_Group {
  company_code: "MIG",
  year: 2023,
  group_code: 3
})
ON CREATE SET
  g3.group_name = "Payout – Cổ tức & phân phối lợi nhuận";

MERGE (ag23)-[:HAS_CRITERIA_GROUP]->(g3);
```

---

## 4. Ví dụ Subgraph ĐHĐCĐ đầy đủ cho MIG – Năm 2023

Dưới đây là ví dụ subgraph **đầy đủ** trong scope ontology v1.1 cho công ty MIG năm 2023:

```text
(Industry {code:"INS_NONLIFE"})
      ^
      |
   [:BELONGS_TO]
      |
(Company {code:"MIG"})
      |
      +--[:HAS_AGM]-->
                (AGM_Year {company_code:"MIG", year:2023})
                          |
                          +--[:HAS_CRITERIA_GROUP]--> (AGM_Group {group_code:1, group_name:"Governance cứng"})
                          |
                          +--[:HAS_CRITERIA_GROUP]--> (AGM_Group {group_code:2, group_name:"Incentive – ESOP & Quỹ"})
                          |
                          +--[:HAS_CRITERIA_GROUP]--> (AGM_Group {group_code:3, group_name:"Payout – Cổ tức & LNST"})
                          |
                          +--[:HAS_CRITERIA_GROUP]--> (AGM_Group {group_code:4, group_name:"Capital Actions"})
                          |
                          +--[:HAS_CRITERIA_GROUP]--> (AGM_Group {group_code:5, group_name:"Ownership & Stakeholders"})
                          |
                          +--[:HAS_CRITERIA_GROUP]--> (AGM_Group {group_code:6, group_name:"Kế hoạch & Chiến lược"})
                          |
                          +--[:HAS_CRITERIA_GROUP]--> (AGM_Group {group_code:7, group_name:"Rủi ro & Quản trị rủi ro"})
```

Tất cả node/edge trong subgraph ĐHĐCĐ đã được định nghĩa đầy đủ về:

- Label
- Bộ property
- Ví dụ instance cụ thể
- Quan hệ và ví dụ Cypher tạo quan hệ

Có thể dùng file này làm **spec ontology chính thức** cho phần ĐHĐCĐ khi triển khai Neo4j / Arrows / generator.
