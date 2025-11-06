#!/bin/bash

# Azure Deployment Script for EnTrust
# This script builds and deploys the EnTrust application to Azure

set -e

# Configuration
RESOURCE_GROUP="entrust-rg"
LOCATION="eastus"
ACR_NAME="enacceleratorsacr"
ACR_LOGIN_SERVER="enacceleratorsacr.azurecr.io"
POSTGRES_SERVER="entrust-postgres-server"
POSTGRES_RESOURCE_GROUP="en_accelerators_db"
POSTGRES_ADMIN_USER="entrust_admin"
POSTGRES_ADMIN_PASSWORD="EnTrust@2025Secure!"
POSTGRES_DB_NAME="entrust_db"
CONTAINER_APP_ENV="entrust-env"

echo "=========================================="
echo "EnTrust Azure Deployment Script"
echo "=========================================="

# Step 1: Login to Azure Container Registry
echo "[1/8] Logging into Azure Container Registry..."
az acr login --name $ACR_NAME

# Step 2: Start PostgreSQL Server (if stopped) and get connection details
echo "[2/8] Checking PostgreSQL server status..."
SERVER_STATE=$(az postgres flexible-server show \
    --name $POSTGRES_SERVER \
    --resource-group $POSTGRES_RESOURCE_GROUP \
    --query "state" \
    --output tsv)

if [ "$SERVER_STATE" = "Stopped" ] || [ "$SERVER_STATE" = "Disabled" ]; then
    echo "PostgreSQL server is stopped. Starting server..."
    az postgres flexible-server start \
        --name $POSTGRES_SERVER \
        --resource-group $POSTGRES_RESOURCE_GROUP \
        --output none
    echo "Waiting for server to start..."
    sleep 30
fi

# Get PostgreSQL FQDN
POSTGRES_FQDN=$(az postgres flexible-server show \
    --name $POSTGRES_SERVER \
    --resource-group $POSTGRES_RESOURCE_GROUP \
    --query "fullyQualifiedDomainName" \
    --output tsv)

echo "PostgreSQL FQDN: $POSTGRES_FQDN"
echo "PostgreSQL Admin User: $POSTGRES_ADMIN_USER"

# Step 3: Create database (if not exists)
echo "[3/8] Creating database (if not exists)..."
az postgres flexible-server db create \
    --resource-group $POSTGRES_RESOURCE_GROUP \
    --server-name $POSTGRES_SERVER \
    --database-name $POSTGRES_DB_NAME \
    --output none 2>/dev/null || echo "Database already exists or creation skipped"

# Step 4: Build and push backend image
echo "[4/8] Building and pushing backend image..."
cd backend
az acr build \
    --registry $ACR_NAME \
    --image entrust-backend:latest \
    --file Dockerfile.prod \
    .
cd ..

# Step 5: Build and push frontend image
echo "[5/8] Building and pushing frontend image..."
cd frontend

# Get backend URL (will be set after backend deployment)
BACKEND_URL="https://entrust-backend.azurecontainerapps.io"

az acr build \
    --registry $ACR_NAME \
    --image entrust-frontend:latest \
    --file Dockerfile.prod \
    --build-arg VITE_API_URL=$BACKEND_URL \
    .
cd ..

# Step 6: Create Container Apps Environment
echo "[6/8] Creating Container Apps Environment..."
az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --output none 2>/dev/null || echo "Container Apps Environment already exists"

# Step 7: Deploy backend container app
echo "[7/8] Deploying backend container app..."
# URL encode the password (basic encoding for special characters)
# Using Python for URL encoding (more reliable than jq)
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$POSTGRES_ADMIN_PASSWORD', safe=''))" 2>/dev/null || echo "$POSTGRES_ADMIN_PASSWORD")
DATABASE_URL="postgresql://${POSTGRES_ADMIN_USER}:${ENCODED_PASSWORD}@${POSTGRES_FQDN}:5432/${POSTGRES_DB_NAME}?sslmode=require"

az containerapp create \
    --name entrust-backend \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image "${ACR_LOGIN_SERVER}/entrust-backend:latest" \
    --registry-server $ACR_LOGIN_SERVER \
    --target-port 8000 \
    --ingress external \
    --allow-insecure false \
    --env-vars \
        "DATABASE_URL=$DATABASE_URL" \
        "SECRET_KEY=$(openssl rand -hex 32)" \
        "ALGORITHM=HS256" \
        "ACCESS_TOKEN_EXPIRE_MINUTES=1440" \
        "LOG_LEVEL=INFO" \
    --cpu 1.0 \
    --memory 2.0Gi \
    --min-replicas 1 \
    --max-replicas 3 \
    --output none 2>/dev/null || \
az containerapp update \
    --name entrust-backend \
    --resource-group $RESOURCE_GROUP \
    --image "${ACR_LOGIN_SERVER}/entrust-backend:latest" \
    --output none

# Get backend URL
BACKEND_URL=$(az containerapp show \
    --name entrust-backend \
    --resource-group $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

echo "Backend URL: https://$BACKEND_URL"

# Step 8: Deploy frontend container app
echo "[8/8] Deploying frontend container app..."
# Rebuild frontend with correct backend URL
cd frontend
az acr build \
    --registry $ACR_NAME \
    --image entrust-frontend:latest \
    --file Dockerfile.prod \
    --build-arg VITE_API_URL="https://$BACKEND_URL" \
    .
cd ..

az containerapp create \
    --name entrust-frontend \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image "${ACR_LOGIN_SERVER}/entrust-frontend:latest" \
    --registry-server $ACR_LOGIN_SERVER \
    --target-port 80 \
    --ingress external \
    --allow-insecure false \
    --cpu 0.5 \
    --memory 1.0Gi \
    --min-replicas 1 \
    --max-replicas 2 \
    --output none 2>/dev/null || \
az containerapp update \
    --name entrust-frontend \
    --resource-group $RESOURCE_GROUP \
    --image "${ACR_LOGIN_SERVER}/entrust-frontend:latest" \
    --output none

# Get frontend URL
FRONTEND_URL=$(az containerapp show \
    --name entrust-frontend \
    --resource-group $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Frontend URL: https://$FRONTEND_URL"
echo "Backend URL: https://$BACKEND_URL"
echo ""
echo "Login Credentials:"
echo "  Username: admin"
echo "  Password: Welcome123!"
echo ""
echo "=========================================="

