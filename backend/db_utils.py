"""
Consolidated Database Utilities Script
=======================================
This script provides various database maintenance and utility operations.

Usage:
    python db_utils.py --reload-questions     # Reload question fields from questions.json
    python db_utils.py --validate-questions   # Validate and report on question data integrity
    python db_utils.py --query-questions      # Analyze and report question distribution
    python db_utils.py --reset-password <user_id> [--password <pwd>]  # Reset user password
    python db_utils.py --list-users           # List all users in the system
    python db_utils.py --list-customers       # List all customers
    python db_utils.py --list-surveys         # List all surveys
"""

import sys
import json
import argparse
from collections import defaultdict
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, auth


class DatabaseUtils:
    """Handles database utility operations"""

    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"\n❌ Error occurred: {exc_val}")
            self.db.rollback()
        self.db.close()

    # ==================== Question Management ====================

    def reload_questions(self):
        """Reload question fields from questions.json file"""
        print("\n" + "="*60)
        print("  RELOADING QUESTIONS FROM FILE")
        print("="*60)

        try:
            with open('questions.json', 'r', encoding='utf-8') as f:
                questions_data = json.load(f)

            print(f"\nFound {len(questions_data)} questions in file.")
            updated_count = 0
            batch_size = 100

            for i, q_data in enumerate(questions_data):
                question = self.db.query(models.Question).filter(
                    models.Question.question_id == q_data['id']
                ).first()

                if question:
                    question.category = q_data.get('category')
                    question.question_type = q_data.get('question_type')
                    question.process = q_data.get('process')
                    question.lifecycle_stage = q_data.get('lifecycle_stage')
                    updated_count += 1

                    # Commit in batches
                    if (i + 1) % batch_size == 0:
                        self.db.commit()
                        print(f"  Processed {i + 1}/{len(questions_data)} questions...")

            # Final commit
            self.db.commit()
            print(f"\n✅ Updated {updated_count} questions successfully!")

        except FileNotFoundError:
            print("❌ ERROR: questions.json file not found!")
        except json.JSONDecodeError as e:
            print(f"❌ ERROR: Invalid JSON in questions.json: {e}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            raise

    def validate_questions(self):
        """Validate and report on question data integrity"""
        print("\n" + "="*60)
        print("  QUESTION DATA VALIDATION REPORT")
        print("="*60)

        questions = self.db.query(models.Question).all()
        total = len(questions)

        # Count field population
        category_count = sum(1 for q in questions if q.category)
        question_type_count = sum(1 for q in questions if q.question_type)
        process_count = sum(1 for q in questions if q.process)
        lifecycle_count = sum(1 for q in questions if q.lifecycle_stage)

        print(f"\n📊 Overall Statistics:")
        print(f"   Total Questions: {total}")
        print(f"   Category filled: {category_count} ({category_count/total*100:.1f}%)")
        print(f"   Question Type filled: {question_type_count} ({question_type_count/total*100:.1f}%)")
        print(f"   Process filled: {process_count} ({process_count/total*100:.1f}%)")
        print(f"   Lifecycle Stage filled: {lifecycle_count} ({lifecycle_count/total*100:.1f}%)")

        # Group by dimension
        print(f"\n📋 Questions by Dimension:")
        dimension_data = defaultdict(lambda: {'total': 0, 'cxo': 0, 'general': 0})

        for q in questions:
            dimension_data[q.dimension]['total'] += 1
            if q.question_type == 'CXO':
                dimension_data[q.dimension]['cxo'] += 1
            elif q.question_type == 'General':
                dimension_data[q.dimension]['general'] += 1

        for dim, data in sorted(dimension_data.items()):
            print(f"\n   {dim}:")
            print(f"      Total: {data['total']}")
            print(f"      CXO: {data['cxo']}")
            print(f"      General: {data['general']}")

        # Show sample questions with new fields
        print(f"\n📝 Sample Questions (first 3):")
        for q in questions[:3]:
            print(f"\n   ID: {q.question_id}")
            print(f"   Text: {q.text[:60]}...")
            print(f"   Dimension: {q.dimension}")
            print(f"   Category: {q.category or 'N/A'}")
            print(f"   Type: {q.question_type or 'N/A'}")
            print(f"   Process: {q.process or 'N/A'}")
            print(f"   Lifecycle: {q.lifecycle_stage or 'N/A'}")

        # Check for null values
        null_questions = [q for q in questions if not (q.category and q.question_type)]
        if null_questions:
            print(f"\n⚠️  Found {len(null_questions)} questions with null category or type:")
            for q in null_questions[:5]:
                print(f"   • {q.question_id}: {q.text[:50]}...")

    def query_questions(self):
        """Analyze and report on question distribution"""
        print("\n" + "="*60)
        print("  QUESTION DISTRIBUTION ANALYSIS")
        print("="*60)

        questions = self.db.query(models.Question).all()
        total = len(questions)

        print(f"\n📊 Total Questions: {total}")

        # Analyze by dimension
        print(f"\n📋 Questions by Dimension:")
        print(f"{'Dimension':<40} {'Total':>8} {'CXO':>8} {'General':>8}")
        print("-" * 68)

        dimension_stats = defaultdict(lambda: {'total': 0, 'cxo': 0, 'general': 0})

        for q in questions:
            dimension_stats[q.dimension]['total'] += 1
            if q.question_type == 'CXO':
                dimension_stats[q.dimension]['cxo'] += 1
            elif q.question_type == 'General':
                dimension_stats[q.dimension]['general'] += 1

        for dim in sorted(dimension_stats.keys()):
            stats = dimension_stats[dim]
            print(f"{dim:<40} {stats['total']:>8} {stats['cxo']:>8} {stats['general']:>8}")

        print("-" * 68)
        total_cxo = sum(s['cxo'] for s in dimension_stats.values())
        total_general = sum(s['general'] for s in dimension_stats.values())
        print(f"{'TOTAL':<40} {total:>8} {total_cxo:>8} {total_general:>8}")

        # Analyze by category
        if any(q.category for q in questions):
            print(f"\n📂 Questions by Category:")
            category_counts = defaultdict(int)
            for q in questions:
                if q.category:
                    category_counts[q.category] += 1

            for cat in sorted(category_counts.keys()):
                print(f"   {cat}: {category_counts[cat]}")

        # Analyze by process
        if any(q.process for q in questions):
            print(f"\n⚙️  Questions by Process:")
            process_counts = defaultdict(int)
            for q in questions:
                if q.process:
                    process_counts[q.process] += 1

            for proc in sorted(process_counts.keys()):
                print(f"   {proc}: {process_counts[proc]}")

        # Analyze by lifecycle stage
        if any(q.lifecycle_stage for q in questions):
            print(f"\n🔄 Questions by Lifecycle Stage:")
            lifecycle_counts = defaultdict(int)
            for q in questions:
                if q.lifecycle_stage:
                    lifecycle_counts[q.lifecycle_stage] += 1

            for stage in sorted(lifecycle_counts.keys()):
                print(f"   {stage}: {lifecycle_counts[stage]}")

    # ==================== User Management ====================

    def reset_password(self, user_id: str, password: str = "Welcome123!"):
        """Reset a user's password"""
        print(f"\nResetting password for user: {user_id}")

        user = self.db.query(models.User).filter(
            models.User.user_id == user_id
        ).first()

        if not user:
            print(f"❌ User '{user_id}' not found!")
            # Try to find by ID
            try:
                user_pk = int(user_id)
                user = self.db.query(models.User).filter(
                    models.User.id == user_pk
                ).first()
            except ValueError:
                pass

        if not user:
            print("❌ User not found!")
            return

        try:
            user.password_hash = auth.get_password_hash(password)
            if hasattr(models.User, 'password'):
                user.password = auth.encrypt_password(password)
            self.db.commit()

            print(f"✅ Password reset successfully!")
            print(f"   User ID: {user.user_id}")
            print(f"   Username: {user.username}")
            print(f"   New Password: {password}")

        except Exception as e:
            print(f"❌ Password reset failed: {e}")
            raise

    def list_users(self):
        """List all users in the system"""
        print("\n" + "="*60)
        print("  ALL USERS")
        print("="*60)

        users = self.db.query(models.User).all()

        if not users:
            print("\nNo users found.")
            return

        print(f"\nTotal Users: {len(users)}\n")
        print(f"{'ID':>4} {'User ID':<20} {'Username':<30} {'Type':<15} {'Customer ID':<12}")
        print("-" * 85)

        for user in users:
            print(f"{user.id:>4} {user.user_id:<20} {user.username:<30} "
                  f"{user.user_type.value:<15} {str(user.customer_id or 'N/A'):<12}")

    def list_customers(self):
        """List all customers"""
        print("\n" + "="*60)
        print("  ALL CUSTOMERS")
        print("="*60)

        customers = self.db.query(models.Customer).all()

        if not customers:
            print("\nNo customers found.")
            return

        print(f"\nTotal Customers: {len(customers)}\n")

        for customer in customers:
            print(f"\nID: {customer.id}")
            print(f"Code: {customer.customer_code}")
            print(f"Name: {customer.name}")
            print(f"Industry: {customer.industry or 'N/A'}")
            print(f"Location: {customer.location or 'N/A'}")
            print(f"Created: {customer.created_at}")

    def list_surveys(self):
        """List all surveys"""
        print("\n" + "="*60)
        print("  ALL SURVEYS")
        print("="*60)

        surveys = self.db.query(models.Survey).all()

        if not surveys:
            print("\nNo surveys found.")
            return

        print(f"\nTotal Surveys: {len(surveys)}\n")
        print(f"{'ID':>4} {'Customer ID':>12} {'Status':<15} {'Submitted':<20} {'Created':<20}")
        print("-" * 75)

        for survey in surveys:
            submitted = survey.submitted_at.strftime('%Y-%m-%d %H:%M') if survey.submitted_at else 'Not submitted'
            created = survey.created_at.strftime('%Y-%m-%d %H:%M') if survey.created_at else 'N/A'
            print(f"{survey.id:>4} {survey.customer_id:>12} {survey.status:<15} "
                  f"{submitted:<20} {created:<20}")


def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Consolidated Database Utilities Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--reload-questions', action='store_true',
                        help='Reload question fields from questions.json')
    parser.add_argument('--validate-questions', action='store_true',
                        help='Validate and report on question data integrity')
    parser.add_argument('--query-questions', action='store_true',
                        help='Analyze and report question distribution')
    parser.add_argument('--reset-password', type=str, metavar='USER_ID',
                        help='Reset user password')
    parser.add_argument('--password', type=str, default='Welcome123!',
                        help='New password (default: Welcome123!)')
    parser.add_argument('--list-users', action='store_true',
                        help='List all users')
    parser.add_argument('--list-customers', action='store_true',
                        help='List all customers')
    parser.add_argument('--list-surveys', action='store_true',
                        help='List all surveys')

    args = parser.parse_args()

    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return

    try:
        with DatabaseUtils() as utils:
            if args.reload_questions:
                utils.reload_questions()
            elif args.validate_questions:
                utils.validate_questions()
            elif args.query_questions:
                utils.query_questions()
            elif args.reset_password:
                utils.reset_password(args.reset_password, args.password)
            elif args.list_users:
                utils.list_users()
            elif args.list_customers:
                utils.list_customers()
            elif args.list_surveys:
                utils.list_surveys()

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
