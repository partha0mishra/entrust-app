"""
Configuration Management for Azure AI Foundry Integration
"""

from .endpoints import (
    load_foundry_config,
    get_foundry_client,
    AzureAIFoundryConfig
)

__all__ = [
    "load_foundry_config",
    "get_foundry_client",
    "AzureAIFoundryConfig"
]
