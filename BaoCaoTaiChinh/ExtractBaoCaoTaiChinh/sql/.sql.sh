# Bảng 
```sql
CREATE TABLE company (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(255) NOT NULL,
    use_legal VARCHAR(255)
);

INSERT INTO company (company_name, industry, use_legal) VALUES
('BIC', 'Bảo hiểm', 'TT232_2012'),
('BMI', 'Bảo hiểm', 'TT232_2012'),
('BVH', 'Bảo hiểm', 'TT199_2014'),
('MIG', 'Bảo hiểm', 'TT232_2012'),
('PGI', 'Bảo hiểm', 'TT232_2012');

```
