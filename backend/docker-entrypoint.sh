#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=entrust_pass psql -h postgres -U entrust_user -d entrust_db -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is ready!"
echo "Deploying database..."

# Run database deployment
python deploy_db.py

echo "Database deployment completed!"
echo "Starting FastAPI server..."

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

