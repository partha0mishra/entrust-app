#!/bin/bash

# Simple Azure Permissions Check for EnTrust Deployment
# Run this in Azure Cloud Shell

echo "Checking Azure permissions for EnTrust deployment..."
echo ""

ERRORS=0

# Check login
echo "1. Azure login status..."
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "   ERROR: Not logged in. Run: az login"
    ERRORS=$((ERRORS + 1))
else
    echo "   OK: Logged in"
    SUB_STATE=$(az account show --query state -o tsv)
    if [ "$SUB_STATE" != "Enabled" ]; then
        echo "   ERROR: Subscription is $SUB_STATE (needs to be Enabled)"
        ERRORS=$((ERRORS + 1))
    else
        echo "   OK: Subscription is Enabled"
    fi
fi

# Check resource groups
echo ""
echo "2. Resource group access..."
az group show --name entrust-rg > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "   ERROR: Cannot access entrust-rg"
    ERRORS=$((ERRORS + 1))
else
    echo "   OK: entrust-rg accessible"
fi

az group show --name en_accelerators_db > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "   ERROR: Cannot access en_accelerators_db"
    ERRORS=$((ERRORS + 1))
else
    echo "   OK: en_accelerators_db accessible"
fi

# Check Container Registry
echo ""
echo "3. Container Registry access..."
az acr show --name enacceleratorsacr --resource-group entrust-rg > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "   ERROR: Cannot access Container Registry"
    ERRORS=$((ERRORS + 1))
else
    echo "   OK: Container Registry accessible"
fi

# Check PostgreSQL
echo ""
echo "4. PostgreSQL Server access..."
az postgres flexible-server show --name entrust-postgres-server --resource-group en_accelerators_db > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "   ERROR: Cannot access PostgreSQL Server"
    ERRORS=$((ERRORS + 1))
else
    echo "   OK: PostgreSQL Server accessible"
fi

# Check permissions
echo ""
echo "5. Subscription permissions..."
USER=$(az account show --query user.name -o tsv)
SUB_ID=$(az account show --query id -o tsv)
ROLES=$(az role assignment list --assignee "$USER" --scope "/subscriptions/$SUB_ID" --query "[].roleDefinitionName" -o tsv)
if echo "$ROLES" | grep -q "Owner\|Contributor"; then
    echo "   OK: Has Owner or Contributor role"
else
    echo "   ERROR: Need Owner or Contributor role"
    ERRORS=$((ERRORS + 1))
fi

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "Result: ALL CHECKS PASSED - Ready to deploy!"
    exit 0
else
    echo "Result: $ERRORS ERROR(S) FOUND - Fix before deploying"
    exit 1
fi
