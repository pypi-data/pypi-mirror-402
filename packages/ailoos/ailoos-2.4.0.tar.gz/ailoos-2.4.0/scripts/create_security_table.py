import psycopg2
import sys

# URL from .env (root)
DB_URL = "postgresql://ailoos_coordinator:TJfr6Lj5keD3SN7Dbbz20WbF_aNMXCel@localhost:5432/ailoos_coordinator"

SQL_CREATE_SECURITY = """
CREATE TABLE IF NOT EXISTS "security_settings" (
	"user_id" text PRIMARY KEY NOT NULL REFERENCES "user"("id") ON DELETE CASCADE,
	"two_factor_enabled" boolean DEFAULT false NOT NULL,
	"session_timeout_minutes" integer DEFAULT 60 NOT NULL,
	"login_alerts_enabled" boolean DEFAULT false NOT NULL,
	"password_last_changed" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
"""

def create_security_table():
    print(f"Connecting to {DB_URL}...")
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Creating security_settings table...")
        cur.execute(SQL_CREATE_SECURITY)
        print("✅ security_settings table created.")
        
        conn.close()
    except Exception as e:
        print(f"❌ Creation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_security_table()
