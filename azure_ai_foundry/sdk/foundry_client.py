"""
Azure AI Foundry Client
Provides interface to Azure AI Foundry endpoints for flow invocation
"""

import asyncio
import httpx
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class AzureAIFoundryClient:
    """
    Client for interacting with Azure AI Foundry deployed flows
    """

    def __init__(
        self,
        project_endpoint: str,
        api_key: str,
        timeout: int = 1800,
        api_version: str = "2024-07-01"
    ):
        """
        Initialize Azure AI Foundry client

        Args:
            project_endpoint: Azure AI Foundry project endpoint URL
            api_key: API key for authentication
            timeout: Request timeout in seconds (default: 30 minutes)
            api_version: API version (default: 2024-07-01)
        """
        self.project_endpoint = project_endpoint.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.api_version = api_version

        logger.info(f"Initialized Azure AI Foundry client: {self.project_endpoint}")

    async def invoke_flow(
        self,
        flow_name: str,
        inputs: Dict,
        timeout: Optional[int] = None
    ) -> Dict:
        """
        Invoke a deployed Azure AI Foundry flow

        Args:
            flow_name: Name of the deployed flow
            inputs: Flow input parameters as dictionary
            timeout: Optional timeout override (in seconds)

        Returns:
            Flow execution result dictionary

        Raises:
            HTTPError: If the API request fails
            TimeoutError: If the request times out

        Example:
            >>> client = AzureAIFoundryClient(endpoint="...", api_key="...")
            >>> result = await client.invoke_flow(
            ...     flow_name="dimension_analysis_flow",
            ...     inputs={
            ...         "survey_data": {...},
            ...         "dimension": "Data Privacy & Compliance",
            ...         "customer_code": "ACME001"
            ...     }
            ... )
            >>> print(result["final_report"])
        """
        # Use provided timeout or default
        request_timeout = timeout or self.timeout

        # Build flow endpoint URL
        flow_url = f"{self.project_endpoint}/flows/{flow_name}/invoke"

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
            "x-api-version": self.api_version
        }

        # Prepare payload
        payload = {
            "inputs": inputs,
            "parameters": {
                "timeout": request_timeout
            }
        }

        logger.info(f"Invoking flow '{flow_name}' with timeout={request_timeout}s")
        logger.debug(f"Flow inputs: {list(inputs.keys())}")

        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                response = await client.post(
                    flow_url,
                    json=payload,
                    headers=headers
                )

                # Check for errors
                if response.status_code != 200:
                    error_detail = self._parse_error_response(response)
                    logger.error(f"Flow invocation failed: {error_detail}")
                    raise httpx.HTTPStatusError(
                        f"Flow invocation failed: {error_detail}",
                        request=response.request,
                        response=response
                    )

                # Parse response
                result = response.json()
                logger.info(f"Flow '{flow_name}' completed successfully")
                logger.debug(f"Flow outputs: {list(result.get('outputs', {}).keys())}")

                return result

        except httpx.TimeoutException as e:
            logger.error(f"Flow '{flow_name}' timed out after {request_timeout}s")
            raise TimeoutError(f"Flow '{flow_name}' timed out after {request_timeout}s") from e

        except httpx.HTTPError as e:
            logger.error(f"HTTP error invoking flow '{flow_name}': {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error invoking flow '{flow_name}': {str(e)}")
            raise

    async def get_flow_status(self, flow_name: str, run_id: str) -> Dict:
        """
        Get status of a flow execution

        Args:
            flow_name: Name of the flow
            run_id: Execution run ID

        Returns:
            Status dictionary
        """
        status_url = f"{self.project_endpoint}/flows/{flow_name}/runs/{run_id}"

        headers = {
            "api-key": self.api_key,
            "x-api-version": self.api_version
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(status_url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def list_flows(self) -> list:
        """
        List all deployed flows in the project

        Returns:
            List of flow metadata dictionaries
        """
        list_url = f"{self.project_endpoint}/flows"

        headers = {
            "api-key": self.api_key,
            "x-api-version": self.api_version
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(list_url, headers=headers)
            response.raise_for_status()
            return response.json().get("flows", [])

    def _parse_error_response(self, response: httpx.Response) -> str:
        """Parse error response from API"""
        try:
            error_body = response.json()
            if isinstance(error_body, dict):
                return error_body.get("error", {}).get("message", response.text)
            return str(error_body)
        except Exception:
            return response.text[:500] if response.text else "Unknown error"

    async def test_connection(self) -> Dict:
        """
        Test connection to Azure AI Foundry

        Returns:
            Dictionary with connection status
        """
        try:
            flows = await self.list_flows()
            return {
                "status": "Success",
                "message": f"Connected to Azure AI Foundry ({len(flows)} flows available)",
                "flows": [f.get("name") for f in flows]
            }
        except Exception as e:
            return {
                "status": "Failed",
                "error": str(e)
            }


# For testing/development: Mock client
class MockAzureAIFoundryClient(AzureAIFoundryClient):
    """Mock client for testing without actual Azure AI Foundry deployment"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.warning("Using MOCK Azure AI Foundry client - for testing only!")

    async def invoke_flow(self, flow_name: str, inputs: Dict, timeout: Optional[int] = None) -> Dict:
        """Mock flow invocation"""
        logger.info(f"MOCK: Invoking flow '{flow_name}'")

        # Simulate delay
        await asyncio.sleep(2)

        # Return mock response based on flow
        if "dimension" in flow_name:
            return {
                "outputs": {
                    "final_report": f"# Mock Report for {inputs.get('dimension', 'Unknown')}\n\nThis is a mock report.",
                    "pdf_report": b"mock_pdf_bytes",
                    "metadata": {
                        "maturity_level": 3,
                        "quality_score": 8.5
                    }
                },
                "status": "Completed"
            }
        elif "overall" in flow_name:
            return {
                "outputs": {
                    "final_report": "# Mock Overall Report\n\nThis is a mock overall report.",
                    "pdf_report": b"mock_pdf_bytes",
                    "metadata": {
                        "avg_maturity_level": 3.2
                    }
                },
                "status": "Completed"
            }
        else:
            return {
                "outputs": {},
                "status": "Completed"
            }

    async def test_connection(self) -> Dict:
        """Mock connection test"""
        return {
            "status": "Success",
            "message": "Mock client - no actual connection",
            "flows": ["dimension_analysis_flow", "overall_synthesis_flow"]
        }


if __name__ == "__main__":
    # Test the client
    async def test_client():
        # Use mock client for testing
        client = MockAzureAIFoundryClient(
            project_endpoint="https://mock.api.azureml.ms",
            api_key="mock_api_key"
        )

        # Test connection
        conn_result = await client.test_connection()
        print(f"Connection test: {conn_result}")

        # Test flow invocation
        result = await client.invoke_flow(
            flow_name="dimension_analysis_flow",
            inputs={
                "survey_data": {"questions": []},
                "dimension": "Data Privacy & Compliance",
                "customer_code": "TEST001"
            }
        )
        print(f"Flow result: {result.get('status')}")

    asyncio.run(test_client())
