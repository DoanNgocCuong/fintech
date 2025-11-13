-- ============================================================================
-- SQL Queries để kiểm tra dữ liệu Financial Reports
-- ============================================================================
-- Database: financial-reporting-database
-- Host: 103.253.20.30:29990
-- ============================================================================

-- 1. TỔNG SỐ RECORDS TRONG MỖI BẢNG
-- ============================================================================
SELECT 
    'income_statement_raw' AS table_name,
    COUNT(*) AS total_records
FROM "income_statement_raw"
UNION ALL
SELECT 
    'balance_sheet_raw' AS table_name,
    COUNT(*) AS total_records
FROM "balance_sheet_raw"
UNION ALL
SELECT 
    'cash_flow_statement_raw' AS table_name,
    COUNT(*) AS total_records
FROM "cash_flow_statement_raw"
ORDER BY table_name;


-- 2. TOP 10 STOCKS CÓ NHIỀU RECORDS NHẤT (INCOME STATEMENT)
-- ============================================================================
SELECT 
    stock,
    COUNT(*) AS record_count,
    MIN(year) AS first_year,
    MAX(year) AS last_year
FROM "income_statement_raw"
GROUP BY stock
ORDER BY record_count DESC
LIMIT 10;


-- 3. TOP 10 STOCKS CÓ NHIỀU RECORDS NHẤT (BALANCE SHEET)
-- ============================================================================
SELECT 
    stock,
    COUNT(*) AS record_count,
    MIN(year) AS first_year,
    MAX(year) AS last_year
FROM "balance_sheet_raw"
GROUP BY stock
ORDER BY record_count DESC
LIMIT 10;


-- 4. TOP 10 STOCKS CÓ NHIỀU RECORDS NHẤT (CASH FLOW)
-- ============================================================================
SELECT 
    stock,
    COUNT(*) AS record_count,
    MIN(year) AS first_year,
    MAX(year) AS last_year
FROM "cash_flow_statement_raw"
GROUP BY stock
ORDER BY record_count DESC
LIMIT 10;


-- 5. RECORDS THEO NĂM (INCOME STATEMENT)
-- ============================================================================
SELECT 
    year,
    COUNT(*) AS record_count,
    COUNT(DISTINCT stock) AS unique_stocks
FROM "income_statement_raw"
GROUP BY year
ORDER BY year DESC;


-- 6. RECORDS THEO NĂM (BALANCE SHEET)
-- ============================================================================
SELECT 
    year,
    COUNT(*) AS record_count,
    COUNT(DISTINCT stock) AS unique_stocks
FROM "balance_sheet_raw"
GROUP BY year
ORDER BY year DESC;


-- 7. RECORDS THEO NĂM (CASH FLOW)
-- ============================================================================
SELECT 
    year,
    COUNT(*) AS record_count,
    COUNT(DISTINCT stock) AS unique_stocks
FROM "cash_flow_statement_raw"
GROUP BY year
ORDER BY year DESC;


-- 8. RECORDS THEO QUARTER (INCOME STATEMENT)
-- ============================================================================
SELECT 
    quarter,
    COUNT(*) AS record_count,
    COUNT(DISTINCT stock) AS unique_stocks
FROM "income_statement_raw"
WHERE quarter IS NOT NULL
GROUP BY quarter
ORDER BY quarter;


-- 9. CHECK MỘT STOCK CỤ THỂ (VD: PGI)
-- ============================================================================
SELECT 
    'Income Statement' AS report_type,
    stock,
    year,
    quarter,
    source_filename,
    created_at
FROM "income_statement_raw"
WHERE stock = 'PGI'
ORDER BY year DESC, quarter DESC
LIMIT 20;

SELECT 
    'Balance Sheet' AS report_type,
    stock,
    year,
    quarter,
    source_filename,
    created_at
FROM "balance_sheet_raw"
WHERE stock = 'PGI'
ORDER BY year DESC, quarter DESC
LIMIT 20;

SELECT 
    'Cash Flow' AS report_type,
    stock,
    year,
    quarter,
    source_filename,
    created_at
FROM "cash_flow_statement_raw"
WHERE stock = 'PGI'
ORDER BY year DESC, quarter DESC
LIMIT 20;


-- 10. CHECK STOCKS CÓ ĐẦY ĐỦ 3 LOẠI BÁO CÁO CHO NĂM 2024
-- ============================================================================
SELECT 
    is_table.stock,
    is_table.year,
    is_table.quarter,
    CASE WHEN is_table.stock IS NOT NULL THEN 'Yes' ELSE 'No' END AS has_income_statement,
    CASE WHEN bs_table.stock IS NOT NULL THEN 'Yes' ELSE 'No' END AS has_balance_sheet,
    CASE WHEN cf_table.stock IS NOT NULL THEN 'Yes' ELSE 'No' END AS has_cash_flow
FROM "income_statement_raw" AS is_table
LEFT JOIN "balance_sheet_raw" AS bs_table 
    ON is_table.stock = bs_table.stock 
    AND is_table.year = bs_table.year 
    AND COALESCE(is_table.quarter, 0) = COALESCE(bs_table.quarter, 0)
LEFT JOIN "cash_flow_statement_raw" AS cf_table 
    ON is_table.stock = cf_table.stock 
    AND is_table.year = cf_table.year 
    AND COALESCE(is_table.quarter, 0) = COALESCE(cf_table.quarter, 0)
WHERE is_table.year = 2024
ORDER BY is_table.stock, is_table.quarter;


-- 11. RECORDS MỚI NHẤT (INCOME STATEMENT)
-- ============================================================================
SELECT 
    stock,
    year,
    quarter,
    source_filename,
    created_at,
    updated_at
FROM "income_statement_raw"
ORDER BY created_at DESC
LIMIT 10;


-- 12. RECORDS MỚI NHẤT (BALANCE SHEET)
-- ============================================================================
SELECT 
    stock,
    year,
    quarter,
    source_filename,
    created_at,
    updated_at
FROM "balance_sheet_raw"
ORDER BY created_at DESC
LIMIT 10;


-- 13. RECORDS MỚI NHẤT (CASH FLOW)
-- ============================================================================
SELECT 
    stock,
    year,
    quarter,
    source_filename,
    created_at,
    updated_at
FROM "cash_flow_statement_raw"
ORDER BY created_at DESC
LIMIT 10;


-- 14. KIỂM TRA DUPLICATE RECORDS (INCOME STATEMENT)
-- ============================================================================
SELECT 
    stock,
    year,
    quarter,
    COUNT(*) AS duplicate_count
FROM "income_statement_raw"
GROUP BY stock, year, quarter
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;


-- 15. KIỂM TRA RECORDS THIẾU STOCK HOẶC YEAR
-- ============================================================================
SELECT 
    'income_statement_raw' AS table_name,
    COUNT(*) AS null_stock_or_year
FROM "income_statement_raw"
WHERE stock IS NULL OR year IS NULL

UNION ALL

SELECT 
    'balance_sheet_raw' AS table_name,
    COUNT(*) AS null_stock_or_year
FROM "balance_sheet_raw"
WHERE stock IS NULL OR year IS NULL

UNION ALL

SELECT 
    'cash_flow_statement_raw' AS table_name,
    COUNT(*) AS null_stock_or_year
FROM "cash_flow_statement_raw"
WHERE stock IS NULL OR year IS NULL;


-- 16. THỐNG KÊ JSON RAW SIZE (BYTES)
-- ============================================================================
SELECT 
    'income_statement_raw' AS table_name,
    COUNT(*) AS total_records,
    AVG(LENGTH(json_raw::text)) AS avg_json_size,
    MIN(LENGTH(json_raw::text)) AS min_json_size,
    MAX(LENGTH(json_raw::text)) AS max_json_size
FROM "income_statement_raw"

UNION ALL

SELECT 
    'balance_sheet_raw' AS table_name,
    COUNT(*) AS total_records,
    AVG(LENGTH(json_raw::text)) AS avg_json_size,
    MIN(LENGTH(json_raw::text)) AS min_json_size,
    MAX(LENGTH(json_raw::text)) AS max_json_size
FROM "balance_sheet_raw"

UNION ALL

SELECT 
    'cash_flow_statement_raw' AS table_name,
    COUNT(*) AS total_records,
    AVG(LENGTH(json_raw::text)) AS avg_json_size,
    MIN(LENGTH(json_raw::text)) AS min_json_size,
    MAX(LENGTH(json_raw::text)) AS max_json_size
FROM "cash_flow_statement_raw";


-- 17. TẤT CẢ STOCKS CÓ TRONG DATABASE
-- ============================================================================
SELECT DISTINCT stock 
FROM "income_statement_raw"
UNION
SELECT DISTINCT stock 
FROM "balance_sheet_raw"
UNION
SELECT DISTINCT stock 
FROM "cash_flow_statement_raw"
ORDER BY stock;


-- 18. TẤT CẢ NĂM CÓ TRONG DATABASE
-- ============================================================================
SELECT DISTINCT year 
FROM "income_statement_raw"
UNION
SELECT DISTINCT year 
FROM "balance_sheet_raw"
UNION
SELECT DISTINCT year 
FROM "cash_flow_statement_raw"
ORDER BY year DESC;


-- 19. XEM CHI TIẾT JSON CỦA MỘT RECORD (INCOME STATEMENT)
-- ============================================================================
-- Thay PGI, 2024, 5 bằng stock, year, quarter muốn xem
SELECT 
    stock,
    year,
    quarter,
    json_raw
FROM "income_statement_raw"
WHERE stock = 'PGI' AND year = 2024 AND quarter = 5
LIMIT 1;


-- 20. SO SÁNH SỐ LƯỢNG RECORDS GIỮA 3 BẢNG
-- ============================================================================
WITH stats AS (
    SELECT 
        'income_statement_raw' AS table_name,
        COUNT(*) AS total_records,
        COUNT(DISTINCT stock) AS unique_stocks,
        COUNT(DISTINCT year) AS unique_years
    FROM "income_statement_raw"
    UNION ALL
    SELECT 
        'balance_sheet_raw' AS table_name,
        COUNT(*) AS total_records,
        COUNT(DISTINCT stock) AS unique_stocks,
        COUNT(DISTINCT year) AS unique_years
    FROM "balance_sheet_raw"
    UNION ALL
    SELECT 
        'cash_flow_statement_raw' AS table_name,
        COUNT(*) AS total_records,
        COUNT(DISTINCT stock) AS unique_stocks,
        COUNT(DISTINCT year) AS unique_years
    FROM "cash_flow_statement_raw"
)
SELECT * FROM stats
ORDER BY table_name;

