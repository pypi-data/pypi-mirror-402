import psycopg2
import sys

# URL from .env (root)
DB_URL = "postgresql://ailoos_coordinator:TJfr6Lj5keD3SN7Dbbz20WbF_aNMXCel@localhost:5432/ailoos_coordinator"

# Extracted from 0025 + Updates
SQL_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS "account" (
	"id" text PRIMARY KEY NOT NULL,
	"account_id" text NOT NULL,
	"provider_id" text NOT NULL,
	"user_id" text NOT NULL REFERENCES "user"("id") ON DELETE CASCADE,
	"access_token" text,
	"refresh_token" text,
	"id_token" text,
	"access_token_expires_at" timestamp,
	"refresh_token_expires_at" timestamp,
	"scope" text,
	"password" text,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS "session" (
	"id" text PRIMARY KEY NOT NULL,
	"expires_at" timestamp NOT NULL,
	"token" text NOT NULL UNIQUE,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp NOT NULL,
	"ip_address" text,
	"user_agent" text,
	"user_id" text NOT NULL REFERENCES "user"("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "verification" (
	"id" text PRIMARY KEY NOT NULL,
	"identifier" text NOT NULL,
	"value" text NOT NULL,
	"expires_at" timestamp NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
"""

def create_tables():
    print(f"Connecting to {DB_URL}...")
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Creating missing tables (account, session, verification)...")
        cur.execute(SQL_CREATE_TABLES)
        print("✅ Tables created successfully.")
        
        conn.close()
    except Exception as e:
        print(f"❌ Creation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_tables()
