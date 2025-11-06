#!/usr/bin/env python3
"""
Migration script to add reasoning_effort and thinking_mode fields to LLMConfig
"""
import sys
from sqlalchemy import text, inspect
from app.database import SessionLocal, engine

def migrate():
    """Add reasoning_effort and thinking_mode columns to llm_configs table"""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("  MIGRATION: Add Reasoning Effort & Thinking Mode Fields")
        print("=" * 70)
        
        # Check if columns already exist
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('llm_configs')]
        
        # Add azure_reasoning_effort column
        if 'azure_reasoning_effort' not in existing_columns:
            print("\n[1/2] Adding azure_reasoning_effort column...")
            db.execute(text("ALTER TABLE llm_configs ADD COLUMN azure_reasoning_effort VARCHAR(20)"))
            db.commit()
            print("✓ Column 'azure_reasoning_effort' added successfully!")
        else:
            print("⚠ Column 'azure_reasoning_effort' already exists, skipping.")
        
        # Add aws_thinking_mode column
        if 'aws_thinking_mode' not in existing_columns:
            print("\n[2/2] Adding aws_thinking_mode column...")
            db.execute(text("ALTER TABLE llm_configs ADD COLUMN aws_thinking_mode VARCHAR(20)"))
            db.commit()
            print("✓ Column 'aws_thinking_mode' added successfully!")
        else:
            print("⚠ Column 'aws_thinking_mode' already exists, skipping.")
        
        print("\n" + "=" * 70)
        print("✓ Migration completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()

