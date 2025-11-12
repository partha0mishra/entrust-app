"""
Self-Critic Agent

Reviews and scores draft reports on clarity, actionability, standards alignment,
and completeness. Revises reports if average score < 8/10.
"""

import json
import time
from typing import Dict, Any
from .base import AgentBase, AgentResult, CritiqueScores


class SelfCriticAgent(AgentBase):
    """
    Quality assurance agent that critiques and revises reports

    Capabilities:
    - Score report on multiple dimensions (1-10)
    - Identify specific improvement areas
    - Generate revision notes if score < 8
    - Optionally trigger report revision
    """

    def __init__(self, llm_provider=None):
        super().__init__("SelfCriticAgent", llm_provider)

    async def execute(
        self,
        dimension: str,
        draft_report: Dict[str, Any],
        threshold: float = 8.0
    ) -> AgentResult:
        """
        Critique draft report and assess quality

        Args:
            dimension: Dimension name
            draft_report: Output from ReportGeneratorAgent
            threshold: Minimum acceptable average score (default: 8.0)

        Returns:
            AgentResult with critique scores and revision notes
        """
        start_time = time.time()
        self.log_execution("START", f"Critiquing report for {dimension}")

        try:
            # Step 1: Generate critique
            self.log_execution("STEP_1", "Scoring report quality")
            scores = await self._score_report(dimension, draft_report)

            # Step 2: Determine if revision needed
            self.log_execution("STEP_2", f"Average score: {scores.average:.1f}/10")
            needs_revision = scores.average < threshold

            if needs_revision:
                self.log_execution("REVISION", f"Score below threshold ({threshold}), generating revision notes")
                revision_notes = await self._generate_revision_notes(
                    dimension, draft_report, scores
                )
                scores.revision_notes = revision_notes
            else:
                self.log_execution("APPROVED", f"Report meets quality standards")
                scores.revision_notes = None

            execution_time = time.time() - start_time
            self.log_execution("COMPLETE", f"Critique completed in {execution_time:.2f}s")

            return AgentResult(
                success=True,
                agent_name=self.agent_name,
                output=scores.model_dump(),
                execution_time_seconds=execution_time
            )

        except Exception as e:
            self.logger.error(f"Error in SelfCriticAgent: {e}", exc_info=True)
            return AgentResult(
                success=False,
                agent_name=self.agent_name,
                output={},
                error=str(e),
                execution_time_seconds=time.time() - start_time
            )

    async def _score_report(
        self,
        dimension: str,
        draft_report: Dict
    ) -> CritiqueScores:
        """Score report on multiple dimensions"""
        system_prompt = self.get_system_prompt()
        user_prompt = self.get_user_prompt(dimension, draft_report)

        response = await self.call_llm(system_prompt, user_prompt, max_tokens=1000)

        # Parse scores from response
        return self._parse_critique_response(response)

    def _parse_critique_response(self, response: str) -> CritiqueScores:
        """Parse LLM critique response into CritiqueScores"""
        # Try to parse JSON
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                data = json.loads(json_str)

                clarity = int(data.get('clarity', 7))
                actionability = int(data.get('actionability', 7))
                standards_alignment = int(data.get('standards_alignment', 7))
                completeness = int(data.get('completeness', 7))

                average = (clarity + actionability + standards_alignment + completeness) / 4
                needs_revision = average < 8.0

                return CritiqueScores(
                    clarity=clarity,
                    actionability=actionability,
                    standards_alignment=standards_alignment,
                    completeness=completeness,
                    average=round(average, 2),
                    needs_revision=needs_revision
                )
        except Exception as e:
            self.logger.warning(f"JSON parsing failed: {e}, using text parsing")

        # Fallback: Parse text response
        scores = {"clarity": 7, "actionability": 7, "standards_alignment": 7, "completeness": 7}

        for line in response.split('\n'):
            line_lower = line.lower()
            for key in scores.keys():
                if key in line_lower or key.replace('_', ' ') in line_lower:
                    # Extract number
                    parts = line.split(':')
                    if len(parts) > 1:
                        try:
                            # Look for X/10 pattern
                            score_part = parts[1].strip()
                            if '/10' in score_part:
                                score_str = score_part.split('/10')[0].strip()
                                scores[key] = int(score_str)
                            else:
                                # Look for standalone number
                                import re
                                numbers = re.findall(r'\d+', score_part)
                                if numbers:
                                    scores[key] = int(numbers[0])
                        except:
                            pass

        average = sum(scores.values()) / len(scores)
        needs_revision = average < 8.0

        return CritiqueScores(
            clarity=scores['clarity'],
            actionability=scores['actionability'],
            standards_alignment=scores['standards_alignment'],
            completeness=scores['completeness'],
            average=round(average, 2),
            needs_revision=needs_revision
        )

    async def _generate_revision_notes(
        self,
        dimension: str,
        draft_report: Dict,
        scores: CritiqueScores
    ) -> str:
        """Generate specific revision recommendations"""
        system_prompt = """You are a quality assurance expert providing revision guidance.
Identify specific improvements needed to raise report quality above 8/10.
Be concrete and actionable.
Output as a bulleted list of 3-5 revision recommendations."""

        user_prompt = f"""The report for {dimension} scored {scores.average:.1f}/10.

Score Breakdown:
- Clarity: {scores.clarity}/10
- Actionability: {scores.actionability}/10
- Standards Alignment: {scores.standards_alignment}/10
- Completeness: {scores.completeness}/10

Provide specific revision recommendations to improve these scores.
Focus on the lowest-scoring areas."""

        response = await self.call_llm(system_prompt, user_prompt, max_tokens=500)
        return response

    def get_system_prompt(self) -> str:
        """System prompt for report critique"""
        return """You are a quality assurance expert reviewing a data management report.
Score the report on a 1-10 scale across four dimensions:

1. **Clarity** (1-10): Is the report well-structured, easy to understand, and logically organized?
2. **Actionability** (1-10): Does it provide specific, implementable recommendations with clear ownership and timelines?
3. **Standards Alignment** (1-10): Does it properly reference industry frameworks (GDPR, NIST, DAMA-DMBOK, etc.) and ground analysis in best practices?
4. **Completeness** (1-10): Does it cover all required sections with sufficient depth and detail?

Output your assessment as JSON:
```json
{
  "clarity": 8,
  "actionability": 7,
  "standards_alignment": 9,
  "completeness": 8
}
```"""

    def get_user_prompt(self, dimension: str, draft_report: Dict) -> str:
        """User prompt for report critique"""
        # Extract key sections for review
        exec_summary = draft_report.get('executive_summary', '')[:500]
        action_items_count = len(draft_report.get('action_items', []))
        sections_count = len(draft_report.get('sections', []))
        roadmap_phases = len(draft_report.get('roadmap', {}))

        return f"""Review the following report for {dimension}:

**Executive Summary (excerpt):**
{exec_summary}

**Report Structure:**
- Number of sections: {sections_count}
- Number of action items: {action_items_count}
- Roadmap phases: {roadmap_phases}

**Metadata:**
{json.dumps(draft_report.get('metadata', {}), indent=2)}

Score this report on clarity, actionability, standards alignment, and completeness (1-10 each).
Output as JSON (structure provided in system prompt)."""
