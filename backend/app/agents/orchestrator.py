"""
Agentic Workflow Orchestrator

Coordinates the execution of all agents in sequence:
1. Survey Parser Agent -> Parse survey data and compute statistics
2. Maturity Assessor Agent -> Evaluate maturity against standards using RAG
3. Report Generator Agent -> Create comprehensive 50+ page report
4. Self-Critic Agent -> Score report quality, trigger revision if needed
5. PDF Formatter Agent -> Convert to professional PDF (optional)

The orchestrator handles:
- Agent initialization
- Sequential execution with data flow
- Error handling and recovery
- Revision loops (if Self-Critic score < 8)
- Final output aggregation
"""

import logging
import time
from typing import Dict, List, Any, Optional
from .survey_parser import SurveyParserAgent
from .maturity_assessor import MaturityAssessorAgent
from .report_generator import ReportGeneratorAgent
from .self_critic import SelfCriticAgent
from .pdf_formatter import PDFFormatterAgent
from .base import AgentResult

logger = logging.getLogger(__name__)


class AgenticWorkflowOrchestrator:
    """
    Orchestrates the agentic workflow for survey analysis

    Manages the full pipeline from raw survey data to final PDF report,
    coordinating multiple specialized agents and ensuring quality standards.
    """

    def __init__(
        self,
        llm_provider,
        rag_service=None,
        enable_pdf: bool = False,
        enable_revision: bool = True,
        max_revisions: int = 1,
        quality_threshold: float = 8.0
    ):
        """
        Initialize orchestrator

        Args:
            llm_provider: LLM provider instance (from llm_providers.py)
            rag_service: RAG service instance (optional)
            enable_pdf: Whether to generate PDF output
            enable_revision: Whether to allow report revisions
            max_revisions: Maximum number of revision attempts
            quality_threshold: Minimum acceptable quality score (1-10)
        """
        self.llm_provider = llm_provider
        self.rag_service = rag_service
        self.enable_pdf = enable_pdf
        self.enable_revision = enable_revision
        self.max_revisions = max_revisions
        self.quality_threshold = quality_threshold

        # Initialize agents
        self.survey_parser = SurveyParserAgent(llm_provider)
        self.maturity_assessor = MaturityAssessorAgent(llm_provider, rag_service)
        self.report_generator = ReportGeneratorAgent(llm_provider)
        self.self_critic = SelfCriticAgent(llm_provider)
        self.pdf_formatter = PDFFormatterAgent(llm_provider)

        logger.info("AgenticWorkflowOrchestrator initialized")
        logger.info(f"Configuration: PDF={enable_pdf}, Revision={enable_revision}, "
                   f"MaxRevisions={max_revisions}, Threshold={quality_threshold}")

    async def execute_workflow(
        self,
        dimension: str,
        questions_data: List[Dict[str, Any]],
        customer_name: str = "Organization",
        customer_code: str = "ORG",
        pdf_output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete agentic workflow

        Args:
            dimension: Dimension name (e.g., "Data Privacy & Compliance")
            questions_data: List of question dicts with scores, comments, etc.
            customer_name: Customer organization name
            customer_code: Customer code
            pdf_output_path: Optional path for PDF output

        Returns:
            Dictionary with:
                - success: bool
                - workflow_results: Dict with results from each agent
                - final_report: The final approved report
                - execution_summary: Summary of execution
                - error: Optional error message
        """
        start_time = time.time()
        logger.info(f"{'='*60}")
        logger.info(f"Starting Agentic Workflow for {dimension}")
        logger.info(f"Customer: {customer_name} ({customer_code})")
        logger.info(f"{'='*60}")

        workflow_results = {
            "dimension": dimension,
            "customer_name": customer_name,
            "customer_code": customer_code,
            "agents_executed": [],
            "revision_count": 0
        }

        try:
            # STEP 1: Survey Parser Agent
            logger.info("[STEP 1] Executing Survey Parser Agent...")
            parser_result = await self.survey_parser.execute(
                dimension=dimension,
                questions_data=questions_data
            )
            workflow_results["agents_executed"].append("SurveyParserAgent")
            workflow_results["survey_parser"] = parser_result.model_dump()

            if not parser_result.success:
                return self._build_error_response(
                    "Survey Parser Agent failed",
                    parser_result.error,
                    workflow_results,
                    time.time() - start_time
                )

            survey_stats = parser_result.output
            logger.info(f"[STEP 1] ✓ Survey parsed: Avg score {survey_stats.get('overall', {}).get('avg_score')}/10")

            # STEP 2: Maturity Assessor Agent
            logger.info("[STEP 2] Executing Maturity Assessor Agent...")
            assessor_result = await self.maturity_assessor.execute(
                dimension=dimension,
                survey_stats=survey_stats,
                questions_data=questions_data
            )
            workflow_results["agents_executed"].append("MaturityAssessorAgent")
            workflow_results["maturity_assessor"] = assessor_result.model_dump()

            if not assessor_result.success:
                return self._build_error_response(
                    "Maturity Assessor Agent failed",
                    assessor_result.error,
                    workflow_results,
                    time.time() - start_time
                )

            maturity_assessment = assessor_result.output
            logger.info(f"[STEP 2] ✓ Maturity assessed: Composite score {maturity_assessment.get('composite_score')}/5")

            # STEP 3: Report Generator Agent
            logger.info("[STEP 3] Executing Report Generator Agent...")
            generator_result = await self.report_generator.execute(
                dimension=dimension,
                survey_stats=survey_stats,
                maturity_assessment=maturity_assessment,
                questions_data=questions_data,
                customer_name=customer_name
            )
            workflow_results["agents_executed"].append("ReportGeneratorAgent")
            workflow_results["report_generator"] = generator_result.model_dump()

            if not generator_result.success:
                return self._build_error_response(
                    "Report Generator Agent failed",
                    generator_result.error,
                    workflow_results,
                    time.time() - start_time
                )

            generated_report = generator_result.output
            logger.info(f"[STEP 3] ✓ Report generated: {len(generated_report.get('sections', []))} sections")

            # STEP 4: Self-Critic Agent (with optional revision loop)
            logger.info("[STEP 4] Executing Self-Critic Agent...")
            final_report = generated_report
            revision_count = 0

            while revision_count <= self.max_revisions:
                critic_result = await self.self_critic.execute(
                    dimension=dimension,
                    draft_report=final_report,
                    threshold=self.quality_threshold
                )
                workflow_results["agents_executed"].append(f"SelfCriticAgent (Attempt {revision_count + 1})")
                workflow_results[f"self_critic_attempt_{revision_count}"] = critic_result.model_dump()

                if not critic_result.success:
                    logger.warning(f"[STEP 4] Self-Critic failed: {critic_result.error}")
                    break

                critique_scores = critic_result.output
                avg_score = critique_scores.get('average', 0)
                needs_revision = critique_scores.get('needs_revision', False)

                logger.info(f"[STEP 4] Quality score: {avg_score:.1f}/10")

                if not needs_revision or not self.enable_revision:
                    logger.info(f"[STEP 4] ✓ Report approved (score: {avg_score:.1f}/10)")
                    workflow_results["final_quality_score"] = avg_score
                    workflow_results["quality_approved"] = True
                    break

                # Revision needed
                revision_count += 1
                workflow_results["revision_count"] = revision_count

                if revision_count > self.max_revisions:
                    logger.warning(f"[STEP 4] Max revisions ({self.max_revisions}) reached, accepting current report")
                    workflow_results["quality_approved"] = False
                    workflow_results["final_quality_score"] = avg_score
                    break

                logger.info(f"[STEP 4] ⚠ Revision needed (score: {avg_score:.1f}/10, attempt {revision_count}/{self.max_revisions})")
                logger.info(f"[STEP 4] Revision notes: {critique_scores.get('revision_notes', 'None')}")

                # TODO: Implement revision logic (regenerate report with feedback)
                # For now, we'll accept the report after critique
                logger.info(f"[STEP 4] Note: Automatic revision not yet implemented, accepting report")
                workflow_results["quality_approved"] = False
                workflow_results["final_quality_score"] = avg_score
                break

            # STEP 5: PDF Formatter Agent (optional)
            if self.enable_pdf and pdf_output_path:
                logger.info("[STEP 5] Executing PDF Formatter Agent...")

                # Convert report to markdown
                markdown_content = self._convert_report_to_markdown(
                    dimension, final_report, customer_name
                )

                pdf_result = await self.pdf_formatter.execute(
                    dimension=dimension,
                    markdown_content=markdown_content,
                    report_data=final_report,
                    output_path=pdf_output_path,
                    customer_name=customer_name
                )
                workflow_results["agents_executed"].append("PDFFormatterAgent")
                workflow_results["pdf_formatter"] = pdf_result.model_dump()

                if pdf_result.success:
                    pdf_output = pdf_result.output
                    if pdf_output.get('status') == 'success':
                        logger.info(f"[STEP 5] ✓ PDF generated: {pdf_output.get('pdf_path')}")
                    else:
                        logger.info(f"[STEP 5] PDF skipped: {pdf_output.get('error_details')}")
                else:
                    logger.warning(f"[STEP 5] PDF generation failed: {pdf_result.error}")

            # Workflow complete
            execution_time = time.time() - start_time
            logger.info(f"{'='*60}")
            logger.info(f"Workflow Complete for {dimension}")
            logger.info(f"Total execution time: {execution_time:.2f}s")
            logger.info(f"Agents executed: {len(workflow_results['agents_executed'])}")
            logger.info(f"{'='*60}")

            return {
                "success": True,
                "workflow_results": workflow_results,
                "final_report": final_report,
                "execution_summary": {
                    "total_time_seconds": round(execution_time, 2),
                    "agents_executed": len(workflow_results['agents_executed']),
                    "revision_count": revision_count,
                    "final_quality_score": workflow_results.get('final_quality_score'),
                    "quality_approved": workflow_results.get('quality_approved', False)
                }
            }

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return self._build_error_response(
                "Workflow execution error",
                str(e),
                workflow_results,
                time.time() - start_time
            )

    def _convert_report_to_markdown(
        self,
        dimension: str,
        report: Dict,
        customer_name: str
    ) -> str:
        """Convert structured report to Markdown format"""
        markdown = f"""# {dimension} Report

**Customer:** {customer_name}
**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

{report.get('executive_summary', '')}

---

"""
        # Add sections
        for section in report.get('sections', []):
            markdown += section.get('content', '') + "\n\n---\n\n"

        # Add action items
        markdown += "## Prioritized Action Items\n\n"
        markdown += "| Priority | Action | Owner | Timeline | Expected Outcome |\n"
        markdown += "|----------|--------|-------|----------|------------------|\n"
        for item in report.get('action_items', []):
            markdown += f"| {item.get('priority', 'N/A')} | {item.get('action', 'N/A')} | {item.get('owner', 'N/A')} | {item.get('timeline', 'N/A')} | {item.get('expected_outcome', 'N/A')} |\n"

        markdown += "\n---\n\n"

        # Add roadmap
        markdown += "## Strategic Roadmap\n\n"
        roadmap = report.get('roadmap', {})
        for phase, items in roadmap.items():
            markdown += f"### {phase}\n\n"
            for item in items:
                markdown += f"- **{item.get('action', 'N/A')}** ({item.get('priority', 'N/A')} priority)\n"
                markdown += f"  - Owner: {item.get('owner', 'N/A')}\n"
                markdown += f"  - Timeline: {item.get('timeline', 'N/A')}\n"
                markdown += f"  - Expected Outcome: {item.get('expected_outcome', 'N/A')}\n\n"

        return markdown

    def _build_error_response(
        self,
        error_stage: str,
        error_message: str,
        workflow_results: Dict,
        execution_time: float
    ) -> Dict[str, Any]:
        """Build error response"""
        logger.error(f"Workflow failed at {error_stage}: {error_message}")
        return {
            "success": False,
            "error": f"{error_stage}: {error_message}",
            "workflow_results": workflow_results,
            "final_report": None,
            "execution_summary": {
                "total_time_seconds": round(execution_time, 2),
                "agents_executed": len(workflow_results.get('agents_executed', [])),
                "failed_at": error_stage
            }
        }
