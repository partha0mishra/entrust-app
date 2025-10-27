"""
Database migration script to add user_survey_submissions table
Run this script to enable per-user survey submission tracking
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from app.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add user_survey_submissions table for per-user submission tracking"""
    engine = create_engine(DATABASE_URL)

    migrations = [
        # Create user_survey_submissions table
        """
        CREATE TABLE IF NOT EXISTS user_survey_submissions (
            id SERIAL PRIMARY KEY,
            survey_id INTEGER NOT NULL REFERENCES surveys(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_survey_user UNIQUE (survey_id, user_id)
        );
        """,

        # Create indexes for performance
        """
        CREATE INDEX IF NOT EXISTS idx_user_survey_submissions_survey_id
        ON user_survey_submissions(survey_id);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_user_survey_submissions_user_id
        ON user_survey_submissions(user_id);
        """,
    ]

    try:
        with engine.connect() as conn:
            for i, migration_sql in enumerate(migrations, 1):
                logger.info(f"Running migration {i}/{len(migrations)}...")
                conn.execute(text(migration_sql))
                conn.commit()
                logger.info(f"Migration {i} completed successfully")

        logger.info("\n✅ All migrations completed successfully!")
        logger.info("\nThe user_survey_submissions table has been created.")
        logger.info("Users can now submit surveys independently without affecting other users.")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting user survey submission migration...\n")
    migrate()
