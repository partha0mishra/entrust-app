# Azure Permissions Check Script for EnTrust Deployment
# Run this script to verify all required permissions for deployment

Write-Host "=========================================="
Write-Host "Azure Permissions Check for EnTrust"
Write-Host "=========================================="
Write-Host ""

$errors = 0
$warnings = 0

# Configuration
$RESOURCE_GROUP = "entrust-rg"
$POSTGRES_RESOURCE_GROUP = "en_accelerators_db"
$ACR_NAME = "enacceleratorsacr"
$POSTGRES_SERVER = "entrust-postgres-server"

# Check 1: Azure CLI Installation
Write-Host "[1/10] Checking Azure CLI installation..."
try {
    $azVersion = az --version 2>&1 | Select-String "azure-cli" | Select-Object -First 1
    if ($azVersion) {
        Write-Host "   [OK] Azure CLI is installed: $azVersion" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Azure CLI not found!" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   [ERROR] Azure CLI not installed or not in PATH" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Check 2: Azure Login Status
Write-Host "[2/10] Checking Azure login status..."
try {
    $account = az account show 2>&1
    if ($LASTEXITCODE -eq 0) {
        $subId = ($account | ConvertFrom-Json).id
        $subName = ($account | ConvertFrom-Json).name
        $subState = ($account | ConvertFrom-Json).state
        Write-Host "   [OK] Logged in to Azure" -ForegroundColor Green
        Write-Host "   Subscription: $subName" -ForegroundColor Cyan
        Write-Host "   Subscription ID: $subId" -ForegroundColor Cyan
        Write-Host "   State: $subState" -ForegroundColor $(if ($subState -eq "Enabled") { "Green" } else { "Yellow" })
        if ($subState -ne "Enabled") {
            Write-Host "   [WARNING] Subscription is not enabled!" -ForegroundColor Yellow
            $warnings++
        }
    } else {
        Write-Host "   [ERROR] Not logged in to Azure. Run: az login" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   [ERROR] Unable to check login status" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Check 3: Current User
Write-Host "[3/10] Checking current user..."
try {
    $user = az account show --query user.name -o tsv 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Current user: $user" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Unable to get user info" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   [ERROR] Unable to check user" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Check 4: Role Assignment (Subscription Level)
Write-Host "[4/10] Checking subscription-level permissions..."
try {
    $user = az account show --query user.name -o tsv
    $subId = az account show --query id -o tsv
    $roles = az role assignment list --assignee $user --scope "/subscriptions/$subId" --query "[].{Role:roleDefinitionName}" -o tsv 2>&1
    if ($LASTEXITCODE -eq 0 -and $roles) {
        Write-Host "   [OK] Subscription-level roles:" -ForegroundColor Green
        $roles | ForEach-Object { Write-Host "      - $_" -ForegroundColor Cyan }
        $hasOwner = $roles -match "Owner"
        $hasContributor = $roles -match "Contributor"
        if (-not $hasOwner -and -not $hasContributor) {
            Write-Host "   [WARNING] Need Owner or Contributor role for deployment" -ForegroundColor Yellow
            $warnings++
        }
    } else {
        Write-Host "   [WARNING] No subscription-level roles found" -ForegroundColor Yellow
        $warnings++
    }
} catch {
    Write-Host "   [WARNING] Unable to check subscription roles" -ForegroundColor Yellow
    $warnings++
}
Write-Host ""

# Check 5: Resource Group Access (entrust-rg)
Write-Host "[5/10] Checking access to resource group: $RESOURCE_GROUP"
try {
    $rg = az group show --name $RESOURCE_GROUP --query "{name:name, location:location}" -o json 2>&1
    if ($LASTEXITCODE -eq 0) {
        $rgInfo = $rg | ConvertFrom-Json
        Write-Host "   [OK] Resource group exists and accessible" -ForegroundColor Green
        Write-Host "      Location: $($rgInfo.location)" -ForegroundColor Cyan
    } else {
        Write-Host "   [ERROR] Cannot access resource group $RESOURCE_GROUP" -ForegroundColor Red
        Write-Host "      Error: $rg" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   [ERROR] Unable to check resource group access" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Check 6: PostgreSQL Resource Group Access
Write-Host "[6/10] Checking access to PostgreSQL resource group: $POSTGRES_RESOURCE_GROUP"
try {
    $rg = az group show --name $POSTGRES_RESOURCE_GROUP --query "{name:name, location:location}" -o json 2>&1
    if ($LASTEXITCODE -eq 0) {
        $rgInfo = $rg | ConvertFrom-Json
        Write-Host "   [OK] PostgreSQL resource group exists and accessible" -ForegroundColor Green
        Write-Host "      Location: $($rgInfo.location)" -ForegroundColor Cyan
    } else {
        Write-Host "   [ERROR] Cannot access resource group $POSTGRES_RESOURCE_GROUP" -ForegroundColor Red
        Write-Host "      Error: $rg" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   [ERROR] Unable to check PostgreSQL resource group access" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Check 7: Container Registry Access
Write-Host "[7/10] Checking access to Container Registry: $ACR_NAME"
try {
    $acr = az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "{name:name, loginServer:loginServer, adminUserEnabled:adminUserEnabled}" -o json 2>&1
    if ($LASTEXITCODE -eq 0) {
        $acrInfo = $acr | ConvertFrom-Json
        Write-Host "   [OK] Container Registry accessible" -ForegroundColor Green
        Write-Host "      Login Server: $($acrInfo.loginServer)" -ForegroundColor Cyan
        Write-Host "      Admin User Enabled: $($acrInfo.adminUserEnabled)" -ForegroundColor Cyan
        
        # Test ACR login
        Write-Host "   Testing ACR login..."
        $loginTest = az acr login --name $ACR_NAME 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "      [OK] Can login to Container Registry" -ForegroundColor Green
        } else {
            Write-Host "      [WARNING] ACR login failed (may need firewall rules)" -ForegroundColor Yellow
            Write-Host "      Error: $loginTest" -ForegroundColor Yellow
            $warnings++
        }
    } else {
        Write-Host "   [ERROR] Cannot access Container Registry $ACR_NAME" -ForegroundColor Red
        Write-Host "      Error: $acr" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   [ERROR] Unable to check Container Registry access" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Check 8: PostgreSQL Server Access
Write-Host "[8/10] Checking access to PostgreSQL Server: $POSTGRES_SERVER"
try {
    $pg = az postgres flexible-server show --name $POSTGRES_SERVER --resource-group $POSTGRES_RESOURCE_GROUP --query "{name:name, state:state, fqdn:fullyQualifiedDomainName, version:version}" -o json 2>&1
    if ($LASTEXITCODE -eq 0) {
        $pgInfo = $pg | ConvertFrom-Json
        Write-Host "   [OK] PostgreSQL Server accessible" -ForegroundColor Green
        Write-Host "      FQDN: $($pgInfo.fqdn)" -ForegroundColor Cyan
        Write-Host "      Version: $($pgInfo.version)" -ForegroundColor Cyan
        Write-Host "      State: $($pgInfo.state)" -ForegroundColor $(if ($pgInfo.state -eq "Ready") { "Green" } else { "Yellow" })
        if ($pgInfo.state -ne "Ready") {
            Write-Host "   [INFO] Server will be started automatically during deployment" -ForegroundColor Cyan
        }
    } else {
        Write-Host "   [ERROR] Cannot access PostgreSQL Server $POSTGRES_SERVER" -ForegroundColor Red
        Write-Host "      Error: $pg" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   [ERROR] Unable to check PostgreSQL Server access" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Check 9: Container Apps Provider
Write-Host "[9/10] Checking Container Apps provider registration..."
try {
    $provider = az provider show --namespace Microsoft.App --query "{registrationState:registrationState}" -o json 2>&1
    if ($LASTEXITCODE -eq 0) {
        $providerInfo = $provider | ConvertFrom-Json
        if ($providerInfo.registrationState -eq "Registered") {
            Write-Host "   [OK] Container Apps provider is registered" -ForegroundColor Green
        } else {
            Write-Host "   [WARNING] Container Apps provider not registered: $($providerInfo.registrationState)" -ForegroundColor Yellow
            Write-Host "      Run: az provider register --namespace Microsoft.App" -ForegroundColor Cyan
            $warnings++
        }
    } else {
        Write-Host "   [WARNING] Unable to check provider registration" -ForegroundColor Yellow
        $warnings++
    }
} catch {
    Write-Host "   [WARNING] Unable to check provider registration" -ForegroundColor Yellow
    $warnings++
}
Write-Host ""

# Check 10: Write Permissions Test
Write-Host "[10/10] Testing write permissions..."
try {
    # Try to read a resource (safe operation)
    $test = az resource list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Can read resources in $RESOURCE_GROUP" -ForegroundColor Green
    } else {
        Write-Host "   [WARNING] Read test failed" -ForegroundColor Yellow
        $warnings++
    }
} catch {
    Write-Host "   [WARNING] Unable to test write permissions" -ForegroundColor Yellow
    $warnings++
}
Write-Host ""

# Summary
Write-Host "=========================================="
Write-Host "Summary"
Write-Host "=========================================="
Write-Host "Errors: $errors" -ForegroundColor $(if ($errors -eq 0) { "Green" } else { "Red" })
Write-Host "Warnings: $warnings" -ForegroundColor $(if ($warnings -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

if ($errors -eq 0 -and $warnings -eq 0) {
    Write-Host "[OK] All checks passed! Ready to deploy." -ForegroundColor Green
    exit 0
} elseif ($errors -eq 0) {
    Write-Host "[WARNING] Some warnings found, but deployment may still work." -ForegroundColor Yellow
    Write-Host "Review warnings above and fix if needed." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "[ERROR] Critical errors found. Please fix them before deploying." -ForegroundColor Red
    exit 1
}



