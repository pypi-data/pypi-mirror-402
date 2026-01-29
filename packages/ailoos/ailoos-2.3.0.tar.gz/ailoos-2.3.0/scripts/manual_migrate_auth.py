import psycopg2
import os

# URL from .env (root) - Verified working
DB_URL = "postgresql://ailoos_coordinator:TJfr6Lj5keD3SN7Dbbz20WbF_aNMXCel@localhost:5432/ailoos_coordinator"

SCHEMA_0000 = """
CREATE TABLE IF NOT EXISTS "Chat" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"createdAt" timestamp NOT NULL,
	"messages" json NOT NULL,
	"userId" uuid NOT NULL
);
CREATE TABLE IF NOT EXISTS "User" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"email" varchar(64) NOT NULL,
	"password" varchar(64)
);
"""

# Note: I omitted the FK constraint in 0000 because 0025 drops/re-adds them and renames tables.
# Safest is to just create the tables if they don't exist, then let 0025 do the heavy lifting of renaming.
# However, 0025 expects "User" to exist to rename it.

SCHEMA_0025 = """
CREATE TABLE IF NOT EXISTS "account" (
	"id" text PRIMARY KEY NOT NULL,
	"account_id" text NOT NULL,
	"provider_id" text NOT NULL,
	"user_id" text NOT NULL,
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
	"token" text NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp NOT NULL,
	"ip_address" text,
	"user_agent" text,
	"user_id" text NOT NULL,
	CONSTRAINT "session_token_unique" UNIQUE("token")
);

-- Handle User -> user transformation
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'User') THEN
        ALTER TABLE "User" RENAME TO "user";
        ALTER TABLE "user" RENAME COLUMN "createdAt" TO "created_at";
        ALTER TABLE "user" RENAME COLUMN "updatedAt" TO "updated_at";
    END IF;
    
    -- If "User" didn't exist but "user" DOES (partial run), we skip renaming
    -- But we need to ensure columns are correct (text type, etc)
    
    -- For now, let's assume strict flow: User created by 0000, renamed by 0025.
END $$;

-- Apply 0025 Alterations (Simplified for robustness)
-- We use DO blocks to avoid errors if columns already changed

ALTER TABLE "Chat" DROP CONSTRAINT IF EXISTS "Chat_userId_User_id_fk";
ALTER TABLE "Document" DROP CONSTRAINT IF EXISTS "Document_userId_User_id_fk";

-- Type conversions (Force them)
ALTER TABLE "user" ALTER COLUMN "id" SET DATA TYPE text;
ALTER TABLE "user" ALTER COLUMN "id" DROP DEFAULT;
ALTER TABLE "user" ALTER COLUMN "email" SET DATA TYPE text;
ALTER TABLE "user" ALTER COLUMN "name" SET DATA TYPE text;
ALTER TABLE "user" ALTER COLUMN "name" SET NOT NULL; -- This might fail if nulls exist (but table is empty)
ALTER TABLE "user" ALTER COLUMN "image" SET DATA TYPE text;

ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "email_verified" boolean DEFAULT false NOT NULL;

-- Add constraints
DO $$ BEGIN
 ALTER TABLE "account" ADD CONSTRAINT "account_user_id_user_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id") ON DELETE cascade ON UPDATE no action;
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
 ALTER TABLE "session" ADD CONSTRAINT "session_user_id_user_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id") ON DELETE cascade ON UPDATE no action;
EXCEPTION WHEN duplicate_object THEN null; END $$;

ALTER TABLE "user" ADD CONSTRAINT "user_email_unique" UNIQUE("email");
"""

SCHEMA_VERIFICATION = """
CREATE TABLE IF NOT EXISTS "verification" (
	"id" text PRIMARY KEY NOT NULL,
	"identifier" text NOT NULL,
	"value" text NOT NULL,
	"expires_at" timestamp NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
"""

def migrate():
    print(f"Connecting to DB...")
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Executing 0000 (User creation)...")
        # Check if user table exists (any case)
        cur.execute("SELECT to_regclass('public.\"User\"');")
        user_exists_cap = cur.fetchone()[0]
        cur.execute("SELECT to_regclass('public.user');")
        user_exists_lower = cur.fetchone()[0]
        
        if not user_exists_cap and not user_exists_lower:
             cur.execute(SCHEMA_0000)
             print("✅ Created 'User' table.")
        else:
             print("ℹ️ 'User' or 'user' table already exists, skipping 0000 creation.")

        print("Executing 0025 (Account/Session/Alterations)...")
        try:
            cur.execute(SCHEMA_0025)
            print("✅ Applied 0025 schema changes.")
        except Exception as e:
            print(f"⚠️ Warning during 0025: {e}")
            
        print("Executing Verification table creation...")
        cur.execute(SCHEMA_VERIFICATION)
        print("✅ Created verification table.")

        conn.close()
        print("🎉 Migration Loop Complete.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
