"""
Agentic Report Service

Integration layer between the existing EnTrust system and the new agentic workflow.
Provides a high-level API for generating reports using the agentic approach.
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from ..llm_providers import get_llm_provider
from ..rag import get_rag_service
from .orchestrator import AgenticWorkflowOrchestrator

logger = logging.getLogger(__name__)


class AgenticReportService:
    """
    Service layer for agentic report generation

    Bridges the gap between existing EnTrust endpoints and the new agentic workflow.
    Handles LLM provider initialization, RAG service integration, and result formatting.
    """

    @staticmethod
    async def generate_agentic_report(
        dimension: str,
        customer_code: str,
        customer_name: str,
        questions_data: List[Dict[str, Any]],
        llm_config: Any,
        enable_pdf: bool = False,
        pdf_output_path: Optional[str] = None,
        enable_revision: bool = True,
        max_revisions: int = 1,
        quality_threshold: float = 8.0
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report using the agentic workflow

        Args:
            dimension: Dimension name (e.g., "Data Privacy & Compliance")
            customer_code: Customer code
            customer_name: Customer organization name
            questions_data: Survey data (list of question dicts with scores, comments, etc.)
            llm_config: LLM configuration from database
            enable_pdf: Whether to generate PDF output
            pdf_output_path: Path for PDF output (if enable_pdf=True)
            enable_revision: Whether to allow Self-Critic revisions
            max_revisions: Maximum number of revision attempts
            quality_threshold: Minimum acceptable quality score (1-10)

        Returns:
            Dictionary with workflow results, final report, and execution summary
        """
        logger.info(f"{'='*60}")
        logger.info(f"AgenticReportService: Generating report for {dimension}")
        logger.info(f"Customer: {customer_name} ({customer_code})")
        logger.info(f"Questions: {len(questions_data)}")
        logger.info(f"{'='*60}")

        try:
            # Step 1: Initialize LLM provider
            logger.info("[INIT] Initializing LLM provider...")
            llm_provider = get_llm_provider(llm_config)

            # Step 2: Initialize RAG service
            logger.info("[INIT] Initializing RAG service...")
            try:
                rag_service = get_rag_service()
                if not rag_service.enabled:
                    logger.warning("[INIT] RAG service not enabled, proceeding without RAG")
                    rag_service = None
            except Exception as e:
                logger.warning(f"[INIT] RAG service initialization failed: {e}, proceeding without RAG")
                rag_service = None

            # Step 3: Initialize orchestrator
            logger.info("[INIT] Initializing agentic workflow orchestrator...")
            orchestrator = AgenticWorkflowOrchestrator(
                llm_provider=llm_provider,
                rag_service=rag_service,
                enable_pdf=enable_pdf,
                enable_revision=enable_revision,
                max_revisions=max_revisions,
                quality_threshold=quality_threshold
            )

            # Step 4: Execute workflow
            logger.info("[EXECUTE] Starting agentic workflow execution...")
            result = await orchestrator.execute_workflow(
                dimension=dimension,
                questions_data=questions_data,
                customer_name=customer_name,
                customer_code=customer_code,
                pdf_output_path=pdf_output_path
            )

            if result.get('success'):
                logger.info("[SUCCESS] Agentic workflow completed successfully")
            else:
                logger.error(f"[ERROR] Agentic workflow failed: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"[ERROR] AgenticReportService failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"AgenticReportService error: {str(e)}",
                "workflow_results": {},
                "final_report": None,
                "execution_summary": {
                    "total_time_seconds": 0,
                    "agents_executed": 0,
                    "failed_at": "Service initialization"
                }
            }

    @staticmethod
    def format_agentic_report_for_api(
        workflow_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format agentic workflow result for API response

        Transforms the internal workflow result into a format compatible
        with the existing EnTrust report API structure.

        Args:
            workflow_result: Output from AgenticWorkflowOrchestrator

        Returns:
            API-compatible report structure
        """
        if not workflow_result.get('success'):
            return {
                "success": False,
                "error": workflow_result.get('error', 'Unknown error'),
                "agentic_workflow": True
            }

        final_report = workflow_result.get('final_report', {})
        execution_summary = workflow_result.get('execution_summary', {})

        # Extract key data from the agentic report
        return {
            "success": True,
            "agentic_workflow": True,
            "dimension": final_report.get('dimension'),
            "executive_summary": final_report.get('executive_summary'),
            "sections": final_report.get('sections', []),
            "action_items": final_report.get('action_items', []),
            "roadmap": final_report.get('roadmap', {}),
            "visuals": final_report.get('visuals', {}),
            "metadata": final_report.get('metadata', {}),
            "quality_score": execution_summary.get('final_quality_score'),
            "quality_approved": execution_summary.get('quality_approved'),
            "revision_count": execution_summary.get('revision_count', 0),
            "execution_time_seconds": execution_summary.get('total_time_seconds'),
            "agents_executed": execution_summary.get('agents_executed')
        }

    @staticmethod
    def convert_to_legacy_format(
        workflow_result: Dict[str, Any],
        questions_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Convert agentic report to legacy EnTrust report format

        This allows the agentic workflow to be used as a drop-in replacement
        for the existing report generation while maintaining backward compatibility.

        Args:
            workflow_result: Output from AgenticWorkflowOrchestrator
            questions_data: Original survey data

        Returns:
            Report in legacy format (compatible with existing UI)
        """
        if not workflow_result.get('success'):
            return {
                "success": False,
                "error": workflow_result.get('error')
            }

        final_report = workflow_result.get('final_report', {})
        workflow_results = workflow_result.get('workflow_results', {})

        # Extract survey stats from workflow
        survey_parser_result = workflow_results.get('survey_parser', {})
        survey_stats = survey_parser_result.get('output', {})

        # Extract maturity assessment from workflow
        maturity_assessor_result = workflow_results.get('maturity_assessor', {})
        maturity_assessment = maturity_assessor_result.get('output', {})

        # Build legacy format
        return {
            "success": True,
            "dimension": final_report.get('dimension'),
            "overall_metrics": survey_stats.get('overall', {}),
            "category_analysis": survey_stats.get('by_category', {}),
            "process_analysis": survey_stats.get('by_process', {}),
            "lifecycle_analysis": survey_stats.get('by_lifecycle', {}),
            "dimension_llm_analysis": final_report.get('executive_summary', ''),
            "questions": questions_data,
            "comment_insights": {
                "total_comments": survey_stats.get('overall', {}).get('total_comments', 0),
                "llm_analysis": "\n".join(survey_stats.get('comment_themes', []))
            },
            # Agentic-specific additions
            "agentic_report": True,
            "agentic_sections": final_report.get('sections', []),
            "action_items": final_report.get('action_items', []),
            "roadmap": final_report.get('roadmap', {}),
            "maturity_assessment": maturity_assessment,
            "quality_score": workflow_result.get('execution_summary', {}).get('final_quality_score'),
            "visuals": final_report.get('visuals', {})
        }
