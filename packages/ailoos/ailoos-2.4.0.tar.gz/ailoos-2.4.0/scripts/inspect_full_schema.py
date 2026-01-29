import psycopg2
import sys

# URL from .env (root)
DB_URL = "postgresql://ailoos_coordinator:TJfr6Lj5keD3SN7Dbbz20WbF_aNMXCel@localhost:5432/ailoos_coordinator"

def inspect_full_schema():
    print(f"Connecting to {DB_URL}...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        tables = ['user', 'account', 'session']
        
        for t in tables:
            print(f"\n--- Table: {t} ---")
            cur.execute(f"""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = '{t}';
            """)
            columns = cur.fetchall()
            if not columns:
                print("❌ Not Found")
                continue
                
            for col in columns:
                print(f"  {col[0]}: {col[1]} ({col[2]})")

            # Check Foreign Keys
            print("  Foreign Keys:")
            cur.execute(f"""
                SELECT
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.key_column_usage AS kcu
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = kcu.constraint_name
                WHERE kcu.table_name = '{t}' AND kcu.constraint_name LIKE '%fk';
            """)
            fks = cur.fetchall()
            if not fks:
                print("    None")
            for fk in fks:
                print(f"    {fk[0]} -> {fk[1]}.{fk[2]}")

        conn.close()
    except Exception as e:
        print(f"❌ Inspection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    inspect_full_schema()
