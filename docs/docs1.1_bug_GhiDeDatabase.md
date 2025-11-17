
# 2h để fix 1 bug về ghi đè dữ liệu. 

* **`quarter = 5`** là dữ liệu **ĐÚNG** (5.5 nghìn tỷ) ✅
* **`quarter = NULL`** là dữ liệu **SAI** (6.6 triệu) ❌
* Nhưng API đang để `NULL` ghi đè lên `5`

---

=> Điều này dẫn đến: 

1. DB dữ liệu khác
2. Nhưng khi mapping ra UI thì nó lại bị sai.

---

## 1.1 Các giải pháp đã thử 

1. Check lại toàn bộ luồng đẩy XLSX -> DB xem đã ghi đè chưa? => Bật ghi đè rùi.
2. Xoá toàn bộ DB và chạy lại => vẫn bị
3. Check DB của BIC - 2024 - 5 trong DB khác và API get data lại khác.
4. Check API get data xem có bị bug gì ko, cho Cursor code các kiểu update, code kiểu khác đi, tư duy để code kiểu khác, map jSON, ... vẫn bug
5. Cho Cursor rà bug mãi ko được, sau phải 1h sau chuyển sang GenSpark thì 1 phát nó chỉ ra vấn đề GHI ĐÈ ngay.

---

## 1. VẤN ĐỀ (CẬP NHẬT)

**Dữ liệu Q5-2024 bị sai:**

* Database `quarter = 5`: `5,524,525,927,458` (5.5 nghìn tỷ) ✅ **ĐÚNG**
* Database `quarter = NULL`: `6,669,734` (6.6 triệu) ❌ **SAI**
* API trả về: `6,669,734` ❌ **Lấy giá trị SAI**

---

## 2. NGUYÊN NHÂN (CẬP NHẬT)

### 🔴 **Thứ tự xử lý trong loop:**

```python
# Query sort: ORDER BY year DESC, quarter DESC NULLS LAST
# → Records quarter=5 đứng TRƯỚC, NULL đứng SAU

for year, quarter, json_raw, created_at in rows:
    if quarter is None:
        quarter = 5
    period_label = f"Q{quarter}-{year}"
    data_by_period[period_label] = json.loads(json_raw)
```

**Kịch bản lỗi:**

```
Loop 1: quarter=5    → Q5-2024 → data = 5,524,525,927,458 ✅
Loop 2: quarter=NULL → Q5-2024 → data = 6,669,734 ❌ (GHI ĐÈ!)
```

**`NULLS LAST`** trong SQL **NHƯNG** loop vẫn ghi đè vì không skip duplicate!

---

## 3. GIẢI PHÁP: Xóa records `quarter = NULL` trong database

### **Test API:**

```bash
curl "http://localhost:8000/api/income-statement/table-data?stock=BIC"
```

**Kết quả mong đợi:**

```json
{
  "indicators": [
    {
      "key": "01_doanh_thu_phi_bao_hiem",
      "values": {
        "Q5-2024": 5524525927458.0,  // ✅ ĐÚNG RỒI!
        "Q4-2024": 5523780421070.0,
        ...
      }
    }
  ]
}
```

---

---

## 6. TÓM TẮT CUỐI CÙNG

| Vấn đề                                             | Nguyên nhân                                                                                          | Giải pháp                                                                                                 |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| Q5-2024 hiển thị 6.6 triệu thay vì 5.5 nghìn tỷ | Database có cả `quarter=5`(đúng) và `quarter=NULL`(sai),`NULL`ghi đè lên `5`trong loop | **Xóa tất cả records có `quarter=NULL`** , thêm constraint `NOT NULL`và `BETWEEN 1 AND 5` |

**Convention chuẩn sau khi fix:**

* `quarter = 1, 2, 3, 4` → Quarterly reports
* `quarter = 5` → Year-end report (báo cáo năm)
* ❌ **KHÔNG cho phép** `quarter = NULL`
