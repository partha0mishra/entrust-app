"""
Add model_name column to llm_configs table
Run: docker exec -it entrust_backend python migrate_llm.py
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
            WHERE table_name='llm_configs' AND column_name='model_name'
        """))
        
        if result.fetchone():
            print("✓ Column 'model_name' already exists. Skipping migration.")
            return
        
        print("Adding 'model_name' column to llm_configs table...")
        
        # Add the new column
        db.execute(text("""
            ALTER TABLE llm_configs 
            ADD COLUMN model_name VARCHAR(100) DEFAULT 'default'
        """))
        db.commit()
        
        print("✓ Column 'model_name' added successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("EnTrust - Add model_name to llm_configs")
    print("=" * 60)
    migrate()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)