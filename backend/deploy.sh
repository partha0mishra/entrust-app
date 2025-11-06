#!/bin/bash
# Database Deployment Helper Script
# Usage: ./deploy.sh [init-only|migrate-only|migrate <name>|full]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "EnTrust Database Deployment"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check if database is accessible
if [ -z "$DATABASE_URL" ]; then
    echo "Warning: DATABASE_URL environment variable not set"
    echo "Using default: postgresql://entrust_user:entrust_pass@localhost:5432/entrust_db"
    echo ""
fi

# Run deployment based on argument
case "${1:-full}" in
    init-only)
        echo "Running database initialization only..."
        python deploy_db.py --init-only
        ;;
    migrate-only)
        echo "Running migrations only..."
        python deploy_db.py --migrate-only
        ;;
    migrate)
        if [ -z "$2" ]; then
            echo "Error: Migration name required"
            echo "Usage: ./deploy.sh migrate <migration_name>"
            echo "Available migrations: password, llm_model, llm_providers, questions_fields, user_submissions"
            exit 1
        fi
        echo "Running migration: $2"
        python deploy_db.py --migrate "$2"
        ;;
    full)
        echo "Running full deployment (init + migrations)..."
        python deploy_db.py
        ;;
    *)
        echo "Usage: ./deploy.sh [init-only|migrate-only|migrate <name>|full]"
        echo ""
        echo "Options:"
        echo "  init-only       - Initialize database only (tables, admin, questions)"
        echo "  migrate-only    - Run all migrations only"
        echo "  migrate <name>  - Run a specific migration"
        echo "  full            - Full deployment (default)"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Deployment completed!"
echo "=========================================="

