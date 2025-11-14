# Azure Permissions Check Script

This script checks all required Azure permissions for deploying EnTrust.

## How to Use in Azure Cloud Shell

1. **Open Azure Cloud Shell**:
   - Go to https://portal.azure.com
   - Click the Cloud Shell icon (>) in the top menu bar
   - Choose **Bash** when prompted

2. **Copy and Paste the Script**:
   - Copy the entire contents of `check-azure-permissions.sh`
   - Paste it into the Cloud Shell terminal
   - Press Enter to run

   Or upload the file and run:
   ```bash
   # Upload check-azure-permissions.sh file
   # Then run:
   chmod +x check-azure-permissions.sh
   ./check-azure-permissions.sh
   ```

3. **Review the Results**:
   - The script will check 10 different permission areas
   - Green [OK] = Good
   - Yellow [WARNING] = May cause issues, review
   - Red [ERROR] = Must fix before deployment

## What It Checks

1. ✅ Azure CLI installation
2. ✅ Azure login status
3. ✅ Current user information
4. ✅ Subscription-level permissions (Owner/Contributor)
5. ✅ Access to `entrust-rg` resource group
6. ✅ Access to `en_accelerators_db` resource group
7. ✅ Container Registry access (`enacceleratorsacr`)
8. ✅ PostgreSQL Server access (`entrust-postgres-server`)
9. ✅ Container Apps provider registration
10. ✅ Write permissions test

## Expected Output

If everything is correct, you should see:
- All checks showing `[OK]` in green
- Summary showing 0 errors and 0 warnings
- Message: "All checks passed! Ready to deploy."

## Common Issues

### Subscription Not Enabled
- **Fix**: Contact Azure subscription administrator to enable the subscription

### Missing Resource Group Access
- **Fix**: Request Contributor or Owner role on the resource group

### Container Registry Access Denied
- **Fix**: Check firewall rules or request ACR permissions

### PostgreSQL Server Not Accessible
- **Fix**: Verify you have access to `en_accelerators_db` resource group

## Next Steps

After running the script:
1. Fix any errors (red)
2. Review warnings (yellow)
3. Once all checks pass, you can run the deployment script



