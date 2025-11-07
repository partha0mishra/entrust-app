# Database Deployment Guide

This guide explains how to deploy and initialize the EnTrust database using the consolidated deployment script.

## Quick Start

### Full Deployment (Recommended for New Environments)

Deploys everything: initialization + all migrations

```bash
# Local deployment
python deploy_db.py

# Docker deployment
docker exec -it entrust_backend python deploy_db.py
```

### Step-by-Step Deployment

#### 1. Initialize Database Only

Creates tables, admin user, and loads questions:

```bash
python deploy_db.py --init-only
```

#### 2. Run All Migrations

Applies all database migrations:

```bash
python deploy_db.py --migrate-only
```

#### 3. Run Specific Migration

Run a single migration:

```bash
python deploy_db.py --migrate password
python deploy_db.py --migrate llm_model
python deploy_db.py --migrate llm_providers
python deploy_db.py --migrate questions_fields
python deploy_db.py --migrate user_submissions
```

## Available Migrations

| Migration Name | Description |
|----------------|-------------|
| `password` | Add password column to users table (encrypted plaintext storage) |
| `llm_model` | Add model_name column to llm_configs table |
| `llm_providers` | Add multi-provider LLM support (LOCAL, BEDROCK, AZURE) |
| `questions_fields` | Add process and lifecycle_stage columns to questions table |
| `user_submissions` | Create user_survey_submissions table for per-user tracking |

## Deployment Scenarios

### Local Development

```bash
# First time setup
cd backend
python deploy_db.py

# After pulling new migrations
python deploy_db.py --migrate-only
```

### Docker Environment

```bash
# Full deployment
docker exec -it entrust_backend python deploy_db.py

# Initialize only
docker exec -it entrust_backend python deploy_db.py --init-only

# Migrate only
docker exec -it entrust_backend python deploy_db.py --migrate-only
```

### Production Deployment

```bash
# 1. Initialize database
python deploy_db.py --init-only

# 2. Run migrations
python deploy_db.py --migrate-only

# 3. Verify deployment
python db_utils.py --list-users
python db_utils.py --validate-questions
```

## Default Credentials

After deployment, the default admin credentials are:

- **User ID:** `admin`
- **Password:** `admin123`

**⚠️ IMPORTANT:** Change the admin password in production environments!

```bash
python db_utils.py --reset-password admin --password <secure_password>
```

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

1. Check what migrations have already been applied by examining the database schema
2. Run migrations individually to identify the problematic one
3. Check logs for detailed error messages

### Questions Not Loading

If questions aren't loading:

1. Verify `questions.json` exists in the `backend` directory
2. Validate JSON format:
   ```bash
   python -m json.tool questions.json > /dev/null
   ```
3. Check file permissions and encoding (must be UTF-8)

## Migration from Old Scripts

The consolidated `deploy_db.py` script replaces all individual scripts:

| Old Script | New Command |
|------------|-------------|
| `python init_db.py` | `python deploy_db.py --init-only` |
| `python migrate_db.py` | `python deploy_db.py --migrate password` |
| `python migrate_llm.py` | `python deploy_db.py --migrate llm_model` |
| `python migrate_llm_providers.py` | `python deploy_db.py --migrate llm_providers` |
| `python migrate_questions.py` | `python deploy_db.py --migrate questions_fields` |
| `python migrate_user_submissions.py` | `python deploy_db.py --migrate user_submissions` |

**Note:** The old scripts remain for backward compatibility, but using `deploy_db.py` is recommended.

## What Gets Deployed

### Initialization (`--init-only`)

1. Creates all database tables (SQLAlchemy models)
2. Creates default admin user
3. Loads questions from `questions.json`

### Migrations

1. **password**: Adds encrypted password column to users
2. **llm_model**: Adds model_name support to LLM configs
3. **llm_providers**: Adds multi-provider support (LOCAL, BEDROCK, AZURE)
4. **questions_fields**: Adds process and lifecycle_stage to questions
5. **user_submissions**: Creates user survey submission tracking table

## Verification

After deployment, verify the setup:

```bash
# Check users
python db_utils.py --list-users

# Check questions
python db_utils.py --validate-questions
python db_utils.py --query-questions

# Check customers
python db_utils.py --list-customers
```

## Support

For issues or questions:
- Check the logs for detailed error messages
- Verify environment variables are set correctly
- Ensure PostgreSQL is accessible and running
- Review the database schema in `app/models.py`

