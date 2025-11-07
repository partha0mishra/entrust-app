#!/usr/bin/env python3
"""
Deep Audit Script for LLM Configuration Implementation
Checks database, models, schemas, providers, and integration
"""
import sys
import asyncio
from sqlalchemy import inspect, text
from app.database import SessionLocal, engine
from app import models, schemas
import json

def check_database_schema():
    """Check database schema for LLM configs table"""
    print("=" * 70)
    print("  1. DATABASE SCHEMA AUDIT")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        
        # Check if table exists
        if 'llm_configs' not in inspector.get_table_names():
            print("✗ Table 'llm_configs' does not exist!")
            return False
        
        # Get all columns
        columns = {col['name']: col for col in inspector.get_columns('llm_configs')}
        
        required_columns = [
            'id', 'purpose', 'provider_type', 'model_name', 'status',
            'api_url', 'api_key',
            'aws_region', 'aws_access_key_id', 'aws_secret_access_key', 'aws_model_id', 'aws_thinking_mode',
            'azure_endpoint', 'azure_api_key', 'azure_deployment_name', 'azure_api_version', 'azure_reasoning_effort'
        ]
        
        print(f"\nTable 'llm_configs' exists with {len(columns)} columns")
        
        missing = []
        for col in required_columns:
            if col in columns:
                col_type = str(columns[col]['type'])
                print(f"  ✓ {col}: {col_type}")
            else:
                print(f"  ✗ {col}: MISSING")
                missing.append(col)
        
        if missing:
            print(f"\n✗ Missing columns: {', '.join(missing)}")
            return False
        
        print("\n✓ All required columns present")
        return True
        
    except Exception as e:
        print(f"✗ Database schema check failed: {e}")
        return False
    finally:
        db.close()

def check_sqlalchemy_model():
    """Check SQLAlchemy model definition"""
    print("\n" + "=" * 70)
    print("  2. SQLALCHEMY MODEL AUDIT")
    print("=" * 70)
    
    try:
        # Check LLMConfig model
        model = models.LLMConfig
        table = model.__table__
        
        required_fields = [
            'id', 'purpose', 'provider_type', 'model_name', 'status',
            'api_url', 'api_key',
            'aws_region', 'aws_access_key_id', 'aws_secret_access_key', 'aws_model_id', 'aws_thinking_mode',
            'azure_endpoint', 'azure_api_key', 'azure_deployment_name', 'azure_api_version', 'azure_reasoning_effort'
        ]
        
        print(f"\nModel: {model.__name__}")
        print(f"Table: {table.name}")
        
        model_columns = [col.name for col in table.columns]
        missing = []
        
        for field in required_fields:
            if field in model_columns:
                col = table.columns[field]
                print(f"  ✓ {field}: {col.type}")
            else:
                print(f"  ✗ {field}: MISSING")
                missing.append(field)
        
        if missing:
            print(f"\n✗ Missing model fields: {', '.join(missing)}")
            return False
        
        print("\n✓ All required model fields present")
        return True
        
    except Exception as e:
        print(f"✗ SQLAlchemy model check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_pydantic_schema():
    """Check Pydantic schema definition"""
    print("\n" + "=" * 70)
    print("  3. PYDANTIC SCHEMA AUDIT")
    print("=" * 70)
    
    try:
        schema = schemas.LLMConfigBase
        
        required_fields = [
            'purpose', 'provider_type', 'model_name',
            'api_url', 'api_key',
            'aws_region', 'aws_access_key_id', 'aws_secret_access_key', 'aws_model_id', 'aws_thinking_mode',
            'azure_endpoint', 'azure_api_key', 'azure_deployment_name', 'azure_api_version', 'azure_reasoning_effort'
        ]
        
        print(f"\nSchema: {schema.__name__}")
        print(f"Fields: {len(schema.model_fields)}")
        
        missing = []
        for field in required_fields:
            if field in schema.model_fields:
                field_info = schema.model_fields[field]
                field_type = field_info.annotation
                default = field_info.default if hasattr(field_info, 'default') else 'None'
                print(f"  ✓ {field}: {field_type} (default: {default})")
            else:
                print(f"  ✗ {field}: MISSING")
                missing.append(field)
        
        if missing:
            print(f"\n✗ Missing schema fields: {', '.join(missing)}")
            return False
        
        print("\n✓ All required schema fields present")
        return True
        
    except Exception as e:
        print(f"✗ Pydantic schema check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_provider_implementation():
    """Check provider implementation"""
    print("\n" + "=" * 70)
    print("  4. PROVIDER IMPLEMENTATION AUDIT")
    print("=" * 70)
    
    success = True
    
    # Check AWSBedrockProvider
    try:
        from app.llm_providers import AWSBedrockProvider
        import inspect as inspect_module
        
        # Check __init__ signature
        init_sig = inspect_module.signature(AWSBedrockProvider.__init__)
        params = list(init_sig.parameters.keys())
        
        if 'thinking_mode' in params:
            print("✓ AWSBedrockProvider.__init__ has 'thinking_mode' parameter")
        else:
            print("✗ AWSBedrockProvider.__init__ missing 'thinking_mode' parameter")
            success = False
        
        # Check _prepare_request_body for temperature logic
        source = inspect_module.getsource(AWSBedrockProvider._prepare_request_body)
        if 'temperature' in source and 'thinking_mode' in source:
            if 'temperature' in source and '1' in source and 'thinking' in source.lower():
                print("✓ AWSBedrockProvider._prepare_request_body has temperature=1 logic for thinking mode")
            else:
                print("⚠ AWSBedrockProvider._prepare_request_body may have temperature logic issues")
        else:
            print("✗ AWSBedrockProvider._prepare_request_body missing temperature/thinking logic")
            success = False
        
        # Check _get_client for timeout
        source = inspect_module.getsource(AWSBedrockProvider._get_client)
        if 'read_timeout' in source and 'thinking_mode' in source:
            print("✓ AWSBedrockProvider._get_client has dynamic timeout for thinking mode")
        else:
            print("✗ AWSBedrockProvider._get_client missing dynamic timeout")
            success = False
        
        # Check verify=False
        if 'verify=False' in source:
            print("✓ AWSBedrockProvider._get_client has verify=False")
        else:
            print("⚠ AWSBedrockProvider._get_client may not have verify=False")
        
    except Exception as e:
        print(f"✗ AWSBedrockProvider check failed: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    # Check AzureOpenAIProvider
    try:
        from app.llm_providers import AzureOpenAIProvider
        import inspect as inspect_module
        
        init_sig = inspect_module.signature(AzureOpenAIProvider.__init__)
        params = list(init_sig.parameters.keys())
        
        if 'reasoning_effort' in params:
            print("✓ AzureOpenAIProvider.__init__ has 'reasoning_effort' parameter")
        else:
            print("✗ AzureOpenAIProvider.__init__ missing 'reasoning_effort' parameter")
            success = False
            
    except Exception as e:
        print(f"✗ AzureOpenAIProvider check failed: {e}")
        success = False
    
    # Check get_llm_provider factory
    try:
        from app.llm_providers import get_llm_provider
        import inspect as inspect_module
        
        source = inspect_module.getsource(get_llm_provider)
        if 'thinking_mode' in source and 'getattr' in source:
            print("✓ get_llm_provider passes thinking_mode to AWSBedrockProvider")
        else:
            print("✗ get_llm_provider may not pass thinking_mode correctly")
            success = False
        
        if 'reasoning_effort' in source:
            print("✓ get_llm_provider passes reasoning_effort to AzureOpenAIProvider")
        else:
            print("⚠ get_llm_provider may not pass reasoning_effort")
            
    except Exception as e:
        print(f"✗ get_llm_provider check failed: {e}")
        success = False
    
    return success

def check_database_data():
    """Check actual database data"""
    print("\n" + "=" * 70)
    print("  5. DATABASE DATA AUDIT")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        configs = db.query(models.LLMConfig).all()
        print(f"\nFound {len(configs)} LLM configs in database")
        
        if len(configs) == 0:
            print("⚠ No LLM configs found (this is OK for a fresh deployment)")
            return True
        
        for config in configs:
            print(f"\n  Config: {config.purpose}")
            print(f"    Provider: {config.provider_type}")
            print(f"    Status: {config.status}")
            
            if config.provider_type == models.LLMProviderType.BEDROCK:
                print(f"    Model: {config.aws_model_id}")
                print(f"    Region: {config.aws_region}")
                print(f"    Thinking Mode: {config.aws_thinking_mode}")
                if config.aws_thinking_mode == 'enabled':
                    print("    ✓ Thinking mode is enabled")
                else:
                    print("    ⚠ Thinking mode is disabled")
                    
            elif config.provider_type == models.LLMProviderType.AZURE:
                print(f"    Model: {config.azure_deployment_name}")
                print(f"    Endpoint: {config.azure_endpoint}")
                print(f"    Reasoning Effort: {config.azure_reasoning_effort}")
        
        print("\n✓ Database data check completed")
        return True
        
    except Exception as e:
        print(f"✗ Database data check failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def check_report_integration():
    """Check report generation integration"""
    print("\n" + "=" * 70)
    print("  6. REPORT GENERATION INTEGRATION AUDIT")
    print("=" * 70)
    
    try:
        from app.routers import reports
        import inspect as inspect_module
        
        # Check get_dimension_report
        source = inspect_module.getsource(reports.get_dimension_report)
        
        checks = [
            ('llm_config.status == "Success"', 'Status check'),
            ('aws_thinking_mode', 'Thinking mode detection'),
            ('timeout_seconds', 'Timeout configuration'),
            ('asyncio.wait_for', 'Timeout wrapper'),
        ]
        
        for check_str, description in checks:
            if check_str in source:
                print(f"✓ {description}: Present")
            else:
                print(f"✗ {description}: Missing")
                return False
        
        print("\n✓ Report generation integration looks correct")
        return True
        
    except Exception as e:
        print(f"✗ Report integration check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all audits"""
    print("\n" + "=" * 70)
    print("  DEEP AUDIT: LLM CONFIGURATION IMPLEMENTATION")
    print("=" * 70)
    print()
    
    results = []
    
    results.append(("Database Schema", check_database_schema()))
    results.append(("SQLAlchemy Model", check_sqlalchemy_model()))
    results.append(("Pydantic Schema", check_pydantic_schema()))
    results.append(("Provider Implementation", check_provider_implementation()))
    results.append(("Database Data", check_database_data()))
    results.append(("Report Integration", check_report_integration()))
    
    print("\n" + "=" * 70)
    print("  AUDIT SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✓ ALL CHECKS PASSED - System is properly configured!")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} CHECK(S) FAILED - Review issues above")
        sys.exit(1)

if __name__ == "__main__":
    main()

