"""
Consolidated Database Deployment Script
=======================================
This script handles complete database setup from initialization to all migrations.
It consolidates all database deployment operations into a single, easy-to-use tool.

Usage:
    # Full deployment (init + all migrations)
    python deploy_db.py

    # Initialize only (tables + admin + questions)
    python deploy_db.py --init-only

    # Migrate only (run all migrations)
    python deploy_db.py --migrate-only

    # Run specific migration
    python deploy_db.py --migrate password
    python deploy_db.py --migrate llm_model
    python deploy_db.py --migrate llm_providers
    python deploy_db.py --migrate questions_fields
    python deploy_db.py --migrate user_submissions

Available Migrations:
    - password           : Add password column to users table
    - llm_model          : Add model_name column to llm_configs table
    - llm_providers      : Add multi-provider LLM support (LOCAL, BEDROCK, AZURE)
    - questions_fields   : Add process and lifecycle_stage columns to questions table
    - user_submissions   : Create user_survey_submissions table
    - customer_storage   : Add storage configuration to customers table (S3, Azure Blob)
"""

import sys
import json
import os
import argparse
import logging
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal, engine
from app import models, auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DatabaseDeployment:
    """Handles complete database deployment from initialization to migrations"""

    def __init__(self):
        self.db = SessionLocal()
        self.inspector = inspect(engine)
        self.errors = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Fatal error occurred: {exc_val}")
            self.db.rollback()
        self.db.close()

    # ==================== Utility Methods ====================

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            return table_name in self.inspector.get_table_names()
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        if not self.table_exists(table_name):
            return False
        try:
            columns = [col['name'] for col in self.inspector.get_columns(table_name)]
            return column_name in columns
        except Exception as e:
            logger.error(f"Error checking column existence: {e}")
            return False

    def execute_sql(self, sql: str, params: dict = None) -> bool:
        """Execute SQL with error handling"""
        try:
            if params:
                self.db.execute(text(sql), params)
            else:
                self.db.execute(text(sql))
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"SQL execution failed: {e}")
            self.db.rollback()
            return False

    # ==================== Initialization ====================

    def initialize_database(self):
        """Complete database initialization: tables, admin user, and questions"""
        logger.info("=" * 70)
        logger.info("  DATABASE INITIALIZATION")
        logger.info("=" * 70)

        # Step 1: Create all tables
        logger.info("\n[1/3] Creating database tables...")
        try:
            models.Base.metadata.create_all(bind=engine)
            logger.info("✓ Tables created successfully!")
        except Exception as e:
            logger.error(f"✗ Failed to create tables: {e}")
            raise

        # Step 2: Create or update default admin user
        logger.info("\n[2/3] Creating/updating default admin user...")
        admin_user = self.db.query(models.User).filter(
            models.User.user_id == "admin"
        ).first()

        admin_password = "admin123"
        
        if not admin_user:
            try:
                admin_user = models.User(
                    user_id="admin",
                    username="System Administrator",
                    password_hash=auth.get_password_hash(admin_password),
                    password=auth.encrypt_password(admin_password),
                    user_type=models.UserType.SYSTEM_ADMIN,
                    customer_id=None
                )
                self.db.add(admin_user)
                self.db.commit()
                logger.info("✓ Default admin user created!")
                logger.info(f"   User ID: admin")
                logger.info(f"   Password: {admin_password}")
            except Exception as e:
                logger.error(f"✗ Failed to create admin user: {e}")
                self.db.rollback()
                raise
        else:
            # Update password to ensure it's set correctly
            try:
                admin_user.password_hash = auth.get_password_hash(admin_password)
                admin_user.password = auth.encrypt_password(admin_password)
                self.db.commit()
                logger.info("✓ Admin user exists - password updated to default!")
                logger.info(f"   User ID: admin")
                logger.info(f"   Password: {admin_password}")
            except Exception as e:
                logger.error(f"✗ Failed to update admin user password: {e}")
                self.db.rollback()
                raise

        # Step 3: Load questions
        logger.info("\n[3/3] Loading questions from questions.json...")
        question_count = self.db.query(models.Question).count()
        if question_count == 0:
            try:
                # Try multiple possible locations for questions.json
                questions_file = None
                possible_paths = [
                    'questions.json',  # Current directory
                    '/app/questions.json',  # App root in Docker
                    os.path.join(os.path.dirname(__file__), '..', 'questions.json'),  # Parent directory
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions.json')  # Root
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        questions_file = path
                        break
                
                if not questions_file:
                    raise FileNotFoundError("questions.json not found in any expected location")
                
                with open(questions_file, 'r', encoding='utf-8') as f:
                    questions_data = json.load(f)

                logger.info(f"Found {len(questions_data)} questions in file.")

                for q in questions_data:
                    question = models.Question(
                        question_id=q['id'],
                        text=q['text'],
                        category=q.get('category'),
                        dimension=q['dimension'],
                        question_type=q.get('question_type'),
                        guidance=q.get('guidance'),
                        process=q.get('process'),
                        lifecycle_stage=q.get('lifecycle_stage')
                    )
                    self.db.add(question)

                self.db.commit()
                logger.info(f"✓ Loaded {len(questions_data)} questions!")

                # Show dimension summary
                dimensions = self.db.query(models.Question.dimension).distinct().all()
                logger.info(f"\n📊 Questions across {len(dimensions)} dimensions:")
                for dim in dimensions:
                    count = self.db.query(models.Question).filter(
                        models.Question.dimension == dim[0]
                    ).count()
                    logger.info(f"   • {dim[0]}: {count} questions")

            except FileNotFoundError:
                logger.error("✗ ERROR: questions.json file not found!")
                logger.error("   Place questions.json in the backend directory.")
                raise
            except json.JSONDecodeError as e:
                logger.error(f"✗ ERROR: Invalid JSON in questions.json: {e}")
                raise
            except Exception as e:
                logger.error(f"✗ Failed to load questions: {e}")
                self.db.rollback()
                raise
        else:
            logger.info(f"⚠ Questions already loaded ({question_count} questions).")

        logger.info("\n" + "=" * 70)
        logger.info("  INITIALIZATION COMPLETE!")
        logger.info("=" * 70)

    # ==================== Migrations ====================

    def migrate_password_column(self):
        """Add password column to users table for plain-text password storage"""
        logger.info("\n[Migration: password] Adding password column to users table...")

        if self.column_exists('users', 'password'):
            logger.info("⚠ Column 'password' already exists in users table.")
            return True

        try:
            # Add password column
            if not self.execute_sql("ALTER TABLE users ADD COLUMN password TEXT"):
                return False

            # Set default passwords for existing users
            admin_password = auth.encrypt_password("admin123")
            default_password = auth.encrypt_password("Welcome123!")
            
            self.db.execute(text("""
                UPDATE users
                SET password = CASE
                    WHEN user_id = 'admin' THEN :admin_pwd
                    ELSE :default_pwd
                END
                WHERE password IS NULL
            """), {"admin_pwd": admin_password, "default_pwd": default_password})
            self.db.commit()

            logger.info("✓ Password column added successfully!")
            logger.info("   Default passwords set for existing users")
            return True
        except Exception as e:
            logger.error(f"✗ Migration failed: {e}")
            self.db.rollback()
            return False

    def migrate_llm_model_name(self):
        """Add model_name column to llm_configs table"""
        logger.info("\n[Migration: llm_model] Adding model_name to llm_configs...")

        if self.column_exists('llm_configs', 'model_name'):
            logger.info("⚠ Column 'model_name' already exists in llm_configs table.")
            return True

        try:
            if self.execute_sql(
                "ALTER TABLE llm_configs ADD COLUMN model_name VARCHAR(100) DEFAULT 'default'"
            ):
                logger.info("✓ model_name column added successfully!")
                return True
            return False
        except Exception as e:
            logger.error(f"✗ Migration failed: {e}")
            return False

    def migrate_llm_providers(self):
        """Add multi-provider LLM support (LOCAL, BEDROCK, AZURE)"""
        logger.info("\n[Migration: llm_providers] Adding multi-provider support...")

        if self.column_exists('llm_configs', 'provider_type'):
            logger.info("⚠ Multi-provider columns already exist in llm_configs table.")
            return True

        try:
            # Create ENUM type if it doesn't exist
            self.execute_sql("""
                DO $$ BEGIN
                    CREATE TYPE llmprovidertype AS ENUM ('LOCAL', 'BEDROCK', 'AZURE');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)

            # Add provider_type column
            if not self.execute_sql(
                "ALTER TABLE llm_configs ADD COLUMN provider_type llmprovidertype DEFAULT 'LOCAL'"
            ):
                return False

            # Add AWS Bedrock fields
            migrations = [
                ("aws_region", "ALTER TABLE llm_configs ADD COLUMN aws_region VARCHAR(50)"),
                ("aws_access_key_id", "ALTER TABLE llm_configs ADD COLUMN aws_access_key_id TEXT"),
                ("aws_secret_access_key", "ALTER TABLE llm_configs ADD COLUMN aws_secret_access_key TEXT"),
                ("aws_model_id", "ALTER TABLE llm_configs ADD COLUMN aws_model_id VARCHAR(200)"),
                # Azure OpenAI fields
                ("azure_endpoint", "ALTER TABLE llm_configs ADD COLUMN azure_endpoint TEXT"),
                ("azure_api_key", "ALTER TABLE llm_configs ADD COLUMN azure_api_key TEXT"),
                ("azure_deployment_name", "ALTER TABLE llm_configs ADD COLUMN azure_deployment_name VARCHAR(200)"),
                ("azure_api_version", "ALTER TABLE llm_configs ADD COLUMN azure_api_version VARCHAR(50) DEFAULT '2024-02-15-preview'"),
                # Make api_url nullable
                ("api_url_nullable", "ALTER TABLE llm_configs ALTER COLUMN api_url DROP NOT NULL"),
            ]

            for col_name, sql in migrations:
                if col_name != "api_url_nullable" and self.column_exists('llm_configs', col_name):
                    logger.info(f"  ⚠ Column '{col_name}' already exists, skipping.")
                    continue
                
                if not self.execute_sql(sql):
                    logger.error(f"  ✗ Failed to add column '{col_name}'")
                    return False

            logger.info("✓ Multi-provider support added successfully!")
            logger.info("   Supported providers: LOCAL, AWS Bedrock, Azure OpenAI")
            return True
        except Exception as e:
            logger.error(f"✗ Migration failed: {e}")
            return False

    def migrate_questions_fields(self):
        """Add process and lifecycle_stage columns to questions table"""
        logger.info("\n[Migration: questions_fields] Adding process and lifecycle_stage...")

        if self.column_exists('questions', 'process') and self.column_exists('questions', 'lifecycle_stage'):
            logger.info("⚠ Process and lifecycle_stage columns already exist.")
            return True

        try:
            if not self.column_exists('questions', 'process'):
                if not self.execute_sql("ALTER TABLE questions ADD COLUMN process VARCHAR(100)"):
                    return False
                logger.info("  ✓ Added 'process' column")

            if not self.column_exists('questions', 'lifecycle_stage'):
                if not self.execute_sql("ALTER TABLE questions ADD COLUMN lifecycle_stage VARCHAR(100)"):
                    return False
                logger.info("  ✓ Added 'lifecycle_stage' column")

            logger.info("✓ Questions fields added successfully!")
            return True
        except Exception as e:
            logger.error(f"✗ Migration failed: {e}")
            return False

    def migrate_user_submissions(self):
        """Create user_survey_submissions table"""
        logger.info("\n[Migration: user_submissions] Creating user_survey_submissions table...")

        if self.table_exists('user_survey_submissions'):
            logger.info("⚠ Table 'user_survey_submissions' already exists.")
            return True

        try:
            # Create table
            if not self.execute_sql("""
                CREATE TABLE user_survey_submissions (
                    id SERIAL PRIMARY KEY,
                    survey_id INTEGER NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_survey_user UNIQUE (survey_id, user_id)
                )
            """):
                return False

            # Create indexes
            indexes = [
                "CREATE INDEX idx_user_submissions_survey ON user_survey_submissions(survey_id)",
                "CREATE INDEX idx_user_submissions_user ON user_survey_submissions(user_id)",
            ]

            for index_sql in indexes:
                if not self.execute_sql(index_sql):
                    logger.warning(f"  ⚠ Index creation may have failed: {index_sql}")

            logger.info("✓ user_survey_submissions table created successfully!")
            return True
        except Exception as e:
            logger.error(f"✗ Migration failed: {e}")
            return False

    def migrate_customer_storage(self):
        """Add storage configuration to customers table"""
        logger.info("\n[Migration: customer_storage] Adding storage configuration...")

        if self.column_exists('customers', 'storage_type'):
            logger.info("⚠ Storage configuration columns already exist.")
            return True

        try:
            # Create ENUM type for storage
            self.execute_sql("""
                DO $$ BEGIN
                    CREATE TYPE storagetype AS ENUM ('LOCAL', 'S3', 'AZURE_BLOB');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)

            # Add storage columns
            migrations = [
                ("storage_type", "ALTER TABLE customers ADD COLUMN storage_type storagetype DEFAULT 'LOCAL'"),
                ("storage_fallback_enabled", "ALTER TABLE customers ADD COLUMN storage_fallback_enabled BOOLEAN DEFAULT TRUE"),
                # S3 fields
                ("s3_bucket_name", "ALTER TABLE customers ADD COLUMN s3_bucket_name VARCHAR(255)"),
                ("s3_region", "ALTER TABLE customers ADD COLUMN s3_region VARCHAR(50)"),
                ("s3_access_key_id", "ALTER TABLE customers ADD COLUMN s3_access_key_id TEXT"),
                ("s3_secret_access_key", "ALTER TABLE customers ADD COLUMN s3_secret_access_key TEXT"),
                ("s3_prefix", "ALTER TABLE customers ADD COLUMN s3_prefix VARCHAR(255)"),
                # Azure Blob fields
                ("azure_storage_account", "ALTER TABLE customers ADD COLUMN azure_storage_account VARCHAR(255)"),
                ("azure_container_name", "ALTER TABLE customers ADD COLUMN azure_container_name VARCHAR(255)"),
                ("azure_connection_string", "ALTER TABLE customers ADD COLUMN azure_connection_string TEXT"),
                ("azure_prefix", "ALTER TABLE customers ADD COLUMN azure_prefix VARCHAR(255)"),
            ]

            for col_name, sql in migrations:
                if self.column_exists('customers', col_name):
                    logger.info(f"  ⚠ Column '{col_name}' already exists, skipping.")
                    continue

                if not self.execute_sql(sql):
                    logger.error(f"  ✗ Failed to add column '{col_name}'")
                    return False

            logger.info("✓ Storage configuration added successfully!")
            logger.info("   Supported storage types: LOCAL, S3, AZURE_BLOB")
            logger.info("   Fallback to local storage enabled by default")
            return True
        except Exception as e:
            logger.error(f"✗ Migration failed: {e}")
            return False

    def run_all_migrations(self):
        """Run all migrations in order"""
        logger.info("\n" + "=" * 70)
        logger.info("  RUNNING ALL MIGRATIONS")
        logger.info("=" * 70)

        migrations = [
            ("password", self.migrate_password_column),
            ("llm_model", self.migrate_llm_model_name),
            ("llm_providers", self.migrate_llm_providers),
            ("questions_fields", self.migrate_questions_fields),
            ("user_submissions", self.migrate_user_submissions),
            ("customer_storage", self.migrate_customer_storage),
        ]

        success_count = 0
        for name, migration_func in migrations:
            try:
                if migration_func():
                    success_count += 1
                else:
                    logger.error(f"✗ Migration '{name}' failed!")
                    self.errors.append(name)
            except Exception as e:
                logger.error(f"✗ Migration '{name}' failed with exception: {e}")
                self.errors.append(name)

        logger.info("\n" + "=" * 70)
        if len(self.errors) == 0:
            logger.info("  ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
        else:
            logger.info(f"  MIGRATIONS COMPLETED WITH {len(self.errors)} ERROR(S)")
        logger.info("=" * 70)

        return len(self.errors) == 0

    def print_summary(self):
        """Print database deployment summary"""
        logger.info("\n" + "=" * 70)
        logger.info("  DATABASE DEPLOYMENT SUMMARY")
        logger.info("=" * 70)
        logger.info("\n📝 Database Statistics:")
        logger.info(f"   • Questions: {self.db.query(models.Question).count()}")
        logger.info(f"   • Customers: {self.db.query(models.Customer).count()}")
        logger.info(f"   • Users: {self.db.query(models.User).count()}")
        logger.info(f"   • Surveys: {self.db.query(models.Survey).count()}")
        logger.info(f"   • LLM Configs: {self.db.query(models.LLMConfig).count()}")

        logger.info("\n🚀 Application URLs:")
        logger.info("   Frontend: http://localhost:3000")
        logger.info("   Backend API: http://localhost:8000")
        logger.info("   API Docs: http://localhost:8000/docs")

        logger.info("\n🔑 Default Login Credentials:")
        logger.info("   User ID: admin")
        logger.info("   Password: admin123")
        logger.info("   ⚠ Change this password in production!")

        if self.errors:
            logger.info("\n⚠ Errors occurred during migration:")
            for error in self.errors:
                logger.info(f"   • {error}")
        
        logger.info("\n" + "=" * 70 + "\n")


def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Consolidated Database Deployment Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--init-only', action='store_true',
                        help='Initialize database only (tables, admin, questions)')
    parser.add_argument('--migrate-only', action='store_true',
                        help='Run all migrations only')
    parser.add_argument('--migrate', type=str,
                        choices=['password', 'llm_model', 'llm_providers', 'questions_fields', 'user_submissions', 'customer_storage'],
                        help='Run a specific migration')

    args = parser.parse_args()

    try:
        with DatabaseDeployment() as deployment:
            if args.init_only:
                # Initialize only
                deployment.initialize_database()
                deployment.print_summary()
            elif args.migrate_only:
                # Migrate only
                deployment.run_all_migrations()
                deployment.print_summary()
            elif args.migrate:
                # Run specific migration
                migration_map = {
                    'password': deployment.migrate_password_column,
                    'llm_model': deployment.migrate_llm_model_name,
                    'llm_providers': deployment.migrate_llm_providers,
                    'questions_fields': deployment.migrate_questions_fields,
                    'user_submissions': deployment.migrate_user_submissions,
                    'customer_storage': deployment.migrate_customer_storage,
                }
                migration_map[args.migrate]()
                deployment.print_summary()
            else:
                # Default: Full deployment (init + migrations)
                logger.info("=" * 70)
                logger.info("  ENTRUST DATABASE DEPLOYMENT")
                logger.info("=" * 70)
                logger.info("Starting full database deployment...")
                logger.info("This will: Initialize database + Run all migrations\n")
                
                deployment.initialize_database()
                deployment.run_all_migrations()
                deployment.print_summary()

    except KeyboardInterrupt:
        logger.info("\n\n⚠ Deployment interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n✗ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

