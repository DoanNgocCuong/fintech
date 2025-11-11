CREATE TABLE balance_sheet_raw (
    stock_year varchar(255),      -- cột mã - năm, kiểu chuỗi đủ lớn chứa mã và năm
    json_raw jsonb           -- cột json-raw, kiểu jsonb để lưu dữ liệu dạng JSON hiệu quả
);


CREATE TABLE balance_sheet_raw (
    stock varchar(255),        -- mã chứng khoán, kiểu chuỗi
    year integer,              -- năm, kiểu số nguyên hoặc có thể dùng varchar nếu cần lưu dạng chuỗi (ví dụ "2025")
    json_raw jsonb             -- dữ liệu dạng JSON
);
