#!/usr/bin/env python3
"""
Deep audit script to verify LLM configuration implementation
"""
import sys
from sqlalchemy import inspect, text
from app.database import SessionLocal, engine
from app import models, schemas
import json

def audit_database_schema():
    """Check database schema matches models"""
    print("=" * 70)
    print("  DATABASE SCHEMA AUDIT")
    print("=" * 70)
    
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('llm_configs')}
    
    required_columns = [
        'azure_reasoning_effort',
        'aws_thinking_mode'
    ]
    
    all_ok = True
    for col_name in required_columns:
        if col_name in columns:
            col_type = str(columns[col_name]['type'])
            print(f"✓ {col_name}: {col_type}")
        else:
            print(f"✗ {col_name}: MISSING!")
            all_ok = False
    
    return all_ok

def audit_models():
    """Check SQLAlchemy models have the fields"""
    print("\n" + "=" * 70)
    print("  SQLALCHEMY MODELS AUDIT")
    print("=" * 70)
    
    all_ok = True
    if hasattr(models.LLMConfig, 'azure_reasoning_effort'):
        print("✓ models.LLMConfig.azure_reasoning_effort exists")
    else:
        print("✗ models.LLMConfig.azure_reasoning_effort MISSING!")
        all_ok = False
    
    if hasattr(models.LLMConfig, 'aws_thinking_mode'):
        print("✓ models.LLMConfig.aws_thinking_mode exists")
    else:
        print("✗ models.LLMConfig.aws_thinking_mode MISSING!")
        all_ok = False
    
    return all_ok

def audit_schemas():
    """Check Pydantic schemas have the fields"""
    print("\n" + "=" * 70)
    print("  PYDANTIC SCHEMAS AUDIT")
    print("=" * 70)
    
    all_ok = True
    schema_fields = schemas.LLMConfigBase.__fields__
    
    if 'azure_reasoning_effort' in schema_fields:
        print("✓ schemas.LLMConfigBase.azure_reasoning_effort exists")
    else:
        print("✗ schemas.LLMConfigBase.azure_reasoning_effort MISSING!")
        all_ok = False
    
    if 'aws_thinking_mode' in schema_fields:
        print("✓ schemas.LLMConfigBase.aws_thinking_mode exists")
    else:
        print("✗ schemas.LLMConfigBase.aws_thinking_mode MISSING!")
        all_ok = False
    
    return all_ok

def audit_providers():
    """Check provider implementations"""
    print("\n" + "=" * 70)
    print("  PROVIDER IMPLEMENTATION AUDIT")
    print("=" * 70)
    
    from app.llm_providers import AzureOpenAIProvider, AWSBedrockProvider
    
    all_ok = True
    
    # Check Azure provider
    try:
        import inspect as py_inspect
        azure_init = py_inspect.signature(AzureOpenAIProvider.__init__)
        if 'reasoning_effort' in azure_init.parameters:
            print("✓ AzureOpenAIProvider.__init__ has reasoning_effort parameter")
        else:
            print("✗ AzureOpenAIProvider.__init__ missing reasoning_effort parameter!")
            all_ok = False
    except Exception as e:
        print(f"✗ Error checking Azure provider: {e}")
        all_ok = False
    
    # Check Bedrock provider
    try:
        bedrock_init = py_inspect.signature(AWSBedrockProvider.__init__)
        if 'thinking_mode' in bedrock_init.parameters:
            print("✓ AWSBedrockProvider.__init__ has thinking_mode parameter")
        else:
            print("✗ AWSBedrockProvider.__init__ missing thinking_mode parameter!")
            all_ok = False
    except Exception as e:
        print(f"✗ Error checking Bedrock provider: {e}")
        all_ok = False
    
    return all_ok

def test_config_creation():
    """Test creating a config with new fields"""
    print("\n" + "=" * 70)
    print("  CONFIG CREATION TEST")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        # Test creating config with reasoning_effort
        test_config = models.LLMConfig(
            purpose="Test_Purpose_Audit",
            provider_type=models.LLMProviderType.AZURE,
            azure_endpoint="https://test.example.com",
            azure_api_key="test-key",
            azure_deployment_name="gpt-5",
            azure_reasoning_effort="high"
        )
        
        # Just test that we can create it (don't save to DB)
        print("✓ Can create LLMConfig with azure_reasoning_effort")
        
        # Test Bedrock config
        test_config2 = models.LLMConfig(
            purpose="Test_Purpose_Audit2",
            provider_type=models.LLMProviderType.BEDROCK,
            aws_region="us-east-1",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            aws_model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            aws_thinking_mode="enabled"
        )
        
        print("✓ Can create LLMConfig with aws_thinking_mode")
        
        return True
    except Exception as e:
        print(f"✗ Error creating test config: {e}")
        return False
    finally:
        db.close()

def main():
    """Run all audits"""
    print("\n" + "=" * 70)
    print("  DEEP AUDIT: LLM Configuration Implementation")
    print("=" * 70 + "\n")
    
    results = []
    results.append(("Database Schema", audit_database_schema()))
    results.append(("SQLAlchemy Models", audit_models()))
    results.append(("Pydantic Schemas", audit_schemas()))
    results.append(("Provider Implementations", audit_providers()))
    results.append(("Config Creation", test_config_creation()))
    
    print("\n" + "=" * 70)
    print("  AUDIT SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✓ ALL CHECKS PASSED - Implementation is ready!")
    else:
        print("  ✗ SOME CHECKS FAILED - Review issues above")
    print("=" * 70 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

