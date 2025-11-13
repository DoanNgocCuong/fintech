"""
Test script to create income_statement_raw table in database.
This script will:
1. Connect to database
2. Create table if not exists
3. Verify table creation
"""

from utils_database_manager import connect, create_table_if_not_exists, DB_CONFIG

TABLE_NAME = 'income_statement_raw'

def main():
    print("=" * 80)
    print("TEST: Create income_statement_raw table")
    print("=" * 80)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Database name: {DB_CONFIG['database']}")
    print(f"Table name: {TABLE_NAME}")
    print("=" * 80)
    
    try:
        # Connect to database
        print("\n1. Connecting to database...")
        conn = connect()
        try:
            print("   ✓ Connected successfully")
        except UnicodeEncodeError:
            print("   [OK] Connected successfully")
        
        # Create table
        print(f"\n2. Creating table '{TABLE_NAME}'...")
        create_table_if_not_exists(conn, table_name=TABLE_NAME)
        
        # Verify table exists
        print(f"\n3. Verifying table '{TABLE_NAME}' exists...")
        cursor = conn.cursor()
        check_table_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        );
        """
        cursor.execute(check_table_query, (TABLE_NAME,))
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            try:
                print(f"   ✓ Table '{TABLE_NAME}' exists")
            except UnicodeEncodeError:
                print(f"   [OK] Table '{TABLE_NAME}' exists")
            
            # Get table structure
            print(f"\n4. Getting table structure...")
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (TABLE_NAME,))
            columns = cursor.fetchall()
            
            print(f"   Columns:")
            for col_name, data_type, is_nullable in columns:
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                print(f"     - {col_name}: {data_type} {nullable}")
            
            # Check constraints
            print(f"\n5. Checking constraints...")
            cursor.execute(f"""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = %s;
            """, (TABLE_NAME,))
            constraints = cursor.fetchall()
            
            for constraint_name, constraint_type in constraints:
                print(f"     - {constraint_name}: {constraint_type}")
        else:
            try:
                print(f"   ✗ Table '{TABLE_NAME}' does NOT exist")
            except UnicodeEncodeError:
                print(f"   [ERROR] Table '{TABLE_NAME}' does NOT exist")
            print("   This might indicate a permission issue or the table was not created.")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("Test completed!")
        print("=" * 80)
        
    except Exception as e:
        try:
            print(f"\n✗ Error: {e}")
        except UnicodeEncodeError:
            print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()

