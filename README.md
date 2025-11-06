# EnTrust - Data Governance Survey Platform

EnTrust is a comprehensive data governance survey platform built with FastAPI (backend) and React (frontend).

## Features

- User authentication and role-based access control
- Survey management with multi-dimensional questions
- LLM-powered analysis and reporting
- PDF report generation
- Customer and user management

## Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Frontend**: React + Vite
- **Database**: PostgreSQL 15
- **Containerization**: Docker

## Quick Start (Local Development)

### Prerequisites

- Docker and Docker Compose
- Git

### Running Locally

1. Clone the repository:
```bash
git clone <repository-url>
cd entrust
```

2. Start the application:
```bash
docker compose up -d
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Default Login Credentials

- **Username**: `admin`
- **Password**: `Welcome123!`

## Azure Deployment

For deploying to Azure, see [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md).

### Quick Deployment

**Prerequisites:**
- Azure CLI installed and logged in
- Access to Azure subscription with write permissions
- Access to the following Azure resources:
  - Resource Group: `entrust-rg`
  - Container Registry: `enacceleratorsacr`
  - PostgreSQL Server: `entrust-postgres-server` (in `en_accelerators_db` resource group)

**Deploy:**

Windows (PowerShell):
```powershell
.\deploy-azure.ps1
```

Linux/Mac (Bash):
```bash
chmod +x deploy-azure.sh
./deploy-azure.sh
```

The script will:
- Start PostgreSQL server if stopped
- Create database if needed
- Build and push Docker images to Azure Container Registry
- Deploy backend and frontend as Azure Container Apps with HTTPS
- Configure all environment variables and CORS settings

## Project Structure

```
entrust/
├── backend/          # FastAPI backend application
│   ├── app/          # Main application code
│   ├── Dockerfile    # Development Dockerfile
│   ├── Dockerfile.prod  # Production Dockerfile
│   └── requirements.txt
├── frontend/         # React frontend application
│   ├── src/          # Source code
│   ├── Dockerfile    # Development Dockerfile
│   ├── Dockerfile.prod  # Production Dockerfile
│   └── package.json
├── docker-compose.yml  # Local development setup
├── deploy-azure.ps1   # Azure deployment script (PowerShell)
├── deploy-azure.sh    # Azure deployment script (Bash)
└── AZURE_DEPLOYMENT.md # Detailed Azure deployment guide
```

## Configuration

### Environment Variables

**Backend:**
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration (default: 1440)
- `LOG_LEVEL`: Logging level (DEBUG/INFO)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

**Frontend:**
- `VITE_API_URL`: Backend API URL (build-time variable)

## Documentation

- [Azure Deployment Guide](AZURE_DEPLOYMENT.md) - Detailed Azure deployment instructions
- [LLM Configuration Guide](LLM_CONFIGURATION.md) - LLM provider setup
- [Enhanced Reporting Plan](ENHANCED_REPORTING_PLAN.md) - Reporting features

## License

[Add your license here]

