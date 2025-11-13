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


def create_table_if_not_exists(conn, table_name: str = None) -> None:
    """
    Create table if not exists.
    
    Args:
        conn: Database connection
        table_name: Table name to create. If None, uses global TABLE_NAME.
    """
    if table_name is None:
        table_name = TABLE_NAME
    
    cursor = conn.cursor()
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS "{table_name}" (
        id SERIAL PRIMARY KEY,
        stock VARCHAR(10) NOT NULL,
        year INTEGER NOT NULL,
        quarter INTEGER,
        source_filename VARCHAR(500),
        json_raw JSONB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(stock, year, quarter)
    );
    """
    try:
        cursor.execute(create_table_query)
        conn.commit()
        # Add columns if table exists but columns don't exist
        try:
            # Check if quarter column exists
            check_quarter_query = f"""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = 'quarter'
            """
            cursor.execute(check_quarter_query)
            quarter_exists = cursor.fetchone()
            
            if not quarter_exists:
                # Add quarter column
                alter_add_quarter = f'ALTER TABLE "{table_name}" ADD COLUMN quarter INTEGER'
                cursor.execute(alter_add_quarter)
                
                # Find and drop old unique constraint (stock, year)
                find_constraint_query = f"""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = '{table_name}' 
                AND constraint_type = 'UNIQUE'
                AND constraint_name LIKE '%stock%year%'
                """
                cursor.execute(find_constraint_query)
                old_constraints = cursor.fetchall()
                
                for (constraint_name,) in old_constraints:
                    drop_constraint = f'ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS "{constraint_name}"'
                    cursor.execute(drop_constraint)
                
                # Add new unique constraint with quarter
                add_constraint = f"""
                ALTER TABLE "{table_name}" 
                ADD CONSTRAINT "{table_name}_stock_year_quarter_key" UNIQUE(stock, year, quarter)
                """
                cursor.execute(add_constraint)
                conn.commit()
            
            # Check if source_filename column exists
            check_filename_query = f"""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = 'source_filename'
            """
            cursor.execute(check_filename_query)
            filename_exists = cursor.fetchone()
            
            if not filename_exists:
                # Add source_filename column
                alter_add_filename = f'ALTER TABLE "{table_name}" ADD COLUMN source_filename VARCHAR(500)'
                cursor.execute(alter_add_filename)
                conn.commit()
        except Exception as alter_e:
            # If alter fails, it's okay - table might be new or constraint might already exist
            conn.rollback()
            # Try to continue anyway
            pass
        try:
            print(f"  ✓ Table '{table_name}' is ready")
        except UnicodeEncodeError:
            print(f"  Table '{table_name}' is ready")
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
    quarter: Optional[int] = None,
    overwrite: bool = False,
    json_data: Optional[Dict[str, Any]] = None,
    table_name: Optional[str] = None,
    source_filename: Optional[str] = None,
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
        # Use provided table_name or default
        target_table = table_name if table_name else TABLE_NAME
        
        # Tạo bảng nếu chưa tồn tại
        create_table_if_not_exists(conn, table_name=target_table)

        cursor = conn.cursor()

        # Đọc JSON nếu cần
        if json_data is None:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

        # Validate stock/year
        if stock is None or year is None:
            raise ValueError("stock and year are required when uploading to DB")

        # Get source filename if not provided
        if source_filename is None and json_path is not None:
            source_filename = json_path.name

        # Kiểm tra record (with quarter if provided)
        # Use schema-qualified table name and ensure proper parameter binding
        if quarter is not None:
            check_query = f'SELECT 1 FROM "{target_table}" WHERE stock = %s AND year = %s AND quarter = %s LIMIT 1'
            cursor.execute(check_query, (str(stock), int(year), int(quarter)))
        else:
            check_query = f'SELECT 1 FROM "{target_table}" WHERE stock = %s AND year = %s AND quarter IS NULL LIMIT 1'
            cursor.execute(check_query, (str(stock), int(year)))
        existing = cursor.fetchone()

        if existing and not overwrite:
            quarter_str = f", quarter={quarter}" if quarter is not None else ", quarter=NULL"
            try:
                print(f"  ⚠ Record already exists for stock={stock}, year={year}{quarter_str}. Skipping...")
            except UnicodeEncodeError:
                print(f"  Record already exists for stock={stock}, year={year}{quarter_str}. Skipping...")
            print(f"    Use overwrite=True to update existing record")
            return True

        if existing and overwrite:
            if quarter is not None:
                update_query = f"""
                UPDATE "{target_table}"
                SET json_raw = %s, source_filename = %s, updated_at = CURRENT_TIMESTAMP
                WHERE stock = %s AND year = %s AND quarter = %s
                """
                cursor.execute(update_query, (PsycopgJson(json_data), source_filename, str(stock), int(year), int(quarter)))
            else:
                update_query = f"""
                UPDATE "{target_table}"
                SET json_raw = %s, source_filename = %s, updated_at = CURRENT_TIMESTAMP
                WHERE stock = %s AND year = %s AND quarter IS NULL
                """
                cursor.execute(update_query, (PsycopgJson(json_data), source_filename, str(stock), int(year)))
            try:
                print(f"  ✓ Updated existing record")
            except UnicodeEncodeError:
                print(f"  Updated existing record")
        else:
            if quarter is not None:
                insert_query = f"""
                INSERT INTO "{target_table}" (stock, year, quarter, source_filename, json_raw)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (str(stock), int(year), int(quarter), source_filename, PsycopgJson(json_data)))
            else:
                insert_query = f"""
                INSERT INTO "{target_table}" (stock, year, source_filename, json_raw)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_query, (str(stock), int(year), source_filename, PsycopgJson(json_data)))
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
