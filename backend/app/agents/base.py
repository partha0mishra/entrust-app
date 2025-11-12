"""
Base Agent Classes and JSON Schemas

Defines the base architecture for all agents in the agentic workflow.
Each agent follows SOLID principles with clear responsibilities and JSON schemas.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentResult(BaseModel):
    """Standard result format for all agents"""
    success: bool
    agent_name: str
    output: Dict[str, Any]
    error: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class AgentBase:
    """
    Base class for all agents in the agentic workflow

    Each agent must implement:
    - execute(): Main execution logic
    - get_prompt(): Return the LLM prompt for this agent
    - parse_output(): Parse LLM output into structured format
    """

    def __init__(self, agent_name: str, llm_provider=None):
        """
        Initialize agent

        Args:
            agent_name: Name of the agent
            llm_provider: LLM provider instance (from llm_providers.py)
        """
        self.agent_name = agent_name
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")

    async def execute(self, **kwargs) -> AgentResult:
        """
        Execute the agent's task

        Args:
            **kwargs: Agent-specific input parameters

        Returns:
            AgentResult with success status and output
        """
        raise NotImplementedError("Subclasses must implement execute()")

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        raise NotImplementedError("Subclasses must implement get_system_prompt()")

    def get_user_prompt(self, **kwargs) -> str:
        """Get the user prompt for this agent"""
        raise NotImplementedError("Subclasses must implement get_user_prompt()")

    async def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Call LLM with prompts

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            max_tokens: Optional max tokens

        Returns:
            LLM response text
        """
        if not self.llm_provider:
            raise ValueError("LLM provider not initialized")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Use provider's call_llm method
        return await self.llm_provider.call_llm(messages, max_tokens or 8000)

    def log_execution(self, stage: str, message: str):
        """Log execution progress"""
        self.logger.info(f"[{self.agent_name}] {stage}: {message}")


# JSON Schemas for Agent Communication

class SurveyStats(BaseModel):
    """Statistics computed by Survey Parser Agent"""
    overall: Dict[str, Any] = Field(description="Overall statistics (avg_score, response_rate, etc.)")
    by_category: Dict[str, Dict[str, Any]] = Field(description="Statistics by category")
    by_process: Dict[str, Dict[str, Any]] = Field(description="Statistics by process")
    by_lifecycle: Dict[str, Dict[str, Any]] = Field(description="Statistics by lifecycle stage")
    comment_themes: List[str] = Field(description="Top comment themes extracted")
    score_distribution: Dict[str, int] = Field(description="Distribution of scores")


class MaturityLevel(BaseModel):
    """Maturity level assessed by Maturity Assessor Agent"""
    framework: str = Field(description="Framework name (e.g., DAMA-DMBOK, NIST, ISO 8000)")
    current_level: str = Field(description="Current maturity level (e.g., Initial, Defined, Managed)")
    score: float = Field(description="Maturity score (1-5)", ge=1, le=5)
    gaps: List[str] = Field(description="List of maturity gaps")
    best_practices: List[str] = Field(description="Best practices from framework")
    evidence_questions: List[int] = Field(description="Question IDs providing evidence")


class MaturityAssessment(BaseModel):
    """Complete maturity assessment"""
    dimension: str
    composite_score: float = Field(description="Overall maturity score (1-5)", ge=1, le=5)
    maturity_levels: List[MaturityLevel] = Field(description="Maturity by framework")
    priority_gaps: List[Dict[str, Any]] = Field(description="Top 5 prioritized gaps")
    rag_context_used: str = Field(description="RAG context retrieved from ChromaDB")


class ReportSection(BaseModel):
    """Individual report section"""
    section_id: str = Field(description="Unique section identifier")
    title: str
    content: str = Field(description="Markdown content")
    subsections: Optional[List['ReportSection']] = None


class GeneratedReport(BaseModel):
    """Complete report generated by Report Generator Agent"""
    dimension: str
    executive_summary: str = Field(description="Executive summary (1-2 pages)")
    sections: List[ReportSection] = Field(description="Report sections")
    action_items: List[Dict[str, Any]] = Field(description="Prioritized action items")
    roadmap: Dict[str, List[Dict[str, Any]]] = Field(description="6-12 month roadmap by phase")
    visuals: Dict[str, Any] = Field(description="Graph and word cloud data")
    metadata: Dict[str, Any] = Field(description="Report metadata")


class CritiqueScores(BaseModel):
    """Scores assigned by Self-Critic Agent"""
    clarity: int = Field(description="Clarity score (1-10)", ge=1, le=10)
    actionability: int = Field(description="Actionability score (1-10)", ge=1, le=10)
    standards_alignment: int = Field(description="Standards alignment score (1-10)", ge=1, le=10)
    completeness: int = Field(description="Completeness score (1-10)", ge=1, le=10)
    average: float = Field(description="Average of all scores")
    needs_revision: bool = Field(description="True if average < 8")
    revision_notes: Optional[str] = Field(description="Notes on what to revise")


class PDFOutput(BaseModel):
    """Output from PDF Formatter Agent"""
    pdf_path: str = Field(description="Path to generated PDF file")
    status: str = Field(description="Status: success or error")
    page_count: Optional[int] = None
    file_size_mb: Optional[float] = None
    error_details: Optional[str] = None
