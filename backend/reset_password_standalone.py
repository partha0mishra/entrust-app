"""
Standalone script to reset admin password
Install dependencies first: pip install passlib bcrypt psycopg2-binary
Usage: python reset_password_standalone.py
"""

import sys

try:
    from passlib.context import CryptContext
    import psycopg2
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("\n📦 Please install required packages:")
    print("   pip install passlib bcrypt psycopg2-binary")
    sys.exit(1)

# Database connection details
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "entrust_db"
DB_USER = "entrust_user"
DB_PASSWORD = "entrust_pass"

# Password to set
NEW_PASSWORD = "Welcome123!"

def reset_password():
    """Reset admin password in database"""

    # Initialize password hasher
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Hash the new password
    password_hash = pwd_context.hash(NEW_PASSWORD)

    print(f"🔐 Resetting admin password to: {NEW_PASSWORD}")
    print(f"📝 Password hash: {password_hash[:50]}...")

    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        # Check if admin user exists
        cursor.execute("SELECT user_id, username FROM users WHERE user_id = 'admin'")
        result = cursor.fetchone()

        if not result:
            print("❌ Admin user not found in database!")
            print("   Please run init_db.py first to create the admin user.")
            return

        print(f"✅ Found admin user: {result[1]}")

        # Update password
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE user_id = 'admin'",
            (password_hash,)
        )
        conn.commit()

        print("\n✅ Admin password has been reset successfully!")
        print("\n🔑 Login credentials:")
        print(f"   User ID: admin")
        print(f"   Password: {NEW_PASSWORD}")
        print("\n🚀 You can now login at http://localhost:3000")

    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        print("\n💡 Check that:")
        print("   - PostgreSQL is running")
        print("   - Database credentials are correct")
        print("   - Database 'entrust_db' exists")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    reset_password()
