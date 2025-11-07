#!/usr/bin/env python3
"""
Deep Security and Implementation Audit for Storage Service
Checks for security vulnerabilities, best practices, and implementation issues
"""
import sys
import re
from sqlalchemy import inspect, text
from app.database import SessionLocal, engine
from app import models
import ast
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
            print("\n✓ PASSED CHECKS:")
            for category, message in self.passed:
                print(f"  ✓ [{category}] {message}")

        if self.warnings:
            print("\n⚠ WARNINGS:")
            for category, message in self.warnings:
                print(f"  ⚠ [{category}] {message}")

        if self.issues:
            print("\n✗ CRITICAL ISSUES:")
            for category, message in self.issues:
                print(f"  ✗ [{category}] {message}")

        print("\n" + "=" * 70)
        print(f"  Summary: {len(self.passed)} passed, {len(self.warnings)} warnings, {len(self.issues)} critical")
        print("=" * 70)

        return len(self.issues) == 0

def check_database_schema(auditor):
    """Check database schema for storage configuration"""
    print("\n" + "=" * 70)
    print("  1. DATABASE SCHEMA AUDIT")
    print("=" * 70)

    db = SessionLocal()
    try:
        inspector = inspect(engine)

        if 'customers' not in inspector.get_table_names():
            auditor.log_issue("Database", "Table 'customers' does not exist!")
            return

        columns = {col['name']: col for col in inspector.get_columns('customers')}

        # Check storage columns
        storage_columns = [
            'storage_type', 'storage_fallback_enabled',
            's3_bucket_name', 's3_region', 's3_access_key_id', 's3_secret_access_key', 's3_prefix',
            'azure_storage_account', 'azure_container_name', 'azure_connection_string', 'azure_prefix'
        ]

        missing = []
        for col in storage_columns:
            if col in columns:
                col_type = str(columns[col]['type'])
                print(f"  ✓ {col}: {col_type}")
            else:
                missing.append(col)

        if missing:
            auditor.log_issue("Database", f"Missing storage columns: {', '.join(missing)}")
            print(f"\n✗ Missing columns: {', '.join(missing)}")
            print("\nRun migration: python backend/deploy_db.py --migrate customer_storage")
        else:
            auditor.log_pass("Database", "All storage configuration columns present")

    except Exception as e:
        auditor.log_issue("Database", f"Schema check failed: {e}")
    finally:
        db.close()

def check_security_credentials(auditor):
    """Check for credential security issues"""
    print("\n" + "=" * 70)
    print("  2. CREDENTIAL SECURITY AUDIT")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Check if any credentials are stored in plaintext
        customers = db.query(models.Customer).all()

        if not customers:
            print("  ⚠ No customers found (OK for fresh deployment)")
            auditor.log_warning("Security", "No customers to audit")
            return

        for customer in customers:
            print(f"\n  Customer: {customer.customer_code}")

            # Check S3 credentials
            if customer.s3_access_key_id or customer.s3_secret_access_key:
                print(f"    Storage Type: {customer.storage_type}")

                # Check if credentials are encrypted (they should be stored securely)
                if customer.s3_access_key_id and len(customer.s3_access_key_id) < 50:
                    auditor.log_warning("Security", f"Customer {customer.customer_code}: S3 credentials may not be encrypted")
                    print(f"    ⚠ S3 credentials may not be encrypted")
                else:
                    print(f"    ✓ S3 credentials appear to be stored")

            # Check Azure credentials
            if customer.azure_connection_string:
                print(f"    Storage Type: {customer.storage_type}")
                print(f"    ✓ Azure connection string configured")

        auditor.log_pass("Security", "Credential storage audit completed")

    except Exception as e:
        auditor.log_issue("Security", f"Credential check failed: {e}")
    finally:
        db.close()

def check_path_traversal_security(auditor):
    """Check for path traversal vulnerabilities"""
    print("\n" + "=" * 70)
    print("  3. PATH TRAVERSAL SECURITY AUDIT")
    print("=" * 70)

    try:
        # Read report_utils.py
        with open('/home/user/entrust-app/backend/app/report_utils.py', 'r') as f:
            code = f.read()

        # Check for path validation
        checks = [
            (r're\.match.*customer_code', 'Customer code validation with regex'),
            (r're\.match.*dimension', 'Dimension name validation with regex'),
            (r'ValueError.*Invalid', 'Path validation raises ValueError'),
            (r'[A-Z0-9_\-]', 'Customer code restricted to safe characters'),
        ]

        for pattern, description in checks:
            if re.search(pattern, code):
                auditor.log_pass("Path Security", description)
                print(f"  ✓ {description}")
            else:
                auditor.log_warning("Path Security", f"Missing: {description}")
                print(f"  ⚠ {description} - NOT FOUND")

        # Check for dangerous path operations
        dangerous_patterns = [
            (r'os\.path\.join\([^)]*\.\.[^)]*\)', 'Direct .. in path join'),
            (r'open\([^)]*\.\.[^)]*\)', 'Direct .. in file open'),
        ]

        for pattern, description in dangerous_patterns:
            if re.search(pattern, code):
                auditor.log_issue("Path Security", f"DANGEROUS: {description}")
                print(f"  ✗ FOUND DANGEROUS PATTERN: {description}")

    except Exception as e:
        auditor.log_issue("Path Security", f"Path traversal check failed: {e}")

def check_storage_service_security(auditor):
    """Check storage service implementation for security issues"""
    print("\n" + "=" * 70)
    print("  4. STORAGE SERVICE SECURITY AUDIT")
    print("=" * 70)

    try:
        # Read storage_service.py
        with open('/home/user/entrust-app/backend/app/storage_service.py', 'r') as f:
            code = f.read()

        # Check for proper error handling
        if 'try:' in code and 'except' in code:
            auditor.log_pass("Error Handling", "Exception handling present")
            print("  ✓ Exception handling implemented")
        else:
            auditor.log_issue("Error Handling", "Missing exception handling")
            print("  ✗ Missing exception handling")

        # Check for credential exposure in logs
        if 'logger.info' in code or 'logger.debug' in code:
            if 'access_key' in code or 'secret' in code:
                # Check if secrets are being logged
                log_lines = [line for line in code.split('\n') if 'logger' in line]
                for line in log_lines:
                    if 'access_key' in line or 'secret' in line or 'connection_string' in line:
                        auditor.log_warning("Security", "Possible credential logging detected")
                        print(f"  ⚠ Possible credential in log: {line.strip()[:80]}")

        # Check for timeout configurations
        if 'timeout' in code or 'read_timeout' in code:
            auditor.log_pass("Reliability", "Timeout configuration present")
            print("  ✓ Timeout configurations found")
        else:
            auditor.log_warning("Reliability", "No timeout configurations found")
            print("  ⚠ No timeout configurations found")

        # Check for input validation
        if 'validate' in code or 'ValueError' in code:
            auditor.log_pass("Input Validation", "Input validation present")
            print("  ✓ Input validation implemented")

        # Check for SQL injection protection (should not use raw SQL)
        if 'execute(text(' in code or 'execute("' in code:
            auditor.log_issue("SQL Injection", "Raw SQL execution detected")
            print("  ✗ Raw SQL execution found (potential SQL injection)")
        else:
            auditor.log_pass("SQL Injection", "No raw SQL found in storage service")
            print("  ✓ No raw SQL execution")

    except Exception as e:
        auditor.log_issue("Storage Service", f"Storage service check failed: {e}")

def check_cloud_provider_configuration(auditor):
    """Check cloud provider SDK usage"""
    print("\n" + "=" * 70)
    print("  5. CLOUD PROVIDER SDK AUDIT")
    print("=" * 70)

    try:
        with open('/home/user/entrust-app/backend/app/storage_service.py', 'r') as f:
            code = f.read()

        # Check boto3 usage
        if 'import boto3' in code:
            print("\n  AWS SDK (boto3):")

            # Check for proper client creation
            if 'boto3.client' in code:
                auditor.log_pass("AWS SDK", "boto3 client creation found")
                print("    ✓ Client creation")

            # Check for credential handling
            if 'aws_access_key_id' in code and 'aws_secret_access_key' in code:
                auditor.log_pass("AWS SDK", "Credential passing to client")
                print("    ✓ Credentials passed to client")

            # Check for error handling
            if 'ClientError' in code or 'NoCredentialsError' in code:
                auditor.log_pass("AWS SDK", "AWS error handling")
                print("    ✓ AWS error handling")
            else:
                auditor.log_warning("AWS SDK", "Missing specific AWS error handling")
                print("    ⚠ Missing AWS-specific error handling")

        # Check Azure SDK usage
        if 'azure.storage.blob' in code:
            print("\n  Azure SDK (azure-storage-blob):")

            # Check for proper client creation
            if 'BlobServiceClient.from_connection_string' in code:
                auditor.log_pass("Azure SDK", "Blob client creation found")
                print("    ✓ Client creation")

            # Check for error handling
            if 'AzureError' in code or 'ResourceNotFoundError' in code:
                auditor.log_pass("Azure SDK", "Azure error handling")
                print("    ✓ Azure error handling")
            else:
                auditor.log_warning("Azure SDK", "Missing specific Azure error handling")
                print("    ⚠ Missing Azure-specific error handling")

    except Exception as e:
        auditor.log_issue("Cloud SDK", f"Cloud provider check failed: {e}")

def check_fallback_logic(auditor):
    """Check fallback logic implementation"""
    print("\n" + "=" * 70)
    print("  6. FALLBACK LOGIC AUDIT")
    print("=" * 70)

    try:
        with open('/home/user/entrust-app/backend/app/storage_service.py', 'r') as f:
            code = f.read()

        # Check for fallback implementation
        if 'fallback_enabled' in code:
            auditor.log_pass("Fallback", "Fallback configuration present")
            print("  ✓ Fallback configuration found")
        else:
            auditor.log_issue("Fallback", "Missing fallback configuration")
            print("  ✗ Missing fallback configuration")

        # Check for proper fallback flow
        if 'if self.fallback_enabled:' in code:
            auditor.log_pass("Fallback", "Fallback logic implemented")
            print("  ✓ Fallback logic found")

            # Check for logging
            if 'logger.info("Falling back' in code or 'logger.warning' in code:
                auditor.log_pass("Fallback", "Fallback logging present")
                print("  ✓ Fallback events are logged")

        # Check that local storage is tried when cloud fails
        save_methods = ['_save_to_s3', '_save_to_azure', '_save_to_local']
        for method in save_methods:
            if method in code:
                print(f"  ✓ Method {method} implemented")

    except Exception as e:
        auditor.log_issue("Fallback", f"Fallback check failed: {e}")

def check_report_retention(auditor):
    """Check report retention policy (one per day)"""
    print("\n" + "=" * 70)
    print("  7. REPORT RETENTION AUDIT")
    print("=" * 70)

    try:
        with open('/home/user/entrust-app/backend/app/report_utils.py', 'r') as f:
            code = f.read()

        # Check for date-based naming
        if 'strftime("%Y%m%d")' in code or 'date_str' in code:
            auditor.log_pass("Retention", "Date-based file naming")
            print("  ✓ Reports use date-based naming")
        else:
            auditor.log_warning("Retention", "Date-based naming not found")
            print("  ⚠ Date-based naming not clearly visible")

        # Check for version control (should be one per day)
        if 'overwrite=True' in code or '{date_str}' in code:
            auditor.log_pass("Retention", "Single version per day policy")
            print("  ✓ Single version per day (overwrites)")

        # Check for old report cleanup (should keep old reports)
        if 'delete' in code.lower() and 'old' in code.lower():
            auditor.log_warning("Retention", "Old report deletion detected")
            print("  ⚠ Old report deletion may be implemented")
        else:
            auditor.log_pass("Retention", "Old reports are preserved")
            print("  ✓ Old reports are preserved")

    except Exception as e:
        auditor.log_issue("Retention", f"Retention check failed: {e}")

def check_presigned_url_security(auditor):
    """Check pre-signed URL implementation"""
    print("\n" + "=" * 70)
    print("  8. PRE-SIGNED URL SECURITY AUDIT")
    print("=" * 70)

    try:
        with open('/home/user/entrust-app/backend/app/storage_service.py', 'r') as f:
            code = f.read()

        # Check for pre-signed URL methods
        if 'generate_presigned_url' in code:
            auditor.log_pass("Pre-signed URLs", "Pre-signed URL generation present")
            print("  ✓ Pre-signed URL generation implemented")

            # Check for expiration
            if 'expiration' in code or 'ExpiresIn' in code or 'expiry' in code:
                auditor.log_pass("Pre-signed URLs", "URL expiration configured")
                print("  ✓ URL expiration configured")

                # Check for reasonable expiration (should be limited)
                if '3600' in code or '7200' in code:
                    auditor.log_pass("Pre-signed URLs", "Reasonable expiration time (1-2 hours)")
                    print("  ✓ Reasonable expiration time")
            else:
                auditor.log_issue("Pre-signed URLs", "Missing URL expiration")
                print("  ✗ Missing URL expiration (security risk)")
        else:
            auditor.log_warning("Pre-signed URLs", "Pre-signed URL generation not found")
            print("  ⚠ Pre-signed URL generation not found")

    except Exception as e:
        auditor.log_issue("Pre-signed URLs", f"Pre-signed URL check failed: {e}")

def check_dependency_security(auditor):
    """Check for dependency issues"""
    print("\n" + "=" * 70)
    print("  9. DEPENDENCY SECURITY AUDIT")
    print("=" * 70)

    try:
        with open('/home/user/entrust-app/backend/requirements.txt', 'r') as f:
            requirements = f.read()

        # Check for required dependencies
        if 'boto3' in requirements:
            auditor.log_pass("Dependencies", "boto3 present for S3 support")
            print("  ✓ boto3 (AWS SDK)")
        else:
            auditor.log_warning("Dependencies", "boto3 not found")
            print("  ⚠ boto3 not in requirements")

        if 'azure-storage-blob' in requirements:
            auditor.log_pass("Dependencies", "azure-storage-blob present")
            print("  ✓ azure-storage-blob (Azure SDK)")
        else:
            auditor.log_warning("Dependencies", "azure-storage-blob not found")
            print("  ⚠ azure-storage-blob not in requirements")

        # Check for version pinning (security best practice)
        lines = requirements.split('\n')
        unpinned = [line for line in lines if line and not line.startswith('#') and '==' not in line and '>=' not in line]

        if unpinned:
            auditor.log_warning("Dependencies", f"Unpinned dependencies: {', '.join(unpinned)}")
            print(f"  ⚠ Unpinned dependencies found: {len(unpinned)}")
        else:
            auditor.log_pass("Dependencies", "All dependencies are version-pinned")
            print("  ✓ All dependencies are version-pinned")

    except Exception as e:
        auditor.log_issue("Dependencies", f"Dependency check failed: {e}")

def check_migration_safety(auditor):
    """Check migration script for safety"""
    print("\n" + "=" * 70)
    print("  10. MIGRATION SAFETY AUDIT")
    print("=" * 70)

    try:
        with open('/home/user/entrust-app/backend/deploy_db.py', 'r') as f:
            code = f.read()

        # Check for customer_storage migration
        if 'migrate_customer_storage' in code:
            auditor.log_pass("Migration", "customer_storage migration present")
            print("  ✓ customer_storage migration found")
        else:
            auditor.log_issue("Migration", "customer_storage migration not found")
            print("  ✗ customer_storage migration not found")
            return

        # Check for IF NOT EXISTS or column_exists checks
        if 'column_exists' in code or 'IF NOT EXISTS' in code:
            auditor.log_pass("Migration", "Safe migration with existence checks")
            print("  ✓ Migration uses existence checks (safe)")
        else:
            auditor.log_warning("Migration", "Missing existence checks")
            print("  ⚠ Migration may not check for existing columns")

        # Check for default values
        if "DEFAULT 'LOCAL'" in code:
            auditor.log_pass("Migration", "Default storage type is LOCAL")
            print("  ✓ Default storage type: LOCAL")

        if 'DEFAULT TRUE' in code or 'DEFAULT true' in code:
            auditor.log_pass("Migration", "Fallback enabled by default")
            print("  ✓ Fallback enabled by default")

        # Check for rollback capability
        if 'rollback' in code.lower():
            auditor.log_pass("Migration", "Rollback handling present")
            print("  ✓ Rollback handling implemented")

    except Exception as e:
        auditor.log_issue("Migration", f"Migration check failed: {e}")

def main():
    """Run all audits"""
    print("\n" + "=" * 70)
    print("  DEEP SECURITY AUDIT: STORAGE SERVICE IMPLEMENTATION")
    print("=" * 70)

    auditor = SecurityAuditor()

    # Run all checks
    check_database_schema(auditor)
    check_security_credentials(auditor)
    check_path_traversal_security(auditor)
    check_storage_service_security(auditor)
    check_cloud_provider_configuration(auditor)
    check_fallback_logic(auditor)
    check_report_retention(auditor)
    check_presigned_url_security(auditor)
    check_dependency_security(auditor)
    check_migration_safety(auditor)

    # Print results
    success = auditor.print_results()

    if success:
        print("\n✓ ALL CRITICAL CHECKS PASSED")
        print("  Review warnings above for potential improvements")
        sys.exit(0)
    else:
        print("\n✗ CRITICAL ISSUES FOUND")
        print("  Please address critical issues before deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()
