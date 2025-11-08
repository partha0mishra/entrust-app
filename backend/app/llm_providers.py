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

    def __init__(self, api_url: str, api_key: Optional[str] = None, model_name: str = "default", timeout: float = 1800.0):
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
        timeout: float = 1800.0,
        thinking_mode: Optional[str] = None
    ):
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.model_id = model_id
        self.timeout = timeout
        self.thinking_mode = thinking_mode  # For Claude Sonnet: enabled, disabled
        self._client = None

    def _reset_client(self):
        """Reset the cached client to force recreation with new settings"""
        self._client = None

    def _get_client(self):
        """Lazy initialization of boto3 client"""
        if self._client is None:
            try:
                import boto3
                from botocore.config import Config
                
                # Configure timeout - longer for thinking mode since it can take much longer
                # Default boto3 read timeout is 60s, which is too short for thinking mode
                # With thinking mode and max_tokens=20000, requests can take 15-20 minutes
                read_timeout = 1200 if self.thinking_mode == "enabled" else 180  # 20 min for thinking, 3 min otherwise
                
                config = Config(
                    read_timeout=read_timeout,
                    retries={'max_attempts': 3}
                )
                
                self._client = boto3.client(
                    'bedrock-runtime',
                    region_name=self.region,
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                    config=config,
                    verify=False  # As per bedrock_access_guide.md
                )
            except ImportError:
                raise Exception("boto3 is not installed. Install it with: pip install boto3")
        return self._client

    async def test_connection(self) -> Dict:
        """Test connection to AWS Bedrock"""
        try:
            import asyncio
            client = self._get_client()

            # Prepare a simple test request
            # If thinking mode is enabled, max_tokens must be greater than budget_tokens (10000)
            # Use a minimal value (15000) for testing to keep it fast
            test_max_tokens = 15000 if self.thinking_mode == "enabled" else 10
            messages = [{"role": "user", "content": "Hello"}]
            body = self._prepare_request_body(messages, max_tokens=test_max_tokens)

            # Run synchronous boto3 call in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body),
                    contentType='application/json',  # As per bedrock_access_guide.md
                    accept='application/json'  # As per bedrock_access_guide.md
                )
            )

            return {"status": "Success", "response": {"message": "Connection successful"}}
        except Exception as e:
            return {"status": "Failed", "error": str(e)}

    async def call_llm(self, messages: List[Dict], max_tokens: int = 500) -> str:
        """Call AWS Bedrock API"""
        try:
            import asyncio
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"AWS Bedrock call_llm - Model: {self.model_id}, Region: {self.region}, Messages: {len(messages)}, Max Tokens: {max_tokens}, Thinking Mode: {self.thinking_mode}")
            
            client = self._get_client()

            # Prepare request body based on model type
            body = self._prepare_request_body(messages, max_tokens)
            
            logger.debug(f"AWS Bedrock request body prepared - Max Tokens: {body.get('max_tokens', 'N/A')}, Thinking: {body.get('thinking', 'N/A')}")

            # Run synchronous boto3 call in executor to avoid blocking event loop
            # and ensure timeout configuration is respected
            loop = asyncio.get_event_loop()
            logger.info("Calling AWS Bedrock invoke_model...")
            response = await loop.run_in_executor(
                None,
                lambda: client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body),
                    contentType='application/json',  # As per bedrock_access_guide.md
                    accept='application/json'  # As per bedrock_access_guide.md
                )
            )
            
            logger.info("AWS Bedrock invoke_model completed, parsing response...")

            # Parse response based on model type
            response_body = json.loads(response['body'].read())
            content = self._extract_content(response_body)
            logger.info(f"AWS Bedrock call_llm completed successfully - Response length: {len(content)} chars")
            return content

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"AWS Bedrock API Error: {str(e)}", exc_info=True)
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

            # Add thinking mode for Claude Sonnet models if enabled
            thinking_budget_tokens = 10000  # Default budget for thinking tokens
            if self.thinking_mode == "enabled":
                # When thinking mode is enabled, max_tokens MUST be greater than budget_tokens
                # AWS Bedrock requires: max_tokens > thinking.budget_tokens
                # If max_tokens is too small, automatically increase it to ensure it works
                if max_tokens <= thinking_budget_tokens:
                    # Ensure max_tokens is at least 50% more than budget_tokens for safety
                    max_tokens = int(thinking_budget_tokens * 1.5)  # 15000 minimum
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": user_messages
            }

            if system_msg:
                body["system"] = system_msg
            
            # Add thinking mode for Claude Sonnet models if enabled
            if self.thinking_mode == "enabled":
                # Claude thinking mode structure: {"type": "enabled", "budget_tokens": 10000}
                # When thinking is enabled, temperature MUST be 1 (per Claude documentation)
                body["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": thinking_budget_tokens
                }
                body["temperature"] = 1  # Required when thinking is enabled
            else:
                body["temperature"] = 0.7  # Default temperature when thinking is disabled

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
        timeout: float = 1800.0,
        reasoning_effort: Optional[str] = None
    ):
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.timeout = timeout
        self.reasoning_effort = reasoning_effort

    def _get_url(self) -> str:
        """Construct the Azure OpenAI API URL"""
        return f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"

    async def test_connection(self) -> Dict:
        """Test connection to Azure OpenAI"""
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

        # Check if this is a GPT-5 or O3 model (doesn't support max_tokens)
        is_gpt5_model = self.deployment_name and self.deployment_name.startswith('gpt-5')
        is_o3_model = self.deployment_name and self.deployment_name.startswith('o3')
        
        payload = {
            "messages": [{"role": "user", "content": "Hello, this is a test message."}]
        }
        
        # GPT-5 and O3 models don't support max_tokens
        if not (is_gpt5_model or is_o3_model):
            payload["max_tokens"] = 10
        
        # Note: reasoning_effort parameter is not supported by all Azure OpenAI GPT-5 deployments
        # If your deployment supports it, you can add it here, but it causes 400 errors on some deployments
        # if is_gpt5_model and self.reasoning_effort:
        #     payload["reasoning"] = {"effort": self.reasoning_effort}

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

        # Validate messages
        if not messages or len(messages) == 0:
            raise Exception("Messages array cannot be empty")
        
        # Validate and clean messages
        validated_messages = []
        for msg in messages:
            if not isinstance(msg, dict):
                raise Exception(f"Invalid message format: {type(msg)}")
            if "role" not in msg or "content" not in msg:
                raise Exception(f"Message missing required fields (role, content): {msg}")
            if not msg.get("content") or not str(msg.get("content")).strip():
                raise Exception(f"Message content cannot be empty: {msg}")
            validated_messages.append({
                "role": str(msg["role"]),
                "content": str(msg["content"])
            })

        # Check if this is a GPT-5 model (doesn't support max_tokens, temperature, etc.)
        is_gpt5_model = self.deployment_name and self.deployment_name.startswith('gpt-5')
        is_o3_model = self.deployment_name and self.deployment_name.startswith('o3')
        
        payload = {
            "messages": validated_messages
        }
        
        # GPT-5 and O3 models don't support standard parameters like max_tokens
        # For gpt-4o and other models, ensure max_tokens is within valid range
        if not (is_gpt5_model or is_o3_model):
            # Azure OpenAI max_tokens range is typically 1-8192 for most models
            # gpt-4o supports up to 16384 tokens
            if max_tokens > 16384:
                max_tokens = 16384
            if max_tokens < 1:
                max_tokens = 100  # Default minimum
            payload["max_tokens"] = max_tokens
        
        # Note: reasoning_effort parameter is not supported by all Azure OpenAI GPT-5 deployments
        # If your deployment supports it, you can add it here, but it causes 400 errors on some deployments
        # The reasoning tokens are automatically used by GPT-5 based on the complexity of the task
        # if is_gpt5_model and self.reasoning_effort:
        #     payload["reasoning"] = {"effort": self.reasoning_effort}

        try:
            # Log request details (sanitized) for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Azure OpenAI Request - URL: {self._get_url()}, Deployment: {self.deployment_name}, Messages: {len(validated_messages)}, Max Tokens: {payload.get('max_tokens', 'N/A (GPT-5/O3)')}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self._get_url(), json=payload, headers=headers)
                
                # Capture detailed error response for debugging
                if response.status_code != 200:
                    error_detail = ""
                    try:
                        error_body = response.json()
                        error_detail = error_body.get("error", {})
                        if isinstance(error_detail, dict):
                            error_detail = error_detail.get("message", str(error_detail))
                        else:
                            error_detail = str(error_detail)
                    except:
                        error_detail = response.text[:500] if response.text else "Unknown error"
                    
                    raise Exception(f"HTTP error calling Azure OpenAI: {response.status_code} {response.reason_phrase}. Error: {error_detail}")
                
                result = response.json()

                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content:
                    raise Exception("No content in Azure OpenAI response")

                return content
        except httpx.TimeoutException:
            raise Exception(f"Azure OpenAI request timed out after {self.timeout} seconds")
        except httpx.HTTPStatusError as e:
            # This is already handled above, but catch it here for safety
            error_detail = ""
            if hasattr(e, 'response'):
                try:
                    error_body = e.response.json()
                    error_detail = error_body.get("error", {})
                    if isinstance(error_detail, dict):
                        error_detail = error_detail.get("message", str(error_detail))
                    else:
                        error_detail = str(error_detail)
                except:
                    error_detail = e.response.text[:500] if e.response.text else "Unknown error"
            raise Exception(f"HTTP error calling Azure OpenAI: {str(e)}. Error: {error_detail}")
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
            model_id=config.aws_model_id,
            thinking_mode=getattr(config, 'aws_thinking_mode', None)
        )

    elif config.provider_type == LLMProviderType.AZURE:
        if not all([config.azure_endpoint, config.azure_api_key, config.azure_deployment_name]):
            raise ValueError("Azure endpoint, api_key, and deployment_name are required for Azure OpenAI")
        return AzureOpenAIProvider(
            endpoint=config.azure_endpoint,
            api_key=config.azure_api_key,
            deployment_name=config.azure_deployment_name,
            api_version=config.azure_api_version or "2024-02-15-preview",
            reasoning_effort=getattr(config, 'azure_reasoning_effort', None)
        )

    else:
        raise ValueError(f"Unsupported provider type: {config.provider_type}")
