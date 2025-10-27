"""
LLM Provider Adapters for different cloud providers and local LLMs
"""
import httpx
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import json


class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""

    @abstractmethod
    async def test_connection(self) -> Dict:
        """Test the connection to the LLM provider"""
        pass

    @abstractmethod
    async def call_llm(self, messages: List[Dict], max_tokens: int = 500) -> str:
        """Call the LLM with messages and return the response content"""
        pass


class LocalLLMProvider(BaseLLMProvider):
    """Provider for local LLMs (LM Studio, Ollama, etc.) using OpenAI-compatible API"""

    def __init__(self, api_url: str, api_key: Optional[str] = None, model_name: str = "default", timeout: float = 180.0):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout

    async def test_connection(self) -> Dict:
        """Test connection with a simple message"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": "Hello, this is a test message."}],
            "max_tokens": 10
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                return {"status": "Success", "response": response.json()}
        except Exception as e:
            return {"status": "Failed", "error": str(e)}

    async def call_llm(self, messages: List[Dict], max_tokens: int = 500) -> str:
        """Call the local LLM API"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()

                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content:
                    raise Exception("No content in LLM response")

                return content
        except httpx.TimeoutException:
            raise Exception(f"LLM request timed out after {self.timeout} seconds")
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error calling LLM: {str(e)}")
        except Exception as e:
            raise Exception(f"LLM API Error: {str(e)}")


class AWSBedrockProvider(BaseLLMProvider):
    """Provider for AWS Bedrock"""

    def __init__(
        self,
        region: str,
        access_key_id: str,
        secret_access_key: str,
        model_id: str,
        timeout: float = 180.0
    ):
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.model_id = model_id
        self.timeout = timeout
        self._client = None

    def _get_client(self):
        """Lazy initialization of boto3 client"""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    'bedrock-runtime',
                    region_name=self.region,
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key
                )
            except ImportError:
                raise Exception("boto3 is not installed. Install it with: pip install boto3")
        return self._client

    async def test_connection(self) -> Dict:
        """Test connection to AWS Bedrock"""
        try:
            client = self._get_client()

            # Prepare a simple test request
            messages = [{"role": "user", "content": "Hello"}]
            body = self._prepare_request_body(messages, max_tokens=10)

            response = client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            return {"status": "Success", "response": {"message": "Connection successful"}}
        except Exception as e:
            return {"status": "Failed", "error": str(e)}

    async def call_llm(self, messages: List[Dict], max_tokens: int = 500) -> str:
        """Call AWS Bedrock API"""
        try:
            client = self._get_client()

            # Prepare request body based on model type
            body = self._prepare_request_body(messages, max_tokens)

            response = client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            # Parse response based on model type
            response_body = json.loads(response['body'].read())
            return self._extract_content(response_body)

        except Exception as e:
            raise Exception(f"AWS Bedrock API Error: {str(e)}")

    def _prepare_request_body(self, messages: List[Dict], max_tokens: int) -> Dict:
        """Prepare request body based on model type"""
        # For Anthropic Claude models on Bedrock
        if "anthropic.claude" in self.model_id.lower():
            # Convert messages to Claude format
            system_msg = ""
            user_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": user_messages
            }

            if system_msg:
                body["system"] = system_msg

            return body

        # For Amazon Titan models
        elif "amazon.titan" in self.model_id.lower():
            # Combine messages into a single prompt
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            return {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": 0.7
                }
            }

        # For AI21 Jurassic models
        elif "ai21" in self.model_id.lower():
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            return {
                "prompt": prompt,
                "maxTokens": max_tokens,
                "temperature": 0.7
            }

        # Default fallback
        else:
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            return {
                "prompt": prompt,
                "max_tokens": max_tokens
            }

    def _extract_content(self, response_body: Dict) -> str:
        """Extract content from response based on model type"""
        # For Anthropic Claude models
        if "anthropic.claude" in self.model_id.lower():
            content_items = response_body.get("content", [])
            if content_items and len(content_items) > 0:
                return content_items[0].get("text", "")
            raise Exception("No content in Bedrock response")

        # For Amazon Titan models
        elif "amazon.titan" in self.model_id.lower():
            results = response_body.get("results", [])
            if results and len(results) > 0:
                return results[0].get("outputText", "")
            raise Exception("No content in Bedrock response")

        # For AI21 models
        elif "ai21" in self.model_id.lower():
            completions = response_body.get("completions", [])
            if completions and len(completions) > 0:
                return completions[0].get("data", {}).get("text", "")
            raise Exception("No content in Bedrock response")

        # Default fallback
        else:
            if "completion" in response_body:
                return response_body["completion"]
            elif "text" in response_body:
                return response_body["text"]
            else:
                raise Exception("Unknown response format from Bedrock")


class AzureOpenAIProvider(BaseLLMProvider):
    """Provider for Azure OpenAI"""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment_name: str,
        api_version: str = "2024-02-15-preview",
        timeout: float = 180.0
    ):
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.timeout = timeout

    def _get_url(self) -> str:
        """Construct the Azure OpenAI API URL"""
        return f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"

    async def test_connection(self) -> Dict:
        """Test connection to Azure OpenAI"""
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

        payload = {
            "messages": [{"role": "user", "content": "Hello, this is a test message."}],
            "max_tokens": 10
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self._get_url(), json=payload, headers=headers)
                response.raise_for_status()
                return {"status": "Success", "response": response.json()}
        except Exception as e:
            return {"status": "Failed", "error": str(e)}

    async def call_llm(self, messages: List[Dict], max_tokens: int = 500) -> str:
        """Call Azure OpenAI API"""
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

        payload = {
            "messages": messages,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self._get_url(), json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()

                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content:
                    raise Exception("No content in Azure OpenAI response")

                return content
        except httpx.TimeoutException:
            raise Exception(f"Azure OpenAI request timed out after {self.timeout} seconds")
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error calling Azure OpenAI: {str(e)}")
        except Exception as e:
            raise Exception(f"Azure OpenAI API Error: {str(e)}")


def get_llm_provider(config) -> BaseLLMProvider:
    """Factory function to get the appropriate LLM provider based on config"""
    from .models import LLMProviderType

    if config.provider_type == LLMProviderType.LOCAL:
        if not config.api_url:
            raise ValueError("api_url is required for local LLM provider")
        return LocalLLMProvider(
            api_url=config.api_url,
            api_key=config.api_key,
            model_name=config.model_name or "default"
        )

    elif config.provider_type == LLMProviderType.BEDROCK:
        if not all([config.aws_region, config.aws_access_key_id, config.aws_secret_access_key, config.aws_model_id]):
            raise ValueError("AWS region, access_key_id, secret_access_key, and model_id are required for Bedrock")
        return AWSBedrockProvider(
            region=config.aws_region,
            access_key_id=config.aws_access_key_id,
            secret_access_key=config.aws_secret_access_key,
            model_id=config.aws_model_id
        )

    elif config.provider_type == LLMProviderType.AZURE:
        if not all([config.azure_endpoint, config.azure_api_key, config.azure_deployment_name]):
            raise ValueError("Azure endpoint, api_key, and deployment_name are required for Azure OpenAI")
        return AzureOpenAIProvider(
            endpoint=config.azure_endpoint,
            api_key=config.azure_api_key,
            deployment_name=config.azure_deployment_name,
            api_version=config.azure_api_version or "2024-02-15-preview"
        )

    else:
        raise ValueError(f"Unsupported provider type: {config.provider_type}")
