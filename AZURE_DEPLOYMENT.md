# Azure Deployment Guide for EnTrust

This guide explains how to deploy the EnTrust application to Azure using Azure Container Apps.

## Prerequisites

1. Azure CLI installed and logged in
2. Azure subscription with write permissions (currently subscription is read-only)
3. Docker installed locally (for initial testing)

## Architecture

- **Frontend**: React app deployed as Azure Container App
- **Backend**: FastAPI app deployed as Azure Container App  
- **Database**: Azure Database for PostgreSQL Flexible Server

## Deployment Steps

### Option 1: Automated Deployment (Recommended)

#### Windows (PowerShell):
```powershell
.\deploy-azure.ps1
```

#### Linux/Mac (Bash):
```bash
chmod +x deploy-azure.sh
./deploy-azure.sh
```

### Option 2: Manual Deployment

#### 1. Login to Azure Container Registry
```bash
az acr login --name enacceleratorsacr
```

#### 2. Start PostgreSQL Server (if stopped) and Create Database
The deployment uses an existing PostgreSQL server: `entrust-postgres-server` in `en_accelerators_db` resource group.

```bash
# Check server status and start if stopped
az postgres flexible-server show \
    --name entrust-postgres-server \
    --resource-group en_accelerators_db \
    --query "state" \
    --output tsv

# Start server if stopped
az postgres flexible-server start \
    --name entrust-postgres-server \
    --resource-group en_accelerators_db

# Create database
az postgres flexible-server db create \
    --resource-group en_accelerators_db \
    --server-name entrust-postgres-server \
    --database-name entrust_db
```

**Note**: The admin user is `entrust_admin`. Update the password in the deployment script if different from `Welcome123!@#`.

#### 3. Build and Push Backend Image
```bash
cd backend
az acr build \
    --registry enacceleratorsacr \
    --image entrust-backend:latest \
    --file Dockerfile.prod \
    .
cd ..
```

#### 4. Build and Push Frontend Image
```bash
cd frontend
az acr build \
    --registry enacceleratorsacr \
    --image entrust-frontend:latest \
    --file Dockerfile.prod \
    --build-arg VITE_API_URL=https://entrust-backend.azurecontainerapps.io \
    .
cd ..
```

#### 5. Create Container Apps Environment
```bash
az containerapp env create \
    --name entrust-env \
    --resource-group entrust-rg \
    --location eastus
```

#### 6. Deploy Backend Container App
```bash
az containerapp create \
    --name entrust-backend \
    --resource-group entrust-rg \
    --environment entrust-env \
    --image enacceleratorsacr.azurecr.io/entrust-backend:latest \
    --registry-server enacceleratorsacr.azurecr.io \
    --target-port 8000 \
    --ingress external \
    --env-vars \
        "DATABASE_URL=postgresql://entrust_admin:Welcome123!@#@entrust-postgres-server.postgres.database.azure.com:5432/entrust_db?sslmode=require" \
        "SECRET_KEY=<generate-secret-key>" \
        "ALGORITHM=HS256" \
        "ACCESS_TOKEN_EXPIRE_MINUTES=1440" \
        "LOG_LEVEL=INFO" \
    --cpu 1.0 \
    --memory 2.0Gi \
    --min-replicas 1 \
    --max-replicas 3
```

#### 7. Get Backend URL and Update Frontend
```bash
BACKEND_URL=$(az containerapp show \
    --name entrust-backend \
    --resource-group entrust-rg \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

# Rebuild frontend with correct backend URL
cd frontend
az acr build \
    --registry enacceleratorsacr \
    --image entrust-frontend:latest \
    --file Dockerfile.prod \
    --build-arg VITE_API_URL=https://$BACKEND_URL \
    .
cd ..
```

#### 8. Deploy Frontend Container App
```bash
az containerapp create \
    --name entrust-frontend \
    --resource-group entrust-rg \
    --environment entrust-env \
    --image enacceleratorsacr.azurecr.io/entrust-frontend:latest \
    --registry-server enacceleratorsacr.azurecr.io \
    --target-port 80 \
    --ingress external \
    --cpu 0.5 \
    --memory 1.0Gi \
    --min-replicas 1 \
    --max-replicas 2
```

## Configuration

### Environment Variables

**Backend:**
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for JWT tokens (generate with: `openssl rand -hex 32`)
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration (default: 1440)
- `LOG_LEVEL`: Logging level (INFO for production)

**Frontend:**
- `VITE_API_URL`: Backend API URL (build-time variable)

## Updating Deployment

To update the application after code changes:

```bash
# Rebuild and push images
cd backend && az acr build --registry enacceleratorsacr --image entrust-backend:latest --file Dockerfile.prod . && cd ..
cd frontend && az acr build --registry enacceleratorsacr --image entrust-frontend:latest --file Dockerfile.prod --build-arg VITE_API_URL=<backend-url> . && cd ..

# Update container apps
az containerapp update --name entrust-backend --resource-group entrust-rg --image enacceleratorsacr.azurecr.io/entrust-backend:latest
az containerapp update --name entrust-frontend --resource-group entrust-rg --image enacceleratorsacr.azurecr.io/entrust-frontend:latest
```

## Access the Application

After deployment, get the URLs:

```bash
# Frontend URL
az containerapp show --name entrust-frontend --resource-group entrust-rg --query "properties.configuration.ingress.fqdn" --output tsv

# Backend URL
az containerapp show --name entrust-backend --resource-group entrust-rg --query "properties.configuration.ingress.fqdn" --output tsv
```

## Default Login Credentials

- **Username**: `admin`
- **Password**: `Welcome123!`

## Troubleshooting

### Check Container Logs
```bash
# Backend logs
az containerapp logs show --name entrust-backend --resource-group entrust-rg --follow

# Frontend logs
az containerapp logs show --name entrust-frontend --resource-group entrust-rg --follow
```

### Check Container Status
```bash
az containerapp list --resource-group entrust-rg --output table
```

### Database Connection Issues
- Ensure PostgreSQL firewall allows Azure services
- Verify DATABASE_URL includes `?sslmode=require`
- Check database credentials

## Cost Considerations

- **Container Apps**: Pay per use (CPU/Memory)
- **PostgreSQL Flexible Server**: Based on SKU (Standard_B1ms ~$15-20/month)
- **Container Registry**: Based on storage and operations
- **Estimated Monthly Cost**: ~$25-35 for basic deployment

