import psycopg2
import sys

# URL from .env (root)
DB_URL = "postgresql://ailoos_coordinator:TJfr6Lj5keD3SN7Dbbz20WbF_aNMXCel@localhost:5432/ailoos_coordinator"

def inspect_schema():
    print(f"Connecting to {DB_URL}...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Check 'user' table columns
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'user' OR table_name = 'User';
        """)
        columns = cur.fetchall()
        
        if not columns:
            print("❌ 'user' table NOT FOUND")
        else:
            print("Found 'user' table columns:")
            for col in columns:
                print(f" - {col[0]} ({col[1]}), Nullable: {col[2]}")

        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    inspect_schema()
