"""
Maturity Assessor Agent

Evaluates organizational maturity against industry standards using ChromaDB RAG store.
Compares survey results to frameworks like GDPR, DAMA-DMBOK, NIST, ISO 8000, etc.
"""

import json
import time
from typing import Dict, List, Any
from .base import AgentBase, AgentResult, MaturityAssessment, MaturityLevel


# Dimension to Framework mapping
DIMENSION_FRAMEWORKS = {
    "Data Privacy & Compliance": [
        "GDPR",
        "CCPA",
        "NIST Privacy Framework",
        "ISO 27701"
    ],
    "Data Quality": [
        "ISO 8000",
        "TDQM (Total Data Quality Management)",
        "DAMA-DMBOK Quality",
        "Six Sigma Data Quality"
    ],
    "Data Governance & Management": [
        "DAMA-DMBOK",
        "COBIT",
        "Gartner EIM Maturity Model",
        "CMMI Data Management Maturity (DMM)"
    ],
    "Data Security & Access": [
        "NIST 800-53",
        "ISO 27001",
        "CIS Controls",
        "Zero Trust Architecture"
    ],
    "Data Lineage & Traceability": [
        "DAMA-DMBOK Lineage",
        "W3C PROV-DM",
        "Data Provenance Standards",
        "Audit Trail Requirements"
    ],
    "Metadata & Documentation": [
        "Dublin Core",
        "DAMA-DMBOK Metadata",
        "ISO 11179",
        "Data Catalog Standards"
    ],
    "Data Value & Lifecycle Management": [
        "DAMA-DMBOK Lifecycle",
        "Information Lifecycle Management (ILM)",
        "Data Valuation Frameworks",
        "ROI-driven Data Management"
    ],
    "Data Ethics & Bias": [
        "IEEE Ethically Aligned Design",
        "AI Ethics Guidelines",
        "Algorithmic Fairness Standards",
        "Responsible AI Frameworks"
    ]
}

# Maturity level definitions (1-5 scale)
MATURITY_LEVELS = {
    1: "Initial/Ad-hoc",
    2: "Repeatable/Reactive",
    3: "Defined/Proactive",
    4: "Managed/Quantified",
    5: "Optimized/Continuous Improvement"
}


class MaturityAssessorAgent(AgentBase):
    """
    Assesses organizational maturity against industry standards

    Capabilities:
    - Query ChromaDB for relevant standards
    - Evaluate maturity across multiple frameworks
    - Identify maturity gaps with evidence from survey
    - Map to best practices
    - Assign maturity scores (1-5) per framework
    """

    def __init__(self, llm_provider=None, rag_service=None):
        super().__init__("MaturityAssessorAgent", llm_provider)
        self.rag_service = rag_service

    async def execute(
        self,
        dimension: str,
        survey_stats: Dict[str, Any],
        questions_data: List[Dict[str, Any]]
    ) -> AgentResult:
        """
        Assess organizational maturity against standards

        Args:
            dimension: Dimension name
            survey_stats: Output from SurveyParserAgent
            questions_data: Original survey data for evidence

        Returns:
            AgentResult with maturity assessment
        """
        start_time = time.time()
        self.log_execution("START", f"Assessing maturity for {dimension}")

        try:
            # Step 1: Get relevant frameworks for this dimension
            self.log_execution("STEP_1", "Identifying relevant frameworks")
            frameworks = self._get_relevant_frameworks(dimension)

            # Step 2: Query RAG for standards context
            self.log_execution("STEP_2", "Querying ChromaDB for standards")
            rag_context = await self._get_rag_context(dimension, survey_stats)

            # Step 3: Assess maturity for each framework
            self.log_execution("STEP_3", "Assessing maturity per framework")
            maturity_levels = await self._assess_frameworks(
                dimension,
                frameworks,
                survey_stats,
                questions_data,
                rag_context
            )

            # Step 4: Compute composite maturity score
            self.log_execution("STEP_4", "Computing composite maturity score")
            composite_score = self._compute_composite_score(maturity_levels)

            # Step 5: Identify priority gaps
            self.log_execution("STEP_5", "Identifying priority gaps")
            priority_gaps = await self._identify_priority_gaps(
                dimension,
                maturity_levels,
                survey_stats,
                rag_context
            )

            # Build assessment
            assessment = MaturityAssessment(
                dimension=dimension,
                composite_score=composite_score,
                maturity_levels=maturity_levels,
                priority_gaps=priority_gaps,
                rag_context_used=rag_context
            )

            execution_time = time.time() - start_time
            self.log_execution("COMPLETE", f"Assessed maturity in {execution_time:.2f}s")

            return AgentResult(
                success=True,
                agent_name=self.agent_name,
                output=assessment.model_dump(),
                execution_time_seconds=execution_time
            )

        except Exception as e:
            self.logger.error(f"Error in MaturityAssessorAgent: {e}", exc_info=True)
            return AgentResult(
                success=False,
                agent_name=self.agent_name,
                output={},
                error=str(e),
                execution_time_seconds=time.time() - start_time
            )

    def _get_relevant_frameworks(self, dimension: str) -> List[str]:
        """Get relevant frameworks for a dimension"""
        return DIMENSION_FRAMEWORKS.get(dimension, ["DAMA-DMBOK"])

    async def _get_rag_context(
        self,
        dimension: str,
        survey_stats: Dict[str, Any]
    ) -> str:
        """Query ChromaDB for relevant standards and best practices"""
        if not self.rag_service:
            return ""

        try:
            # Build query based on survey stats
            overall = survey_stats.get('overall', {})
            avg_score = overall.get('avg_score', 'N/A')
            query = f"{dimension}: Maturity assessment with average score {avg_score}/10. Best practices and standards."

            # Retrieve context
            context = self.rag_service.get_dimension_context(
                dimension=dimension,
                survey_summary=f"Average score: {avg_score}/10"
            )

            return context if context else ""

        except Exception as e:
            self.logger.warning(f"RAG context retrieval failed: {e}")
            return ""

    async def _assess_frameworks(
        self,
        dimension: str,
        frameworks: List[str],
        survey_stats: Dict[str, Any],
        questions_data: List[Dict],
        rag_context: str
    ) -> List[MaturityLevel]:
        """Assess maturity for each framework using LLM"""
        maturity_levels = []

        for framework in frameworks:
            self.log_execution("ASSESS_FRAMEWORK", f"Assessing {framework}")

            system_prompt = self.get_system_prompt()
            user_prompt = self.get_user_prompt(
                framework=framework,
                dimension=dimension,
                survey_stats=survey_stats,
                questions_data=questions_data,
                rag_context=rag_context
            )

            # Call LLM
            response = await self.call_llm(system_prompt, user_prompt, max_tokens=2000)

            # Parse response into MaturityLevel
            maturity_level = self._parse_maturity_response(framework, response, survey_stats, questions_data)
            maturity_levels.append(maturity_level)

        return maturity_levels

    def _parse_maturity_response(
        self,
        framework: str,
        response: str,
        survey_stats: Dict,
        questions_data: List[Dict]
    ) -> MaturityLevel:
        """Parse LLM response into structured MaturityLevel"""
        # Try to extract JSON from response
        try:
            # Look for JSON block
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                data = json.loads(json_str)

                return MaturityLevel(
                    framework=framework,
                    current_level=data.get("current_level", "Initial"),
                    score=float(data.get("score", 2.0)),
                    gaps=data.get("gaps", []),
                    best_practices=data.get("best_practices", []),
                    evidence_questions=data.get("evidence_questions", [])
                )
        except:
            pass

        # Fallback: Parse text response
        # Extract score (look for patterns like "Score: X/5" or "X.X/5")
        score = 2.0  # Default
        for line in response.split('\n'):
            if 'score' in line.lower() and '/5' in line:
                try:
                    # Extract number before /5
                    parts = line.split('/5')[0]
                    score_str = parts.split()[-1]
                    score = float(score_str)
                    break
                except:
                    pass

        # Extract current level
        current_level = "Repeatable"
        for level in MATURITY_LEVELS.values():
            if level.lower() in response.lower():
                current_level = level
                break

        # Extract gaps and best practices (simple parsing)
        gaps = []
        best_practices = []
        lines = response.split('\n')
        in_gaps_section = False
        in_practices_section = False

        for line in lines:
            line = line.strip()
            if 'gaps' in line.lower() or 'gap' in line.lower():
                in_gaps_section = True
                in_practices_section = False
            elif 'best practice' in line.lower() or 'practice' in line.lower():
                in_practices_section = True
                in_gaps_section = False
            elif line.startswith('-') or line.startswith('•') or (line and line[0].isdigit()):
                item = line.lstrip('0123456789.-•) ').strip()
                if in_gaps_section and item:
                    gaps.append(item)
                elif in_practices_section and item:
                    best_practices.append(item)

        # Extract evidence questions (look for Q# references)
        evidence_questions = []
        for q in questions_data[:5]:  # Top 5 as evidence
            q_id = q.get('question_id')
            if q_id:
                evidence_questions.append(q_id)

        return MaturityLevel(
            framework=framework,
            current_level=current_level,
            score=score,
            gaps=gaps[:5] if gaps else ["Gap analysis requires more data"],
            best_practices=best_practices[:5] if best_practices else ["Best practices require detailed assessment"],
            evidence_questions=evidence_questions
        )

    def _compute_composite_score(self, maturity_levels: List[MaturityLevel]) -> float:
        """Compute composite maturity score across all frameworks"""
        if not maturity_levels:
            return 2.0

        scores = [ml.score for ml in maturity_levels]
        return round(sum(scores) / len(scores), 2)

    async def _identify_priority_gaps(
        self,
        dimension: str,
        maturity_levels: List[MaturityLevel],
        survey_stats: Dict,
        rag_context: str
    ) -> List[Dict[str, Any]]:
        """Identify and prioritize top 5 gaps using LLM"""
        # Collect all gaps
        all_gaps = []
        for ml in maturity_levels:
            for gap in ml.gaps:
                all_gaps.append({
                    "framework": ml.framework,
                    "gap": gap,
                    "current_level": ml.current_level,
                    "score": ml.score
                })

        if not all_gaps:
            return []

        # Use LLM to prioritize gaps
        system_prompt = """You are a senior data management consultant prioritizing maturity gaps.
Analyze the gaps and prioritize the top 5 based on:
1. Business impact (regulatory risk, operational efficiency, data quality)
2. Urgency (immediate vs. long-term)
3. Remediation complexity (effort required)

Output ONLY valid JSON with this structure:
```json
{
  "priority_gaps": [
    {
      "gap_name": "Gap title",
      "description": "Detailed description",
      "framework": "Framework name",
      "priority": "Critical/High/Medium",
      "business_impact": "Impact description",
      "urgency": "Immediate/Short-term/Long-term",
      "complexity": "Low/Medium/High"
    }
  ]
}
```"""

        gaps_text = "\n".join([f"- {g['framework']}: {g['gap']} (Score: {g['score']}/5)" for g in all_gaps])
        user_prompt = f"""Dimension: {dimension}

Identified Gaps:
{gaps_text}

Survey Stats:
{json.dumps(survey_stats.get('overall', {}), indent=2)}

RAG Context (truncated):
{rag_context[:500]}

Prioritize the top 5 gaps and output as JSON."""

        try:
            response = await self.call_llm(system_prompt, user_prompt, max_tokens=2000)

            # Parse JSON
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                data = json.loads(json_str)
                return data.get("priority_gaps", [])[:5]
        except Exception as e:
            self.logger.warning(f"Gap prioritization parsing failed: {e}")

        # Fallback: Return top 5 gaps by score
        sorted_gaps = sorted(all_gaps, key=lambda x: x['score'])[:5]
        return [
            {
                "gap_name": g['gap'],
                "description": f"Gap in {g['framework']}",
                "framework": g['framework'],
                "priority": "High" if g['score'] < 3 else "Medium",
                "business_impact": "Requires assessment",
                "urgency": "Short-term",
                "complexity": "Medium"
            }
            for g in sorted_gaps
        ]

    def get_system_prompt(self) -> str:
        """System prompt for maturity assessment"""
        return """You are a senior data management consultant specializing in maturity assessment.
Analyze survey data against industry frameworks and standards.
Use Chain-of-Thought reasoning:
Step 1: Review survey scores and patterns
Step 2: Compare to framework requirements (from RAG context)
Step 3: Assign maturity level (1-5 scale)
Step 4: Identify gaps
Step 5: Map to best practices

Output your assessment as JSON:
```json
{
  "current_level": "Level name (Initial/Repeatable/Defined/Managed/Optimized)",
  "score": 2.5,
  "gaps": ["Gap 1", "Gap 2", "Gap 3"],
  "best_practices": ["Practice 1", "Practice 2", "Practice 3"],
  "evidence_questions": [1, 5, 12]
}
```"""

    def get_user_prompt(
        self,
        framework: str,
        dimension: str,
        survey_stats: Dict,
        questions_data: List[Dict],
        rag_context: str
    ) -> str:
        """User prompt for framework-specific maturity assessment"""
        overall = survey_stats.get('overall', {})
        avg_score = overall.get('avg_score', 'N/A')

        # Sample questions (top 5)
        sample_questions = questions_data[:5]
        questions_text = "\n".join([
            f"Q{q.get('question_id')}: {q.get('text', q.get('question', ''))} (Score: {q.get('avg_score', 'N/A')}/10)"
            for q in sample_questions
        ])

        return f"""Assess organizational maturity for: {dimension}
Framework: {framework}

Survey Results:
- Average Score: {avg_score}/10
- Total Questions: {overall.get('total_questions', 0)}
- Total Responses: {overall.get('total_responses', 0)}

Sample Questions:
{questions_text}

Industry Standards Context (from RAG):
{rag_context[:1000]}

Assess maturity against {framework} on a 1-5 scale:
1 = Initial/Ad-hoc
2 = Repeatable/Reactive
3 = Defined/Proactive
4 = Managed/Quantified
5 = Optimized/Continuous Improvement

Output as JSON (structure provided in system prompt)."""
