"""
Azure AI Foundry Endpoint Configuration
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class AzureAIFoundryConfig:
    """Configuration for Azure AI Foundry integration"""

    project_endpoint: str
    api_key: str
    api_version: str = "2024-07-01"
    timeout: int = 1800  # 30 minutes default

    # Flow endpoint URLs (optional, for direct flow invocation)
    flows: Dict[str, str] = field(default_factory=dict)

    # Feature flags
    use_mock_client: bool = False  # For testing without deployment


def load_foundry_config() -> Optional[AzureAIFoundryConfig]:
    """
    Load Azure AI Foundry configuration from environment or database

    Priority:
    1. Environment variables (AZURE_AI_FOUNDRY_*)
    2. Database LLMConfig table (provider_type = "AZURE_AI_FOUNDRY")
    3. Return None if not configured

    Environment Variables:
        AZURE_AI_FOUNDRY_ENDPOINT: Project endpoint URL
        AZURE_AI_FOUNDRY_API_KEY: API key
        AZURE_AI_FOUNDRY_API_VERSION: API version (optional, default: 2024-07-01)
        AZURE_AI_FOUNDRY_USE_MOCK: Use mock client for testing (optional, default: false)

    Returns:
        AzureAIFoundryConfig instance or None if not configured
    """
    # Try environment variables first
    endpoint = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
    api_key = os.getenv("AZURE_AI_FOUNDRY_API_KEY")

    if endpoint and api_key:
        logger.info("Loading Azure AI Foundry config from environment variables")
        return AzureAIFoundryConfig(
            project_endpoint=endpoint,
            api_key=api_key,
            api_version=os.getenv("AZURE_AI_FOUNDRY_API_VERSION", "2024-07-01"),
            use_mock_client=os.getenv("AZURE_AI_FOUNDRY_USE_MOCK", "false").lower() == "true"
        )

    # Try loading from database
    try:
        # Import here to avoid circular dependency
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

        from app.database import SessionLocal
        from app import models

        db = SessionLocal()

        # Look for Azure AI Foundry config in database
        # For now, we'll use a special "Azure AI Foundry" purpose in LLMConfig
        llm_config = db.query(models.LLMConfig).filter(
            models.LLMConfig.purpose == "Azure AI Foundry"
        ).first()

        if llm_config:
            logger.info("Loading Azure AI Foundry config from database")

            # Extract from azure_* fields (reusing Azure OpenAI fields for simplicity)
            return AzureAIFoundryConfig(
                project_endpoint=llm_config.azure_endpoint or "",
                api_key=llm_config.azure_api_key or "",
                api_version=llm_config.azure_api_version or "2024-07-01"
            )

        db.close()

    except Exception as e:
        logger.warning(f"Could not load config from database: {e}")

    # Not configured
    logger.warning("Azure AI Foundry not configured. Set AZURE_AI_FOUNDRY_ENDPOINT and AZURE_AI_FOUNDRY_API_KEY environment variables.")
    return None


def get_foundry_client():
    """
    Get initialized Azure AI Foundry client

    Returns:
        AzureAIFoundryClient instance or None if not configured
    """
    from ..sdk.foundry_client import AzureAIFoundryClient, MockAzureAIFoundryClient

    config = load_foundry_config()

    if not config:
        logger.warning("Azure AI Foundry not configured, returning None")
        return None

    # Use mock client for testing if configured
    if config.use_mock_client:
        logger.warning("Using MOCK Azure AI Foundry client for testing")
        return MockAzureAIFoundryClient(
            project_endpoint=config.project_endpoint,
            api_key=config.api_key,
            timeout=config.timeout,
            api_version=config.api_version
        )

    # Return real client
    return AzureAIFoundryClient(
        project_endpoint=config.project_endpoint,
        api_key=config.api_key,
        timeout=config.timeout,
        api_version=config.api_version
    )


if __name__ == "__main__":
    # Test configuration loading
    print("Testing configuration loading...")

    config = load_foundry_config()
    if config:
        print(f"Loaded config: {config.project_endpoint}")
        print(f"Use mock: {config.use_mock_client}")
    else:
        print("No configuration found")
