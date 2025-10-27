"""
Add process and lifecycle_stage columns to questions table
Run: docker exec -it entrust_backend python migrate_questions.py
"""

from sqlalchemy import text
from app.database import SessionLocal

def migrate():
    db = SessionLocal()
    
    try:
        # Check if columns already exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='questions' AND column_name IN ('process', 'lifecycle_stage')
        """))
        
        existing_columns = [row[0] for row in result.fetchall()]
        
        if 'process' not in existing_columns:
            print("Adding 'process' column to questions table...")
            db.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN process VARCHAR(100)
            """))
            db.commit()
            print("✓ Column 'process' added successfully!")
        else:
            print("✓ Column 'process' already exists. Skipping.")
        
        if 'lifecycle_stage' not in existing_columns:
            print("Adding 'lifecycle_stage' column to questions table...")
            db.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN lifecycle_stage VARCHAR(100)
            """))
            db.commit()
            print("✓ Column 'lifecycle_stage' added successfully!")
        else:
            print("✓ Column 'lifecycle_stage' already exists. Skipping.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("EnTrust - Add process and lifecycle_stage to questions")
    print("=" * 60)
    migrate()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)

