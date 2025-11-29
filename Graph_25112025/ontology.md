# Ontology KG cho FinAI (Neo4j)

## 1. Node Labels

### Industry

-   **industry_id**
-   **ten_nganh**
-   **mo_ta**
-   **level**
-   **ma_chuan**

### Company

-   **company_id**
-   **ma_ck**
-   **ten_day_du**
-   **ten_viet_tat**
-   **ngay_niem_yet**
-   **san_giao_dich**
-   **trang_thai**

### FS_Report

-   **fs_report_id**
-   **ky_bao_cao**
-   **nam**
-   **ngay_bat_dau**
-   **ngay_ket_thuc**
-   **loai_bao_cao**
-   **don_vi_tinh**
-   **nguon_du_lieu**

### FS_Section

-   **fs_section_id**
-   **loai_section**
-   **tieu_de**

### FS_LineItem

-   **fs_line_item_id**
-   **ma_chi_tieu**
-   **ten_chi_tieu**
-   **giatri**
-   **ky_bao_cao**
-   **nam**
-   **note_ref**

### Metric

-   **metric_id**
-   **ten_metric**
-   **mo_ta**
-   **cong_thuc**
-   **loai**
-   **don_vi**

### MetricValue

-   **metric_value_id**
-   **gia_tri**
-   **ky_bao_cao**
-   **nam**
-   **method**

### Fact

-   **fact_id**
-   **loai_fact**
-   **tieu_de**
-   **noi_dung_tom_tat**
-   **nam**
-   **tag**

### Document

-   **document_id**
-   **tieu_de**
-   **nam**
-   **loai_tai_lieu**
-   **nguon**
-   **file_path**

### Page

-   **page_id**
-   **page_number**
-   **text_raw**
-   **embedding_id**

## 2. Relationship Types

-   `Company —BELONGS_TO→ Industry`
-   `Company —HAS_FS→ FS_Report`
-   `FS_Report —HAS_SECTION→ FS_Section`
-   `FS_Section —HAS_LINE_ITEM→ FS_LineItem`
-   `Company —HAS_METRIC→ MetricValue`
-   `MetricValue —OF_METRIC→ Metric`
-   `MetricValue —DERIVED_FROM→ FS_LineItem`
-   `Company —HAS_FACT→ Fact`
-   `Fact —CITED_FROM→ Document`
-   `Document —HAS_PAGE→ Page`
-   `Fact —LOCATED_AT_PAGE→ Page`

## 3. Cypher Constraint Mẫu

\`\`\`cypher CREATE CONSTRAINT industry_id_unique IF NOT EXISTS FOR
(i:Industry) REQUIRE i.industry_id IS UNIQUE; \`\`\`
