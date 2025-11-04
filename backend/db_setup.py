"""
Consolidated Database Setup and Migration Script
================================================
This script consolidates all database initialization and migration operations
into a single, easy-to-use tool for setting up the database in any environment.

Usage:
    python db_setup.py --all                  # Run all operations (init + migrations)
    python db_setup.py --init                 # Initialize database (tables + admin + questions)
    python db_setup.py --migrate              # Run all migrations
    python db_setup.py --migrate-specific <name>  # Run a specific migration

Available Migrations:
    - password           : Add password column to users table
    - llm_model          : Add model_name column to llm_configs table
    - llm_providers      : Add multi-provider LLM support (LOCAL, BEDROCK, AZURE)
    - questions_fields   : Add process and lifecycle_stage columns to questions table
    - user_submissions   : Create user_survey_submissions table
"""

import sys
import json
import argparse
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models, auth


class DatabaseSetup:
    """Handles all database setup and migration operations"""

    def __init__(self):
        self.db = SessionLocal()
        self.inspector = inspect(engine)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"\n❌ Error occurred: {exc_val}")
            self.db.rollback()
        self.db.close()

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        return table_name in self.inspector.get_table_names()

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        if not self.table_exists(table_name):
            return False
        columns = [col['name'] for col in self.inspector.get_columns(table_name)]
        return column_name in columns

    # ==================== Initialization ====================

    def initialize_database(self):
        """Create tables, default admin user, and load questions"""
        print("\n" + "="*60)
        print("  DATABASE INITIALIZATION")
        print("="*60)

        # Step 1: Create all tables
        print("\n[1/3] Creating database tables...")
        models.Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")

        # Step 2: Create default admin user
        print("\n[2/3] Creating default admin user...")
        admin_user = self.db.query(models.User).filter(
            models.User.user_id == "admin"
        ).first()

        if not admin_user:
            admin_user = models.User(
                user_id="admin",
                username="System Administrator",
                password_hash=auth.get_password_hash("admin123"),
                password=auth.encrypt_password("admin123"),
                user_type=models.UserType.SYSTEM_ADMIN,
                customer_id=None
            )
            self.db.add(admin_user)
            self.db.commit()
            print("✅ Default admin user created!")
            print("   User ID: admin")
            print("   Password: admin123")
        else:
            print("⚠️  Admin user already exists, skipping creation.")

        # Step 3: Load questions
        print("\n[3/3] Loading questions from questions.json...")
        question_count = self.db.query(models.Question).count()
        if question_count == 0:
            try:
                with open('questions.json', 'r', encoding='utf-8') as f:
                    questions_data = json.load(f)

                print(f"Found {len(questions_data)} questions in file.")

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
                print(f"✅ Loaded {len(questions_data)} questions!")

                # Show dimension summary
                dimensions = self.db.query(models.Question.dimension).distinct().all()
                print(f"\n📊 Questions across {len(dimensions)} dimensions:")
                for dim in dimensions:
                    count = self.db.query(models.Question).filter(
                        models.Question.dimension == dim[0]
                    ).count()
                    print(f"   • {dim[0]}: {count} questions")

            except FileNotFoundError:
                print("❌ ERROR: questions.json file not found!")
                print("   Place questions.json in the backend directory.")
            except json.JSONDecodeError as e:
                print(f"❌ ERROR: Invalid JSON in questions.json: {e}")
        else:
            print(f"⚠️  Questions already loaded ({question_count} questions).")

        # Summary
        self._print_summary("INITIALIZATION")

    # ==================== Migrations ====================

    def migrate_password_column(self):
        """Add password column to users table for plain-text password storage"""
        print("\n[Migration: password] Adding password column to users table...")

        if self.column_exists('users', 'password'):
            print("⚠️  Column 'password' already exists in users table.")
            return

        try:
            # Add password column
            self.db.execute(text("ALTER TABLE users ADD COLUMN password TEXT"))

            # Set default passwords
            self.db.execute(text("""
                UPDATE users
                SET password = CASE
                    WHEN user_id = 'admin' THEN :admin_pwd
                    ELSE :default_pwd
                END
            """), {"admin_pwd": auth.encrypt_password("admin123"),
                   "default_pwd": auth.encrypt_password("Welcome123!")})

            self.db.commit()
            print("✅ Password column added successfully!")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

    def migrate_llm_model_name(self):
        """Add model_name column to llm_configs table"""
        print("\n[Migration: llm_model] Adding model_name to llm_configs...")

        if self.column_exists('llm_configs', 'model_name'):
            print("⚠️  Column 'model_name' already exists in llm_configs table.")
            return

        try:
            self.db.execute(text(
                "ALTER TABLE llm_configs ADD COLUMN model_name VARCHAR(100) DEFAULT 'default'"
            ))
            self.db.commit()
            print("✅ model_name column added successfully!")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

    def migrate_llm_providers(self):
        """Add multi-provider LLM support (LOCAL, BEDROCK, AZURE)"""
        print("\n[Migration: llm_providers] Adding multi-provider support...")

        if self.column_exists('llm_configs', 'provider_type'):
            print("⚠️  Multi-provider columns already exist in llm_configs table.")
            return

        try:
            # Create ENUM type if it doesn't exist
            self.db.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE llmprovidertype AS ENUM ('LOCAL', 'BEDROCK', 'AZURE');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))

            # Add provider_type column
            self.db.execute(text(
                "ALTER TABLE llm_configs ADD COLUMN provider_type llmprovidertype DEFAULT 'LOCAL'"
            ))

            # Add AWS Bedrock fields
            self.db.execute(text("ALTER TABLE llm_configs ADD COLUMN aws_region VARCHAR(50)"))
            self.db.execute(text("ALTER TABLE llm_configs ADD COLUMN aws_access_key_id TEXT"))
            self.db.execute(text("ALTER TABLE llm_configs ADD COLUMN aws_secret_access_key TEXT"))
            self.db.execute(text("ALTER TABLE llm_configs ADD COLUMN aws_model_id VARCHAR(100)"))

            # Add Azure OpenAI fields
            self.db.execute(text("ALTER TABLE llm_configs ADD COLUMN azure_endpoint TEXT"))
            self.db.execute(text("ALTER TABLE llm_configs ADD COLUMN azure_api_key TEXT"))
            self.db.execute(text("ALTER TABLE llm_configs ADD COLUMN azure_deployment_name VARCHAR(100)"))
            self.db.execute(text("ALTER TABLE llm_configs ADD COLUMN azure_api_version VARCHAR(20)"))

            # Make api_url nullable (only required for LOCAL provider)
            self.db.execute(text("ALTER TABLE llm_configs ALTER COLUMN api_url DROP NOT NULL"))

            self.db.commit()
            print("✅ Multi-provider support added successfully!")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

    def migrate_questions_fields(self):
        """Add process and lifecycle_stage columns to questions table"""
        print("\n[Migration: questions_fields] Adding process and lifecycle_stage...")

        if self.column_exists('questions', 'process'):
            print("⚠️  Process and lifecycle_stage columns already exist.")
            return

        try:
            self.db.execute(text("ALTER TABLE questions ADD COLUMN process VARCHAR(100)"))
            self.db.execute(text("ALTER TABLE questions ADD COLUMN lifecycle_stage VARCHAR(100)"))
            self.db.commit()
            print("✅ Questions fields added successfully!")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

    def migrate_user_submissions(self):
        """Create user_survey_submissions table"""
        print("\n[Migration: user_submissions] Creating user_survey_submissions table...")

        if self.table_exists('user_survey_submissions'):
            print("⚠️  Table 'user_survey_submissions' already exists.")
            return

        try:
            self.db.execute(text("""
                CREATE TABLE user_survey_submissions (
                    id SERIAL PRIMARY KEY,
                    survey_id INTEGER NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    submitted_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(survey_id, user_id)
                )
            """))

            # Create indexes
            self.db.execute(text(
                "CREATE INDEX idx_user_submissions_survey ON user_survey_submissions(survey_id)"
            ))
            self.db.execute(text(
                "CREATE INDEX idx_user_submissions_user ON user_survey_submissions(user_id)"
            ))

            self.db.commit()
            print("✅ user_survey_submissions table created successfully!")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

    def run_all_migrations(self):
        """Run all migrations in order"""
        print("\n" + "="*60)
        print("  RUNNING ALL MIGRATIONS")
        print("="*60)

        migrations = [
            ("password", self.migrate_password_column),
            ("llm_model", self.migrate_llm_model_name),
            ("llm_providers", self.migrate_llm_providers),
            ("questions_fields", self.migrate_questions_fields),
            ("user_submissions", self.migrate_user_submissions),
        ]

        for name, migration_func in migrations:
            try:
                migration_func()
            except Exception as e:
                print(f"❌ Migration '{name}' failed: {e}")
                print("Stopping migration process.")
                return False

        print("\n✅ All migrations completed successfully!")
        return True

    def _print_summary(self, operation_type: str):
        """Print operation summary"""
        print("\n" + "="*60)
        print(f"  {operation_type} COMPLETE!")
        print("="*60)
        print("\n📝 Database Summary:")
        print(f"   • Questions: {self.db.query(models.Question).count()}")
        print(f"   • Customers: {self.db.query(models.Customer).count()}")
        print(f"   • Users: {self.db.query(models.User).count()}")
        print(f"   • Surveys: {self.db.query(models.Survey).count()}")

        print("\n🚀 Application URLs:")
        print("   Frontend: http://localhost:3000")
        print("   Backend API: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")

        print("\n🔑 Default Login:")
        print("   User ID: admin")
        print("   Password: admin123")
        print()


def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Consolidated Database Setup and Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--all', action='store_true',
                        help='Run initialization and all migrations')
    parser.add_argument('--init', action='store_true',
                        help='Initialize database (tables, admin, questions)')
    parser.add_argument('--migrate', action='store_true',
                        help='Run all migrations')
    parser.add_argument('--migrate-specific', type=str,
                        choices=['password', 'llm_model', 'llm_providers', 'questions_fields', 'user_submissions'],
                        help='Run a specific migration')

    args = parser.parse_args()

    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return

    try:
        with DatabaseSetup() as db_setup:
            if args.all:
                db_setup.initialize_database()
                db_setup.run_all_migrations()
            elif args.init:
                db_setup.initialize_database()
            elif args.migrate:
                db_setup.run_all_migrations()
            elif args.migrate_specific:
                migration_map = {
                    'password': db_setup.migrate_password_column,
                    'llm_model': db_setup.migrate_llm_model_name,
                    'llm_providers': db_setup.migrate_llm_providers,
                    'questions_fields': db_setup.migrate_questions_fields,
                    'user_submissions': db_setup.migrate_user_submissions,
                }
                migration_map[args.migrate_specific]()
                db_setup._print_summary(f"MIGRATION ({args.migrate_specific.upper()})")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
