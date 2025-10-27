"""
Database migration script to add multi-provider support to LLM configurations
Run this script to update the llm_configs table with new provider-specific fields
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
    """Add provider-specific columns to llm_configs table"""
    engine = create_engine(DATABASE_URL)

    migrations = [
        # Drop the old provider_type column if it exists
        """
        ALTER TABLE llm_configs DROP COLUMN IF EXISTS provider_type;
        """,

        # Drop the enum type if it exists
        """
        DROP TYPE IF EXISTS llmprovidertype CASCADE;
        """,

        # Create the enum type with lowercase values
        """
        CREATE TYPE llmprovidertype AS ENUM ('local', 'bedrock', 'azure');
        """,

        # Add provider_type column with default 'local'
        """
        ALTER TABLE llm_configs
        ADD COLUMN provider_type llmprovidertype DEFAULT 'local'::llmprovidertype NOT NULL;
        """,

        # Make api_url nullable (required only for local provider)
        """
        ALTER TABLE llm_configs
        ALTER COLUMN api_url DROP NOT NULL;
        """,

        # Add AWS Bedrock fields
        """
        ALTER TABLE llm_configs
        ADD COLUMN IF NOT EXISTS aws_region VARCHAR(50);
        """,
        """
        ALTER TABLE llm_configs
        ADD COLUMN IF NOT EXISTS aws_access_key_id VARCHAR(500);
        """,
        """
        ALTER TABLE llm_configs
        ADD COLUMN IF NOT EXISTS aws_secret_access_key VARCHAR(500);
        """,
        """
        ALTER TABLE llm_configs
        ADD COLUMN IF NOT EXISTS aws_model_id VARCHAR(200);
        """,

        # Add Azure OpenAI fields
        """
        ALTER TABLE llm_configs
        ADD COLUMN IF NOT EXISTS azure_endpoint VARCHAR(500);
        """,
        """
        ALTER TABLE llm_configs
        ADD COLUMN IF NOT EXISTS azure_api_key VARCHAR(500);
        """,
        """
        ALTER TABLE llm_configs
        ADD COLUMN IF NOT EXISTS azure_deployment_name VARCHAR(200);
        """,
        """
        ALTER TABLE llm_configs
        ADD COLUMN IF NOT EXISTS azure_api_version VARCHAR(50) DEFAULT '2024-02-15-preview';
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
        logger.info("\nThe llm_configs table now supports:")
        logger.info("  - Local LLMs (LM Studio, Ollama, etc.)")
        logger.info("  - AWS Bedrock")
        logger.info("  - Azure OpenAI")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting LLM provider migration...")
    migrate()
