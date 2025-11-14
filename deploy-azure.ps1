# Azure Deployment Script for EnTrust (PowerShell)
# This script builds and deploys the EnTrust application to Azure

$ErrorActionPreference = "Stop"

# Configuration
$RESOURCE_GROUP = "entrust"
$LOCATION = "eastus"
$ACR_NAME = "entrustregistry"
$ACR_LOGIN_SERVER = "entrustregistry.azurecr.io"
$POSTGRES_SERVER = "entrust-postgres"
$POSTGRES_RESOURCE_GROUP = "entrust"
$POSTGRES_ADMIN_USER = "entrust_admin"
# Password will be generated or retrieved from Key Vault in production
$POSTGRES_ADMIN_PASSWORD = "VChmn9fjsWk7u36XG8gz!@#"
$POSTGRES_DB_NAME = "entrust_db"
$CONTAINER_APP_ENV = "entrust-env"

Write-Host "=========================================="
Write-Host "EnTrust Azure Deployment Script"
Write-Host "=========================================="

# Step 1: Login to Azure Container Registry
Write-Host "[1/9] Logging into Azure Container Registry..."
az acr login --name $ACR_NAME

# Step 2: Check if PostgreSQL server exists, create if not
Write-Host "[2/9] Checking PostgreSQL server..."
$postgresExists = $null
try {
    $postgresExists = az postgres flexible-server show `
        --name $POSTGRES_SERVER `
        --resource-group $POSTGRES_RESOURCE_GROUP `
        --query "name" `
        --output tsv 2>&1
    if ($LASTEXITCODE -ne 0) {
        $postgresExists = $null
    }
} catch {
    $postgresExists = $null
}

if (-not $postgresExists) {
    Write-Host "PostgreSQL server does not exist. Creating..."
    if (-not $POSTGRES_ADMIN_PASSWORD) {
        # Generate secure password
        $POSTGRES_ADMIN_PASSWORD = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 20 | ForEach-Object {[char]$_}) + "!@#"
        Write-Host "Generated PostgreSQL password (save this securely!)"
    }
    
    # Try multiple regions - PostgreSQL Flexible Server availability varies by subscription
    $regions = @("centralus", "southcentralus", "northeurope", "westeurope", "uksouth", "eastasia")
    $postgresLocation = $null
    
    foreach ($region in $regions) {
        Write-Host "Trying to create PostgreSQL in $region..."
        az postgres flexible-server create `
            --resource-group $POSTGRES_RESOURCE_GROUP `
            --name $POSTGRES_SERVER `
            --location $region `
            --admin-user $POSTGRES_ADMIN_USER `
            --admin-password $POSTGRES_ADMIN_PASSWORD `
            --sku-name Standard_B2s `
            --tier Burstable `
            --version 15 `
            --storage-size 32 `
            --public-access 0.0.0.0 `
            --output none 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $postgresLocation = $region
            Write-Host "Successfully created PostgreSQL in $region"
            break
        } else {
            Write-Host "Failed to create in $region, trying next region..."
        }
    }
    
    if (-not $postgresLocation) {
        Write-Host "ERROR: Could not create PostgreSQL server in any available region."
        Write-Host "Please create PostgreSQL manually or use an existing server."
        exit 1
    }
    
    Write-Host "PostgreSQL server created. Waiting for provisioning..."
    Start-Sleep -Seconds 60
} else {
    Write-Host "PostgreSQL server exists. Checking status..."
    $serverState = az postgres flexible-server show `
        --name $POSTGRES_SERVER `
        --resource-group $POSTGRES_RESOURCE_GROUP `
        --query "state" `
        --output tsv
    
    if ($serverState -eq "Stopped" -or $serverState -eq "Disabled") {
        Write-Host "PostgreSQL server is stopped. Starting server..."
        az postgres flexible-server start `
            --name $POSTGRES_SERVER `
            --resource-group $POSTGRES_RESOURCE_GROUP `
            --output none
        Write-Host "Waiting for server to start..."
        Start-Sleep -Seconds 30
    }
    
    # Retrieve password from Azure Key Vault if available, or prompt
    if (-not $POSTGRES_ADMIN_PASSWORD) {
        Write-Host "WARNING: PostgreSQL password not set. Please provide it or retrieve from Key Vault."
        Write-Host "For now, using placeholder. Update DATABASE_URL manually after deployment."
        $POSTGRES_ADMIN_PASSWORD = "CHANGE_ME"
    }
}

# Get PostgreSQL FQDN
$POSTGRES_FQDN = az postgres flexible-server show `
    --name $POSTGRES_SERVER `
    --resource-group $POSTGRES_RESOURCE_GROUP `
    --query "fullyQualifiedDomainName" `
    --output tsv

Write-Host "PostgreSQL FQDN: $POSTGRES_FQDN"
Write-Host "PostgreSQL Admin User: $POSTGRES_ADMIN_USER"

# Step 3: Create database (if not exists)
Write-Host "[3/9] Creating database (if not exists)..."
az postgres flexible-server db create `
    --resource-group $POSTGRES_RESOURCE_GROUP `
    --server-name $POSTGRES_SERVER `
    --database-name $POSTGRES_DB_NAME `
    --output none 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Database already exists or creation skipped"
}

# Step 4: Build and push backend image
Write-Host "[4/9] Building and pushing backend image..."
Push-Location backend
az acr build `
    --registry $ACR_NAME `
    --image entrust-backend:latest `
    --file Dockerfile.prod `
    .
Pop-Location

# Step 5: Build and push frontend image (temporary with placeholder)
Write-Host "[5/9] Building and pushing frontend image (initial build)..."
$BACKEND_URL = "https://entrust-backend.azurecontainerapps.io"
Push-Location frontend
az acr build `
    --registry $ACR_NAME `
    --image entrust-frontend:latest `
    --file Dockerfile.prod `
    --build-arg "VITE_API_URL=$BACKEND_URL" `
    .
Pop-Location

# Step 6: Create Container Apps Environment
Write-Host "[6/9] Creating Container Apps Environment..."
az containerapp env create `
    --name $CONTAINER_APP_ENV `
    --resource-group $RESOURCE_GROUP `
    --location $LOCATION `
    --output none 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Container Apps Environment already exists"
}

# Step 7: Deploy backend container app
Write-Host "[7/9] Deploying backend container app..."
# Note: URL encode special characters in password (@ becomes %40, ! becomes %21, etc.)
$encodedPassword = $POSTGRES_ADMIN_PASSWORD -replace '@', '%40' -replace '!', '%21' -replace '#', '%23' -replace ' ', '%20' -replace '\$', '%24'
$DATABASE_URL = "postgresql://${POSTGRES_ADMIN_USER}:${encodedPassword}@${POSTGRES_FQDN}:5432/${POSTGRES_DB_NAME}?sslmode=require"
$SECRET_KEY = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Get frontend URL placeholder (will update after frontend is created)
$FRONTEND_URL_PLACEHOLDER = "https://entrust-frontend.azurecontainerapps.io"

az containerapp create `
    --name entrust-backend `
    --resource-group $RESOURCE_GROUP `
    --environment $CONTAINER_APP_ENV `
    --image "${ACR_LOGIN_SERVER}/entrust-backend:latest" `
    --registry-server $ACR_LOGIN_SERVER `
    --target-port 8000 `
    --ingress external `
    --allow-insecure false `
    --env-vars "DATABASE_URL=$DATABASE_URL" "SECRET_KEY=$SECRET_KEY" "ALGORITHM=HS256" "ACCESS_TOKEN_EXPIRE_MINUTES=1440" "LOG_LEVEL=INFO" "ALLOWED_ORIGINS=http://localhost:3000,$FRONTEND_URL_PLACEHOLDER" `
    --cpu 1.0 `
    --memory 2.0Gi `
    --min-replicas 1 `
    --max-replicas 3 `
    --output none 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Updating existing backend container app..."
    az containerapp update `
        --name entrust-backend `
        --resource-group $RESOURCE_GROUP `
        --image "${ACR_LOGIN_SERVER}/entrust-backend:latest" `
        --output none
}

# Get backend URL
$BACKEND_URL = az containerapp show `
    --name entrust-backend `
    --resource-group $RESOURCE_GROUP `
    --query "properties.configuration.ingress.fqdn" `
    --output tsv

Write-Host "Backend URL: https://$BACKEND_URL"

# Step 8: Rebuild frontend with correct backend URL and deploy
Write-Host "[8/9] Rebuilding frontend with backend URL and deploying..."
Push-Location frontend
az acr build `
    --registry $ACR_NAME `
    --image entrust-frontend:latest `
    --file Dockerfile.prod `
    --build-arg "VITE_API_URL=https://$BACKEND_URL" `
    .
Pop-Location

az containerapp create `
    --name entrust-frontend `
    --resource-group $RESOURCE_GROUP `
    --environment $CONTAINER_APP_ENV `
    --image "${ACR_LOGIN_SERVER}/entrust-frontend:latest" `
    --registry-server $ACR_LOGIN_SERVER `
    --target-port 80 `
    --ingress external `
    --allow-insecure false `
    --cpu 0.5 `
    --memory 1.0Gi `
    --min-replicas 1 `
    --max-replicas 2 `
    --output none 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Updating existing frontend container app..."
    az containerapp update `
        --name entrust-frontend `
        --resource-group $RESOURCE_GROUP `
        --image "${ACR_LOGIN_SERVER}/entrust-frontend:latest" `
        --output none
}

# Get frontend URL
$FRONTEND_URL = az containerapp show `
    --name entrust-frontend `
    --resource-group $RESOURCE_GROUP `
    --query "properties.configuration.ingress.fqdn" `
    --output tsv

# Update backend CORS with actual frontend URL
Write-Host "Updating backend CORS settings with frontend URL..."
az containerapp update `
    --name entrust-backend `
    --resource-group $RESOURCE_GROUP `
    --set-env-vars "ALLOWED_ORIGINS=http://localhost:3000,https://$FRONTEND_URL" `
    --output none

Write-Host ""
Write-Host "=========================================="
Write-Host "Deployment Complete!"
Write-Host "=========================================="
Write-Host "Frontend URL: https://$FRONTEND_URL"
Write-Host "Backend URL: https://$BACKEND_URL"
Write-Host ""
Write-Host "Login Credentials:"
Write-Host "  Username: admin"
Write-Host "  Password: Welcome123!"
Write-Host ""
Write-Host "=========================================="

