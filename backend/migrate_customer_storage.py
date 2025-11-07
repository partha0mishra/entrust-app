"""
Database migration script to add storage configuration to customers table
Run this script to update the customers table with storage preference fields
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
    """Add storage configuration columns to customers table"""
    engine = create_engine(DATABASE_URL)

    migrations = [
        # Create storage type enum
        """
        DROP TYPE IF EXISTS storagetype CASCADE;
        """,
        """
        CREATE TYPE storagetype AS ENUM ('LOCAL', 'S3', 'AZURE_BLOB');
        """,

        # Add storage_type column with default 'LOCAL'
        """
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS storage_type storagetype DEFAULT 'LOCAL'::storagetype NOT NULL;
        """,

        # Add fallback enabled flag
        """
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS storage_fallback_enabled BOOLEAN DEFAULT TRUE;
        """,

        # Add S3 configuration fields
        """
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS s3_bucket_name VARCHAR(255);
        """,
        """
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS s3_region VARCHAR(50);
        """,
        """
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS s3_access_key_id VARCHAR(500);
        """,
        """
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS s3_secret_access_key VARCHAR(500);
        """,
        """
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS s3_prefix VARCHAR(255);
        """,

        # Add Azure Blob configuration fields
        """
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS azure_storage_account VARCHAR(255);
        """,
        """
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS azure_container_name VARCHAR(255);
        """,
        """
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS azure_connection_string VARCHAR(1000);
        """,
        """
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS azure_prefix VARCHAR(255);
        """,
    ]

    try:
        with engine.connect() as conn:
            for i, migration_sql in enumerate(migrations, 1):
                logger.info(f"Running migration {i}/{len(migrations)}...")
                conn.execute(text(migration_sql))
                conn.commit()
                logger.info(f"Migration {i} completed successfully")

        logger.info("All migrations completed successfully!")
        logger.info("\nThe customers table now supports:")
        logger.info("  - Local storage (default)")
        logger.info("  - AWS S3 storage")
        logger.info("  - Azure Blob storage")
        logger.info("  - Fallback to local storage when cloud storage fails")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting customer storage configuration migration...")
    migrate()
