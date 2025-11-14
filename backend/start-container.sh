#!/bin/sh
set -e

echo "[$(date)] Waiting for database..."
python - <<'PY'
import os
import time
from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise SystemExit("DATABASE_URL environment variable is required")

engine = create_engine(database_url, pool_pre_ping=True)
max_attempts = 30

for attempt in range(1, max_attempts + 1):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[INIT] Database connection established on attempt {attempt}.")
        break
    except Exception as exc:
        if attempt == max_attempts:
            raise
        print(f"[INIT] Database not ready (attempt {attempt}/{max_attempts}): {exc}")
        time.sleep(5)
PY

run_script() {
  LABEL="$1"
  shift
  echo "[$(date)] Starting $LABEL..."
  if "$@"; then
    echo "[$(date)] Completed $LABEL."
  else
    STATUS=$?
    echo "[$(date)] WARNING: $LABEL failed with exit code $STATUS. Continuing startup."
  fi
}

run_script "EVTech dataset (fill_tesla_data.py)" python fill_tesla_data.py
run_script "GPUTech dataset (fill_test_data.py)" python fill_test_data.py
run_script "TechSoft/Noodle/FruitTech/MarketPlace datasets (fill_msft_goog_aapl_amzn.py)" python fill_msft_goog_aapl_amzn.py

echo "[$(date)] Starting FastAPI (uvicorn)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

