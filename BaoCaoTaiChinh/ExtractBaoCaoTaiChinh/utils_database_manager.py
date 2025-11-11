import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

try:
    import psycopg2
    from psycopg2.extras import Json as PsycopgJson
except ImportError:
    psycopg2 = None
    PsycopgJson = None


# Database configuration
DB_CONFIG: Dict[str, Any] = {
    'host': '103.253.20.30',
    'port': 29990,
    'database': 'financial-reporting-database',
    'user': 'postgres',
    'password': 'postgres',
}

TABLE_NAME = 'balance_sheet_raw'


def connect() -> "psycopg2.extensions.connection":
    if psycopg2 is None:
        raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
    return psycopg2.connect(**DB_CONFIG)


def create_table_if_not_exists(conn) -> None:
    cursor = conn.cursor()
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id SERIAL PRIMARY KEY,
        stock VARCHAR(10) NOT NULL,
        year INTEGER NOT NULL,
        json_raw JSONB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(stock, year)
    );
    """
    try:
        cursor.execute(create_table_query)
        conn.commit()
        try:
            print(f"  ✓ Table '{TABLE_NAME}' is ready")
        except UnicodeEncodeError:
            print(f"  Table '{TABLE_NAME}' is ready")
    except Exception as e:
        conn.rollback()
        try:
            print(f"  ⚠ Warning: Could not create table: {e}")
        except UnicodeEncodeError:
            print(f"  Warning: Could not create table: {e}")
    finally:
        cursor.close()


def upload_json_to_db(
    json_file: Optional[str] = None,
    stock: Optional[str] = None,
    year: Optional[int] = None,
    overwrite: bool = False,
    json_data: Optional[Dict[str, Any]] = None,
) -> bool:
    if psycopg2 is None:
        raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")

    json_path: Optional[Path] = Path(json_file) if json_file else None

    if json_data is None:
        if json_path is None or not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file}")

    # Kết nối database
    try:
        conn = connect()
        try:
            print(f"  ✓ Connected to database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        except UnicodeEncodeError:
            print(f"  Connected to database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    except Exception as e:
        try:
            print(f"  ✗ Error connecting to database: {e}")
        except UnicodeEncodeError:
            print(f"  Error connecting to database: {e}")
        return False

    cursor = None
    try:
        # Tạo bảng nếu chưa tồn tại
        create_table_if_not_exists(conn)

        cursor = conn.cursor()

        # Đọc JSON nếu cần
        if json_data is None:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

        # Validate stock/year
        if stock is None or year is None:
            raise ValueError("stock and year are required when uploading to DB")

        # Kiểm tra record
        check_query = f"SELECT 1 FROM {TABLE_NAME} WHERE stock = %s AND year = %s LIMIT 1"
        cursor.execute(check_query, (stock, year))
        existing = cursor.fetchone()

        if existing and not overwrite:
            try:
                print(f"  ⚠ Record already exists for stock={stock}, year={year}. Skipping...")
            except UnicodeEncodeError:
                print(f"  Record already exists for stock={stock}, year={year}. Skipping...")
            print(f"    Use overwrite=True to update existing record")
            return True

        if existing and overwrite:
            update_query = f"""
            UPDATE {TABLE_NAME}
            SET json_raw = %s, updated_at = CURRENT_TIMESTAMP
            WHERE stock = %s AND year = %s
            """
            cursor.execute(update_query, (PsycopgJson(json_data), stock, year))
            try:
                print(f"  ✓ Updated existing record")
            except UnicodeEncodeError:
                print(f"  Updated existing record")
        else:
            insert_query = f"""
            INSERT INTO {TABLE_NAME} (stock, year, json_raw)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (stock, year, PsycopgJson(json_data)))
            try:
                print(f"  ✓ Inserted new record")
            except UnicodeEncodeError:
                print(f"  Inserted new record")

        conn.commit()
        try:
            print(f"  ✓ Successfully uploaded to database")
        except UnicodeEncodeError:
            print(f"  Successfully uploaded to database")
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        try:
            print(f"  ✗ Error uploading to database: {e}")
        except UnicodeEncodeError:
            print(f"  Error uploading to database: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
