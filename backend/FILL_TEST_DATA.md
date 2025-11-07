# Fill Test Data Script

This script automatically populates the database with NVIDIA test data for development and testing.

## What It Creates

### Customer
- **Code**: NVDA
- **Name**: NVIDIA
- **Industry**: High Tech
- **Location**: Santa Clara, CA
- **Description**: Nvidia Corporation is an American technology company headquartered in Santa Clara, California. Founded in 1993 by Jensen Huang, Chris Malachowsky, and Curtis Priem

### Users

| User ID | Name | Password | User Type | Customer |
|---------|------|----------|-----------|----------|
| jhuang | Jensen Huang | Welcome123! | CXO | NVIDIA |
| Partha | Partha Mishra | Welcome123! | Participant | NVIDIA |
| Madhu | Madhu Ivaturi | Welcome123! | Participant | NVIDIA |
| Nagaraj | Nagaraj Sastry | Welcome123! | Sales | (none) |

### Survey Data
- Creates a survey for NVIDIA customer
- Fills responses for CXO and Participant users
- Random scores (1-10) with realistic comments based on score ranges
- Survey status set to "Submitted" and ready for report generation

## Usage

### Automatic Execution (Docker)
The script runs automatically during `docker compose up`:
```bash
docker compose up --build
```

The startup sequence:
1. Wait for PostgreSQL
2. Deploy database schema (deploy_db.py)
3. **Fill NVIDIA test data (fill_test_data.py)** ← Automatic
4. Start FastAPI server

### Manual Execution

#### Create test data (skip if already exists):
```bash
cd backend
python fill_test_data.py
```

#### Force recreate test data:
```bash
python fill_test_data.py --force
```

## Behavior

### Smart Skip Logic
- If NVIDIA customer already exists with a completed survey
- And survey has responses
- The script will skip execution to save time
- Shows a summary and exits quickly

**Example Output:**
```
======================================================================
  CREATING TEST DATA FOR REPORT GENERATION
======================================================================

✓ NVIDIA test data already exists and is complete!
   Customer: NVIDIA
   Survey Status: Submitted
   Responses: 540

⏩ Skipping test data creation. Use --force to recreate.
======================================================================
```

### Force Recreation
Use `--force` flag to delete and recreate all NVIDIA data:
```bash
python fill_test_data.py --force
```

This will:
1. Delete existing NVIDIA customer
2. Delete associated users (CXO + Participants)
3. Delete surveys and responses (cascade)
4. Recreate everything fresh

## Login Credentials

After running the script, you can login with:

**CXO Access:**
- User ID: `jhuang`
- Password: `Welcome123!`
- Role: View all reports, manage survey

**Participant Access:**
- User ID: `Partha` or `Madhu`
- Password: `Welcome123!`
- Role: Submit survey responses

**Sales Access:**
- User ID: `Nagaraj`
- Password: `Welcome123!`
- Role: Manage customers, view reports

**System Admin:**
- User ID: `admin`
- Password: `admin123`
- Role: Full system access

## Features

### Realistic Survey Responses
The script generates diverse, realistic comments based on score ranges:

- **Scores 8-10 (High)**: Mature governance practices, strong compliance
- **Scores 5-7 (Medium)**: Functional but needs improvement, gaps identified
- **Scores 1-4 (Low)**: Critical gaps, requires remediation

Each response includes:
- Random score (1-10)
- Contextually appropriate comment
- Realistic patterns across all dimensions

### Complete Survey Data
- Covers all 8 data governance dimensions
- Includes responses for all question types (CXO, Participant)
- Survey marked as "Submitted" for immediate report generation
- All required relationships established (customer → users → survey → responses)

## Integration with Docker Compose

The script is integrated into the Docker startup sequence in `docker-compose.yml`:

```yaml
command: >
  sh -c "
    echo 'Waiting for PostgreSQL to be ready...' &&
    until PGPASSWORD=entrust_pass psql -h postgres -U entrust_user -d entrust_db -c 'SELECT 1' >/dev/null 2>&1; do
      echo 'PostgreSQL is unavailable - sleeping'
      sleep 1
    done &&
    echo 'PostgreSQL is ready! Deploying database...' &&
    python deploy_db.py &&
    echo 'Filling test data (NVIDIA)...' &&
    python fill_test_data.py &&
    echo 'Starting FastAPI server...' &&
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  "
```

## Files

- `backend/fill_test_data.py` - Main script
- `backend/FILL_TEST_DATA.md` - This documentation
- `docker-compose.yml` - Automatic execution configuration

## Troubleshooting

### "Error: relation does not exist"
Run database deployment first:
```bash
python deploy_db.py
```

### Script takes too long
If data already exists, the script skips quickly. First run takes ~10-30 seconds.

### Need fresh data
Use `--force` flag:
```bash
python fill_test_data.py --force
```

### Docker container won't start
Check logs:
```bash
docker logs entrust_backend
```

The fill_test_data.py step should complete successfully before uvicorn starts.

## Notes

- Script is idempotent (safe to run multiple times)
- Uses smart skip logic to avoid redundant work
- Sales user (Nagaraj) has no customer association (cross-customer access)
- All passwords are "Welcome123!" except admin ("admin123")
- Change passwords in production!
