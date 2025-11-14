# Script to rebuild frontend with HTTPS backend URL
# Run: az login first if you get authorization errors

$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "Fixing Frontend HTTPS Backend URL"
Write-Host "=========================================="

# Configuration
$RESOURCE_GROUP = "entrust"
$ACR_NAME = "entrustregistry"
$BACKEND_URL = "https://entrust-backend.calmbay-c64e42cc.eastus.azurecontainerapps.io"

Write-Host "[1/3] Rebuilding frontend with HTTPS backend URL..."
Write-Host "Backend URL: $BACKEND_URL"

Push-Location frontend
az acr build `
    --registry $ACR_NAME `
    --image entrust-frontend:latest `
    --file Dockerfile.prod `
    --build-arg "VITE_API_URL=$BACKEND_URL" `
    .
Pop-Location

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed. Please check Azure authentication: az login"
    exit 1
}

Write-Host "[2/3] Updating frontend container app..."
az containerapp update `
    --name entrust-frontend `
    --resource-group $RESOURCE_GROUP `
    --image "${ACR_NAME}.azurecr.io/entrust-frontend:latest" `
    --output none

Write-Host "[3/3] Waiting for deployment to complete..."
Start-Sleep -Seconds 20

Write-Host ""
Write-Host "=========================================="
Write-Host "✓ Frontend updated successfully!"
Write-Host "=========================================="
Write-Host "Frontend URL: https://entrust-frontend.calmbay-c64e42cc.eastus.azurecontainerapps.io"
Write-Host ""
Write-Host "Note: Use password 'Welcome123!' for admin login"
Write-Host "     (Password will be 'admin123' after next backend restart)"

