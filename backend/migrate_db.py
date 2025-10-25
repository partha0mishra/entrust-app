"""
Migration script to add password column for plain text password storage
Run this ONCE: docker exec -it entrust_backend python migrate_db.py
"""

from sqlalchemy import text
from app.database import SessionLocal

def migrate():
    db = SessionLocal()
    
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='password'
        """))
        
        if result.fetchone():
            print("✓ Column 'password' already exists. Skipping migration.")
            return
        
        print("Adding 'password' column to users table...")
        
        # Add the new column
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN password TEXT
        """))
        db.commit()
        
        print("✓ Column added successfully!")
        
        # Set default passwords for existing users
        print("Setting default passwords for existing users...")
        
        # Admin keeps admin123
        db.execute(text("""
            UPDATE users 
            SET password = 'admin123' 
            WHERE user_id = 'admin'
        """))
        
        # Other users get a default password
        db.execute(text("""
            UPDATE users 
            SET password = 'Welcome123!' 
            WHERE user_id != 'admin' AND password IS NULL
        """))
        
        db.commit()
        
        print("✓ Passwords set:")
        print("  - Admin: admin123")
        print("  - Others: Welcome123!")
        print("\n⚠️  Users should change their passwords after first login")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("EnTrust Database Migration - Add password column")
    print("=" * 60)
    migrate()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)