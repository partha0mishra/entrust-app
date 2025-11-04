# Database Setup and Maintenance Guide

This guide explains how to use the consolidated database scripts for setting up and maintaining the EnTrust application database in any environment.

## Quick Start

### Initial Setup (New Environment)

To set up the database from scratch in a new environment:

```bash
cd backend
python db_setup.py --all
```

This will:
1. Create all database tables
2. Create the default admin user
3. Load questions from `questions.json`
4. Run all database migrations

### Selective Setup

If you only need specific operations:

```bash
# Initialize database only (tables + admin + questions)
python db_setup.py --init

# Run all migrations only
python db_setup.py --migrate

# Run a specific migration
python db_setup.py --migrate-specific password
python db_setup.py --migrate-specific llm_providers
```

## Available Scripts

### 1. `db_setup.py` - Database Initialization and Migrations

Consolidated script that replaces:
- `init_db.py` - Initial database setup
- `migrate_db.py` - Password column migration
- `migrate_llm.py` - LLM model name migration
- `migrate_llm_providers.py` - Multi-provider LLM migration
- `migrate_questions.py` - Question fields migration
- `migrate_user_submissions.py` - User submissions table migration

#### Usage

```bash
# Full setup (recommended for new environments)
python db_setup.py --all

# Initialize database
python db_setup.py --init

# Run all migrations
python db_setup.py --migrate

# Run specific migration
python db_setup.py --migrate-specific <migration_name>
```

#### Available Migrations

| Migration Name | Description |
|----------------|-------------|
| `password` | Add password column to users table |
| `llm_model` | Add model_name column to llm_configs |
| `llm_providers` | Add multi-provider LLM support (LOCAL, BEDROCK, AZURE) |
| `questions_fields` | Add process and lifecycle_stage columns to questions |
| `user_submissions` | Create user_survey_submissions table |

### 2. `db_utils.py` - Database Maintenance and Utilities

Consolidated script that replaces:
- `reload_questions.py` - Reload question fields
- `validate_questions.py` - Validate question data
- `query_questions.py` - Query question distribution
- `reset_admin_password.py` - Reset admin password
- `reset_password_standalone.py` - Standalone password reset

#### Usage

```bash
# Question management
python db_utils.py --reload-questions       # Reload from questions.json
python db_utils.py --validate-questions     # Validate data integrity
python db_utils.py --query-questions        # Analyze distribution

# User management
python db_utils.py --reset-password admin   # Reset admin password
python db_utils.py --reset-password admin --password newpass123  # Custom password
python db_utils.py --list-users             # List all users

# Data exploration
python db_utils.py --list-customers         # List all customers
python db_utils.py --list-surveys           # List all surveys
```

## Environment-Specific Setup

### Local Development

```bash
# First time setup
python db_setup.py --all

# After pulling code changes that include migrations
python db_setup.py --migrate
```

### Docker Environment

```bash
# Inside the backend container
docker exec -it entrust_backend python db_setup.py --all

# Or run specific operations
docker exec -it entrust_backend python db_utils.py --validate-questions
```

### Production Deployment

```bash
# 1. Initialize database
python db_setup.py --init

# 2. Run migrations
python db_setup.py --migrate

# 3. Validate setup
python db_utils.py --validate-questions
python db_utils.py --list-users
```

## Migration to New Scripts

If you have been using the old individual scripts, you can now use the consolidated versions:

### Old Scripts → New Scripts

| Old Script | New Command |
|------------|-------------|
| `python init_db.py` | `python db_setup.py --init` |
| `python migrate_db.py` | `python db_setup.py --migrate-specific password` |
| `python migrate_llm.py` | `python db_setup.py --migrate-specific llm_model` |
| `python migrate_llm_providers.py` | `python db_setup.py --migrate-specific llm_providers` |
| `python migrate_questions.py` | `python db_setup.py --migrate-specific questions_fields` |
| `python migrate_user_submissions.py` | `python db_setup.py --migrate-specific user_submissions` |
| `python reload_questions.py` | `python db_utils.py --reload-questions` |
| `python validate_questions.py` | `python db_utils.py --validate-questions` |
| `python query_questions.py` | `python db_utils.py --query-questions` |
| `python reset_admin_password.py` | `python db_utils.py --reset-password admin` |

**Note:** The old scripts remain in place for backward compatibility, but it's recommended to use the new consolidated scripts going forward.

## Troubleshooting

### Database Connection Issues

If you encounter connection errors:

1. Check `DATABASE_URL` environment variable:
   ```bash
   echo $DATABASE_URL
   ```

2. Verify PostgreSQL is running:
   ```bash
   docker ps | grep postgres
   ```

3. Test database connection:
   ```bash
   psql $DATABASE_URL -c "SELECT 1"
   ```

### Migration Errors

If a migration fails:

1. Check what migrations have already been applied:
   ```bash
   python db_utils.py --list-users  # Verifies basic connectivity
   ```

2. Run migrations individually:
   ```bash
   python db_setup.py --migrate-specific password
   python db_setup.py --migrate-specific llm_model
   # etc.
   ```

3. If a migration reports "already exists", it's safe to skip - the migration is idempotent.

### Questions Not Loading

If questions aren't loading:

1. Verify `questions.json` exists in the `backend` directory:
   ```bash
   ls -l backend/questions.json
   ```

2. Validate JSON format:
   ```bash
   python -m json.tool questions.json > /dev/null
   ```

3. Reload questions:
   ```bash
   python db_utils.py --reload-questions
   ```

## Default Credentials

After initialization, the default admin credentials are:

- **User ID:** `admin`
- **Password:** `admin123`

**Important:** Change the admin password in production environments!

```bash
python db_utils.py --reset-password admin --password <secure_password>
```

## Prompts Organization

The LLM prompts have been organized into a separate module at `backend/app/prompts/`:

```
backend/app/prompts/
├── __init__.py                       # Module exports
├── base_prompts.py                   # Shared prompt components
├── dimension_prompts.py              # Dimension-specific prompts
├── analysis_prompts.py               # Analysis prompt functions
└── overall_summary_prompts.py        # Overall summary prompts
```

This organization makes it easier to:
- Maintain and update prompts
- Add new dimension-specific prompts
- Customize prompts per deployment
- Version control prompt changes

## Additional Resources

- **Application Setup:** See main `README.md`
- **LLM Configuration:** See `LLM_CONFIGURATION.md`
- **API Documentation:** http://localhost:8000/docs (when running)
- **Database Schema:** See `backend/app/models.py`
