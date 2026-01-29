import psycopg2
import sys

# URL from .env (root)
DB_URL = "postgresql://ailoos_coordinator:TJfr6Lj5keD3SN7Dbbz20WbF_aNMXCel@localhost:5432/ailoos_coordinator"

FIX_SCHEMA_SQL = """
-- 1. Fix ID type (UUID -> TEXT)
ALTER TABLE "user" ALTER COLUMN "id" SET DATA TYPE text;
ALTER TABLE "user" ALTER COLUMN "id" DROP DEFAULT;

-- 2. Add missing columns
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "name" text;
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "image" text;
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "email_verified" boolean DEFAULT false NOT NULL;

-- 3. Fix timestamps
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "created_at" timestamp DEFAULT now() NOT NULL;
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "updated_at" timestamp DEFAULT now() NOT NULL;

-- 4. Fill 'name' for existing rows if null (to satisfy NOT NULL later)
UPDATE "user" SET "name" = 'User' WHERE "name" IS NULL;

-- 5. Enforce NOT NULL on 'name'
ALTER TABLE "user" ALTER COLUMN "name" SET NOT NULL;

-- 6. Ensure email is text
ALTER TABLE "user" ALTER COLUMN "email" SET DATA TYPE text;
"""

def fix_schema():
    print(f"Connecting to {DB_URL}...")
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check what exists
        cur.execute("SELECT to_regclass('public.\"User\"');")
        user_cap = cur.fetchone()[0]
        
        cur.execute("SELECT to_regclass('public.\"user\"');")
        user_lower = cur.fetchone()[0]
        
        print(f"Table state: 'User'={user_cap}, 'user'={user_lower}")
        
        target_table = None
        
        if user_cap:
            print("Found 'User', renaming to 'user'...")
            cur.execute('ALTER TABLE "User" RENAME TO "user";')
            target_table = "user"
        elif user_lower:
            target_table = "user"
        else:
            print("❌ No user table found! Creating from scratch...")
            cur.execute("""
            CREATE TABLE "user" (
                "id" text PRIMARY KEY,  -- text to match schema.ts
                "email" text NOT NULL UNIQUE,
                "password" text,
                "name" text NOT NULL,
                "image" text,
                "email_verified" boolean DEFAULT false NOT NULL,
                "created_at" timestamp DEFAULT now() NOT NULL,
                "updated_at" timestamp DEFAULT now() NOT NULL
            );
            """)
            print("✅ Created fresh 'user' table.")
            return

        print(f"Targeting table: '{target_table}'")
        
        # Now apply the fixes to 'user'
        # 1. Fix ID type
        print("Fixing ID type...")
        try:
            cur.execute('ALTER TABLE "user" ALTER COLUMN "id" SET DATA TYPE text;')
            cur.execute('ALTER TABLE "user" ALTER COLUMN "id" DROP DEFAULT;')
        except Exception as e:
            print(f"⚠️ ID Fix warn: {e}")

        # 2. Add columns individually to avoid errors if they exist
        cols = [
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "name" text;',
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "image" text;',
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "email_verified" boolean DEFAULT false NOT NULL;',
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "created_at" timestamp DEFAULT now() NOT NULL;',
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "updated_at" timestamp DEFAULT now() NOT NULL;'
        ]
        
        for sql in cols:
            try:
                cur.execute(sql)
            except Exception as e:
                print(f"⚠️ Column add error: {e}")

        # 3. Data cleanup
        cur.execute("UPDATE \"user\" SET \"name\" = 'User' WHERE \"name\" IS NULL;")
        try:
            cur.execute('ALTER TABLE "user" ALTER COLUMN "name" SET NOT NULL;')
        except Exception as e:
            print(f"⚠️ Name NOT NULL error: {e}")
            
        try:
            cur.execute('ALTER TABLE "user" ALTER COLUMN "email" SET DATA TYPE text;')
        except Exception as e:
             print(f"⚠️ Email type error: {e}")

        print("✅ Schema fix sequence complete.")

        conn.close()
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_schema()
