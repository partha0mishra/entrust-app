"""
Flow Executor
High-level wrapper for executing Azure AI Foundry flows from entrust-app
"""

from typing import Dict, List, Optional
import logging
from .foundry_client import AzureAIFoundryClient

logger = logging.getLogger(__name__)


class FlowExecutor:
    """
    Executes Azure AI Foundry flows for survey analysis
    """

    def __init__(self, foundry_client: AzureAIFoundryClient):
        """
        Initialize flow executor

        Args:
            foundry_client: Initialized AzureAIFoundryClient instance
        """
        self.client = foundry_client
        logger.info("Flow executor initialized")

    async def execute_dimension_analysis(
        self,
        survey_data: Dict,
        dimension: str,
        customer_code: str,
        customer_name: str,
        force_regenerate: bool = False
    ) -> Dict:
        """
        Execute dimension analysis flow

        Args:
            survey_data: Survey data with questions, scores, comments
            dimension: Dimension name (e.g., "Data Privacy & Compliance")
            customer_code: Customer identifier
            customer_name: Customer organization name
            force_regenerate: Skip cached results

        Returns:
            Dictionary with final_report, pdf_report, metadata

        Example:
            >>> executor = FlowExecutor(client)
            >>> result = await executor.execute_dimension_analysis(
            ...     survey_data={...},
            ...     dimension="Data Privacy & Compliance",
            ...     customer_code="ACME001",
            ...     customer_name="Acme Corp"
            ... )
            >>> print(result["final_report"])
        """
        logger.info(f"Executing dimension analysis: {dimension} for {customer_code}")

        try:
            # Invoke dimension analysis flow
            result = await self.client.invoke_flow(
                flow_name="dimension_analysis_flow",
                inputs={
                    "survey_data": survey_data,
                    "dimension": dimension,
                    "customer_code": customer_code,
                    "customer_name": customer_name,
                    "force_regenerate": force_regenerate
                },
                timeout=1800  # 30 minutes
            )

            # Extract outputs
            outputs = result.get("outputs", {})

            return {
                "success": True,
                "final_report": outputs.get("final_report"),
                "pdf_report": outputs.get("pdf_report"),
                "metadata": outputs.get("metadata", {}),
                "rag_context": outputs.get("rag_context")
            }

        except Exception as e:
            logger.error(f"Dimension analysis failed for {dimension}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "final_report": None,
                "metadata": {}
            }

    async def execute_overall_synthesis(
        self,
        dimension_reports: List[Dict],
        customer_code: str,
        customer_name: str,
        survey_metadata: Dict
    ) -> Dict:
        """
        Execute overall synthesis flow

        Args:
            dimension_reports: List of dimension report dictionaries
            customer_code: Customer identifier
            customer_name: Customer organization name
            survey_metadata: Survey metadata (dates, participants, etc.)

        Returns:
            Dictionary with final_report, pdf_report, executive_summary, metadata

        Example:
            >>> result = await executor.execute_overall_synthesis(
            ...     dimension_reports=[...],
            ...     customer_code="ACME001",
            ...     customer_name="Acme Corp",
            ...     survey_metadata={...}
            ... )
        """
        logger.info(f"Executing overall synthesis for {customer_code}")

        try:
            # Invoke overall synthesis flow
            result = await self.client.invoke_flow(
                flow_name="overall_synthesis_flow",
                inputs={
                    "dimension_reports": dimension_reports,
                    "customer_code": customer_code,
                    "customer_name": customer_name,
                    "survey_metadata": survey_metadata
                },
                timeout=1200  # 20 minutes
            )

            # Extract outputs
            outputs = result.get("outputs", {})

            return {
                "success": True,
                "final_report": outputs.get("final_report"),
                "pdf_report": outputs.get("pdf_report"),
                "executive_summary": outputs.get("executive_summary"),
                "metadata": outputs.get("metadata", {})
            }

        except Exception as e:
            logger.error(f"Overall synthesis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "final_report": None,
                "metadata": {}
            }

    async def execute_full_survey_analysis(
        self,
        survey_id: int,
        customer_id: int,
        force_regenerate: bool = False
    ) -> Dict:
        """
        Execute complete survey analysis (all dimensions + overall)
        using the orchestrator flow

        Args:
            survey_id: Survey database ID
            customer_id: Customer database ID
            force_regenerate: Skip cached results

        Returns:
            Dictionary with dimension_reports, overall_report, status

        Example:
            >>> result = await executor.execute_full_survey_analysis(
            ...     survey_id=1,
            ...     customer_id=101
            ... )
        """
        logger.info(f"Executing full survey analysis: survey_id={survey_id}, customer_id={customer_id}")

        try:
            # Invoke orchestrator flow
            result = await self.client.invoke_flow(
                flow_name="orchestrator_flow",
                inputs={
                    "survey_id": survey_id,
                    "customer_id": customer_id,
                    "force_regenerate": force_regenerate
                },
                timeout=3600  # 60 minutes
            )

            # Extract outputs
            outputs = result.get("outputs", {})

            return {
                "success": True,
                "dimension_reports": outputs.get("dimension_reports", []),
                "overall_report": outputs.get("overall_report", {}),
                "status": outputs.get("status", {}),
                "execution_time": outputs.get("status", {}).get("execution_time")
            }

        except Exception as e:
            logger.error(f"Full survey analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "dimension_reports": [],
                "overall_report": {}
            }


if __name__ == "__main__":
    # Test flow executor
    import asyncio
    from .foundry_client import MockAzureAIFoundryClient

    async def test_executor():
        # Use mock client
        client = MockAzureAIFoundryClient(
            project_endpoint="https://mock.api.azureml.ms",
            api_key="mock_key"
        )

        executor = FlowExecutor(client)

        # Test dimension analysis
        result = await executor.execute_dimension_analysis(
            survey_data={"questions": []},
            dimension="Data Privacy & Compliance",
            customer_code="TEST001",
            customer_name="Test Corp"
        )

        print(f"Dimension analysis result: {result['success']}")

    asyncio.run(test_executor())
