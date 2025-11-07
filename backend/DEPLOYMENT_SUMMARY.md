# Database Deployment Consolidation Summary

## What Was Done

All database deployment scripts have been consolidated into a single, comprehensive deployment script: `deploy_db.py`

## New Consolidated Script

### Main Script: `deploy_db.py`

A single, unified script that handles:
- ✅ Database initialization (tables, admin user, questions)
- ✅ All migrations in correct order
- ✅ Proper error handling and logging
- ✅ Idempotent operations (safe to run multiple times)
- ✅ Detailed progress reporting

### Usage Examples

```bash
# Full deployment (recommended for new environments)
python deploy_db.py

# Initialize only
python deploy_db.py --init-only

# Migrate only
python deploy_db.py --migrate-only

# Run specific migration
python deploy_db.py --migrate password
python deploy_db.py --migrate llm_providers
```

## Helper Scripts

### For Linux/Mac: `deploy.sh`
```bash
chmod +x deploy.sh
./deploy.sh full              # Full deployment
./deploy.sh init-only         # Initialize only
./deploy.sh migrate-only      # Migrate only
./deploy.sh migrate password  # Specific migration
```

### For Windows: `deploy.ps1`
```powershell
.\deploy.ps1 full              # Full deployment
.\deploy.ps1 init-only         # Initialize only
.\deploy.ps1 migrate-only      # Migrate only
.\deploy.ps1 migrate password  # Specific migration
```

## What Gets Deployed

### Initialization
1. Creates all database tables (from SQLAlchemy models)
2. Creates default admin user (admin/admin123)
3. Loads questions from `questions.json`

### Migrations (in order)
1. **password** - Adds encrypted password column to users table
2. **llm_model** - Adds model_name column to llm_configs
3. **llm_providers** - Adds multi-provider LLM support (LOCAL, BEDROCK, AZURE)
4. **questions_fields** - Adds process and lifecycle_stage to questions
5. **user_submissions** - Creates user_survey_submissions table

## Migration from Old Scripts

The old individual scripts are still present for backward compatibility, but the new consolidated script is recommended:

| Old Script | New Command |
|------------|-------------|
| `python init_db.py` | `python deploy_db.py --init-only` |
| `python migrate_db.py` | `python deploy_db.py --migrate password` |
| `python migrate_llm.py` | `python deploy_db.py --migrate llm_model` |
| `python migrate_llm_providers.py` | `python deploy_db.py --migrate llm_providers` |
| `python migrate_questions.py` | `python deploy_db.py --migrate questions_fields` |
| `python migrate_user_submissions.py` | `python deploy_db.py --migrate user_submissions` |

## Features

### ✅ Idempotent Operations
- Safe to run multiple times
- Checks for existing tables/columns before creating
- Skips operations that have already been completed

### ✅ Comprehensive Logging
- Detailed progress reporting
- Clear error messages
- Summary statistics after deployment

### ✅ Error Handling
- Rollback on errors
- Continues with other migrations even if one fails
- Detailed error reporting

### ✅ Docker Compatible
- Works seamlessly in Docker containers
- Can be run via `docker exec` commands

## Documentation

- **DEPLOYMENT.md** - Complete deployment guide with troubleshooting
- **DEPLOYMENT_SUMMARY.md** - This file (quick reference)

## Next Steps

1. Test the deployment script in your environment
2. Update your CI/CD pipelines to use the new script
3. Consider deprecating old individual scripts (they remain for compatibility)

## Verification

After deployment, verify everything worked:

```bash
# Check users
python db_utils.py --list-users

# Validate questions
python db_utils.py --validate-questions

# Check database stats
python db_utils.py --list-customers
```

## Default Credentials

- **User ID:** admin
- **Password:** admin123

⚠️ **Change in production!**

```bash
python db_utils.py --reset-password admin --password <secure_password>
```

