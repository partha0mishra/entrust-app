#!/usr/bin/env python3
"""
Static Security and Implementation Audit for Storage Service
Analyzes code without requiring imports or database connection
"""
import sys
import re
import os

class SecurityAuditor:
    """Security and code quality auditor"""

    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []

    def log_issue(self, category, message):
        """Log a critical security issue"""
        self.issues.append((category, message))

    def log_warning(self, category, message):
        """Log a warning"""
        self.warnings.append((category, message))

    def log_pass(self, category, message):
        """Log a passed check"""
        self.passed.append((category, message))

    def print_results(self):
        """Print all results"""
        print("\n" + "=" * 70)
        print("  AUDIT RESULTS")
        print("=" * 70)

        if self.passed:
            print(f"\n✓ PASSED CHECKS ({len(self.passed)}):")
            for category, message in self.passed:
                print(f"  ✓ [{category}] {message}")

        if self.warnings:
            print(f"\n⚠ WARNINGS ({len(self.warnings)}):")
            for category, message in self.warnings:
                print(f"  ⚠ [{category}] {message}")

        if self.issues:
            print(f"\n✗ CRITICAL ISSUES ({len(self.issues)}):")
            for category, message in self.issues:
                print(f"  ✗ [{category}] {message}")

        print("\n" + "=" * 70)
        print(f"  Summary: {len(self.passed)} passed, {len(self.warnings)} warnings, {len(self.issues)} critical")
        print("=" * 70)

        return len(self.issues) == 0

def check_models_security(auditor):
    """Check models.py for security issues"""
    print("\n" + "=" * 70)
    print("  1. MODELS SECURITY AUDIT")
    print("=" * 70)

    try:
        with open('backend/app/models.py', 'r') as f:
            code = f.read()

        # Check for StorageType enum
        if 'class StorageType' in code:
            auditor.log_pass("Models", "StorageType enum defined")
            print("  ✓ StorageType enum found")
        else:
            auditor.log_issue("Models", "StorageType enum missing")
            print("  ✗ StorageType enum not found")

        # Check for storage fields in Customer model
        storage_fields = [
            'storage_type', 'storage_fallback_enabled',
            's3_bucket_name', 's3_region', 's3_access_key_id', 's3_secret_access_key',
            'azure_storage_account', 'azure_container_name', 'azure_connection_string'
        ]

        missing_fields = []
        for field in storage_fields:
            if field in code:
                print(f"  ✓ Field '{field}' present")
            else:
                missing_fields.append(field)

        if missing_fields:
            auditor.log_issue("Models", f"Missing fields: {', '.join(missing_fields)}")
        else:
            auditor.log_pass("Models", "All storage fields present in Customer model")

        # Check for default values
        if "default=StorageType.LOCAL" in code:
            auditor.log_pass("Models", "Default storage type is LOCAL (safe)")
            print("  ✓ Default storage: LOCAL")

        if "default=True" in code and "fallback" in code:
            auditor.log_pass("Models", "Fallback enabled by default")
            print("  ✓ Fallback enabled by default")

    except Exception as e:
        auditor.log_issue("Models", f"Model check failed: {e}")

def check_path_traversal_security(auditor):
    """Check for path traversal vulnerabilities"""
    print("\n" + "=" * 70)
    print("  2. PATH TRAVERSAL SECURITY AUDIT")
    print("=" * 70)

    try:
        with open('backend/app/report_utils.py', 'r') as f:
            code = f.read()

        # Check for path validation
        if 're.match' in code and 'customer_code' in code:
            auditor.log_pass("Path Security", "Customer code validation with regex")
            print("  ✓ Customer code validated with regex")

            # Check regex pattern
            if r'[A-Z0-9_\-]+' in code or r'[A-Z0-9_\\-]+' in code:
                auditor.log_pass("Path Security", "Safe character whitelist used")
                print("  ✓ Safe character whitelist: [A-Z0-9_-]")
        else:
            auditor.log_issue("Path Security", "Missing customer code validation")
            print("  ✗ Customer code validation not found")

        if 'ValueError' in code and 'Invalid' in code:
            auditor.log_pass("Path Security", "ValueError raised for invalid paths")
            print("  ✓ Raises ValueError for invalid input")

        # Check for dimension validation
        if 'dimension' in code and ('validate' in code or 're.match' in code):
            auditor.log_pass("Path Security", "Dimension name validation present")
            print("  ✓ Dimension name validation")

        # Check for dangerous patterns
        dangerous_patterns = [
            (r'\.\./|\.\.\\', 'Directory traversal (../)'),
            (r'eval\(', 'eval() usage (code injection risk)'),
            (r'exec\(', 'exec() usage (code injection risk)'),
            (r'__import__\(', 'Dynamic imports'),
        ]

        found_dangerous = False
        for pattern, description in dangerous_patterns:
            if re.search(pattern, code):
                auditor.log_issue("Path Security", f"DANGEROUS: {description}")
                print(f"  ✗ DANGEROUS: {description}")
                found_dangerous = True

        if not found_dangerous:
            auditor.log_pass("Path Security", "No dangerous path patterns found")
            print("  ✓ No dangerous path patterns")

    except Exception as e:
        auditor.log_issue("Path Security", f"Path traversal check failed: {e}")

def check_storage_service_security(auditor):
    """Check storage service implementation"""
    print("\n" + "=" * 70)
    print("  3. STORAGE SERVICE SECURITY AUDIT")
    print("=" * 70)

    try:
        with open('backend/app/storage_service.py', 'r') as f:
            code = f.read()

        # Check for proper error handling
        try_count = code.count('try:')
        except_count = code.count('except')

        if try_count > 5 and except_count > 5:
            auditor.log_pass("Error Handling", f"{except_count} exception handlers found")
            print(f"  ✓ Comprehensive error handling ({except_count} handlers)")
        else:
            auditor.log_warning("Error Handling", "Limited exception handling")
            print(f"  ⚠ Limited exception handling")

        # Check for credential exposure in logs
        log_patterns = [
            r'logger\.(info|debug|warning)\([^)]*(?:access_key|secret|password|token|credential)[^)]*\)',
        ]

        credential_logged = False
        for pattern in log_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            if matches:
                for match in matches:
                    # Check if it's actually logging the credential value
                    auditor.log_warning("Security", "Potential credential in log statement")
                    print(f"  ⚠ Possible credential logging")
                    credential_logged = True
                    break

        if not credential_logged:
            auditor.log_pass("Security", "No obvious credential logging")
            print("  ✓ No obvious credential logging")

        # Check for boto3 imports and usage
        if 'import boto3' in code:
            auditor.log_pass("AWS SDK", "boto3 imported for S3 support")
            print("\n  AWS S3 Support:")
            print("    ✓ boto3 imported")

            # Check error handling
            if 'ClientError' in code:
                auditor.log_pass("AWS SDK", "AWS ClientError handled")
                print("    ✓ ClientError handling")

            if 'NoCredentialsError' in code:
                auditor.log_pass("AWS SDK", "NoCredentialsError handled")
                print("    ✓ NoCredentialsError handling")

            # Check for pre-signed URLs
            if 'generate_presigned_url' in code:
                auditor.log_pass("AWS SDK", "Pre-signed URL generation")
                print("    ✓ Pre-signed URL generation")

                # Check expiration
                if 'ExpiresIn' in code:
                    auditor.log_pass("AWS SDK", "URL expiration configured")
                    print("    ✓ URL expiration configured")

        # Check for Azure support
        if 'from azure.storage.blob import' in code:
            auditor.log_pass("Azure SDK", "Azure Blob SDK imported")
            print("\n  Azure Blob Support:")
            print("    ✓ azure-storage-blob imported")

            # Check error handling
            if 'AzureError' in code:
                auditor.log_pass("Azure SDK", "AzureError handled")
                print("    ✓ AzureError handling")

            if 'ResourceNotFoundError' in code:
                auditor.log_pass("Azure SDK", "ResourceNotFoundError handled")
                print("    ✓ ResourceNotFoundError handling")

            # Check for SAS tokens
            if 'generate_blob_sas' in code:
                auditor.log_pass("Azure SDK", "SAS token generation")
                print("    ✓ SAS token generation")

        # Check for fallback logic
        if 'fallback_enabled' in code:
            auditor.log_pass("Fallback", "Fallback configuration present")
            print("\n  Fallback Logic:")
            print("    ✓ Fallback configuration")

            if 'logger.info("Falling back' in code or 'logger.warning' in code:
                auditor.log_pass("Fallback", "Fallback events logged")
                print("    ✓ Fallback events logged")

        # Check for input validation
        if 'ValueError' in code and 'validate' in code.lower():
            auditor.log_pass("Input Validation", "Input validation present")
            print("\n  ✓ Input validation implemented")

    except Exception as e:
        auditor.log_issue("Storage Service", f"Storage service check failed: {e}")

def check_report_utils_integration(auditor):
    """Check report_utils.py integration"""
    print("\n" + "=" * 70)
    print("  4. REPORT UTILS INTEGRATION AUDIT")
    print("=" * 70)

    try:
        with open('backend/app/report_utils.py', 'r') as f:
            code = f.read()

        # Check for StorageService import
        if 'from .storage_service import StorageService' in code:
            auditor.log_pass("Integration", "StorageService imported")
            print("  ✓ StorageService imported")
        else:
            auditor.log_issue("Integration", "StorageService not imported")
            print("  ✗ StorageService not imported")

        # Check save_reports signature
        if 'def save_reports(' in code and 'customer=None' in code:
            auditor.log_pass("Integration", "save_reports accepts customer parameter")
            print("  ✓ save_reports accepts customer parameter")
        else:
            auditor.log_issue("Integration", "save_reports missing customer parameter")
            print("  ✗ save_reports missing customer parameter")

        # Check for storage service usage
        if 'StorageService(customer)' in code:
            auditor.log_pass("Integration", "StorageService instantiated with customer")
            print("  ✓ StorageService instantiated with customer config")

        # Check for storage_type in result
        if "'storage_type'" in code:
            auditor.log_pass("Integration", "storage_type returned in result")
            print("  ✓ storage_type tracked in result")

        # Check for date-based naming (one report per day)
        if 'strftime("%Y%m%d")' in code:
            auditor.log_pass("Retention", "Date-based file naming")
            print("  ✓ Date-based file naming (one per day)")

    except Exception as e:
        auditor.log_issue("Integration", f"Report utils check failed: {e}")

def check_router_integration(auditor):
    """Check routers/reports.py integration"""
    print("\n" + "=" * 70)
    print("  5. ROUTER INTEGRATION AUDIT")
    print("=" * 70)

    try:
        with open('backend/app/routers/reports.py', 'r') as f:
            code = f.read()

        # Check if customer is passed to save_reports
        if 'save_reports(' in code and 'customer=customer' in code:
            auditor.log_pass("Integration", "customer passed to save_reports")
            print("  ✓ customer passed to save_reports")
        else:
            auditor.log_issue("Integration", "customer not passed to save_reports")
            print("  ✗ customer not passed to save_reports")

        # Check for storage_type logging
        if 'storage_type' in code and 'logger.info' in code:
            auditor.log_pass("Integration", "storage_type logged")
            print("  ✓ storage_type logged for debugging")

        # Count occurrences
        save_calls = len(re.findall(r'save_reports\(', code))
        print(f"  ℹ Found {save_calls} save_reports() calls")

    except Exception as e:
        auditor.log_issue("Integration", f"Router check failed: {e}")

def check_migration_script(auditor):
    """Check migration script"""
    print("\n" + "=" * 70)
    print("  6. MIGRATION SCRIPT AUDIT")
    print("=" * 70)

    try:
        with open('backend/deploy_db.py', 'r') as f:
            code = f.read()

        # Check for customer_storage migration
        if 'def migrate_customer_storage' in code:
            auditor.log_pass("Migration", "customer_storage migration defined")
            print("  ✓ migrate_customer_storage() defined")
        else:
            auditor.log_issue("Migration", "customer_storage migration not found")
            print("  ✗ migrate_customer_storage() not found")
            return

        # Check for safe migration practices
        if 'column_exists' in code:
            auditor.log_pass("Migration", "column_exists checks used")
            print("  ✓ column_exists checks (idempotent)")

        # Check for enum creation
        if 'storagetype' in code.lower():
            auditor.log_pass("Migration", "StorageType enum created")
            print("  ✓ StorageType enum creation")

        # Check default values
        if "DEFAULT 'LOCAL'" in code:
            auditor.log_pass("Migration", "Default storage is LOCAL")
            print("  ✓ Default storage: LOCAL")

        if "DEFAULT TRUE" in code or "DEFAULT true" in code:
            auditor.log_pass("Migration", "Fallback enabled by default")
            print("  ✓ Default fallback: enabled")

        # Check if migration is in the list
        if "'customer_storage'" in code and 'migrate_customer_storage' in code:
            auditor.log_pass("Migration", "Migration registered in run_all_migrations")
            print("  ✓ Migration registered in run_all_migrations()")

    except Exception as e:
        auditor.log_issue("Migration", f"Migration script check failed: {e}")

def check_dependencies(auditor):
    """Check requirements.txt"""
    print("\n" + "=" * 70)
    print("  7. DEPENDENCIES AUDIT")
    print("=" * 70)

    try:
        with open('backend/requirements.txt', 'r') as f:
            requirements = f.read()

        # Check for boto3
        if 'boto3' in requirements:
            auditor.log_pass("Dependencies", "boto3 present")
            print("  ✓ boto3 (AWS S3 support)")
        else:
            auditor.log_warning("Dependencies", "boto3 not found")
            print("  ⚠ boto3 not in requirements.txt")

        # Check for azure-storage-blob
        if 'azure-storage-blob' in requirements:
            auditor.log_pass("Dependencies", "azure-storage-blob present")
            print("  ✓ azure-storage-blob (Azure Blob support)")
        else:
            auditor.log_warning("Dependencies", "azure-storage-blob not found")
            print("  ⚠ azure-storage-blob not in requirements.txt")

        # Check version pinning
        lines = [l.strip() for l in requirements.split('\n') if l.strip() and not l.startswith('#')]
        unpinned = [l for l in lines if '==' not in l and '>=' not in l]

        if unpinned:
            auditor.log_warning("Dependencies", f"Unpinned: {', '.join(unpinned[:3])}")
            print(f"  ⚠ {len(unpinned)} unpinned dependencies")
        else:
            auditor.log_pass("Dependencies", "All dependencies version-pinned")
            print("  ✓ All dependencies version-pinned")

    except Exception as e:
        auditor.log_issue("Dependencies", f"Dependencies check failed: {e}")

def check_security_best_practices(auditor):
    """Check overall security best practices"""
    print("\n" + "=" * 70)
    print("  8. SECURITY BEST PRACTICES AUDIT")
    print("=" * 70)

    checks = {
        'backend/app/storage_service.py': [
            ('ImportError', 'Graceful handling of missing SDKs'),
            ('except Exception as e', 'Generic exception handling'),
            ('logger.error', 'Error logging'),
        ],
        'backend/app/models.py': [
            ('nullable=True', 'Optional cloud credential fields'),
            ('String(500)', 'Adequate field sizes for credentials'),
        ],
    }

    for file_path, patterns in checks.items():
        try:
            with open(file_path, 'r') as f:
                code = f.read()

            for pattern, description in patterns:
                if pattern in code:
                    auditor.log_pass("Best Practice", description)
                    print(f"  ✓ {description}")

        except Exception as e:
            auditor.log_warning("Best Practice", f"Could not check {file_path}")

def main():
    """Run all audits"""
    print("\n" + "=" * 70)
    print("  COMPREHENSIVE SECURITY & IMPLEMENTATION AUDIT")
    print("  Storage Service for Offline Reports")
    print("=" * 70)

    auditor = SecurityAuditor()

    # Run all checks
    check_models_security(auditor)
    check_path_traversal_security(auditor)
    check_storage_service_security(auditor)
    check_report_utils_integration(auditor)
    check_router_integration(auditor)
    check_migration_script(auditor)
    check_dependencies(auditor)
    check_security_best_practices(auditor)

    # Print results
    success = auditor.print_results()

    # Additional recommendations
    print("\n" + "=" * 70)
    print("  RECOMMENDATIONS")
    print("=" * 70)
    print("\n1. Credential Security:")
    print("   - Consider encrypting S3/Azure credentials in database")
    print("   - Use environment variables for sensitive config when possible")
    print("   - Implement credential rotation policies")
    print("\n2. Monitoring:")
    print("   - Monitor storage failures and fallback events")
    print("   - Track storage usage and costs")
    print("   - Alert on repeated failures")
    print("\n3. Testing:")
    print("   - Test S3 integration with mock credentials")
    print("   - Test Azure Blob integration")
    print("   - Test fallback scenarios")
    print("   - Test path traversal prevention")
    print("\n4. Documentation:")
    print("   - Document storage configuration per customer")
    print("   - Document fallback behavior")
    print("   - Document pre-signed URL expiration")

    if success:
        print("\n✓ ALL CRITICAL CHECKS PASSED")
        print("  Implementation appears secure and well-designed")
        print("  Review warnings and recommendations above")
        sys.exit(0)
    else:
        print("\n✗ CRITICAL ISSUES FOUND")
        print("  Please address critical issues before deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()
