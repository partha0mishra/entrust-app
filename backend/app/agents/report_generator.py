"""
Report Generator Agent

Crafts comprehensive 50+ page reports incorporating stats, maturity analysis,
action items, roadmaps, graphs, and word clouds.
"""

import json
import time
from typing import Dict, List, Any
from .base import AgentBase, AgentResult, GeneratedReport, ReportSection


class ReportGeneratorAgent(AgentBase):
    """
    Generates comprehensive, professional reports

    Capabilities:
    - Create executive summary
    - Build detailed sections (current state, analysis, maturity, recommendations)
    - Generate prioritized action items with RICE scoring
    - Create 6-12 month roadmap
    - Prepare data for graphs and word clouds
    """

    def __init__(self, llm_provider=None):
        super().__init__("ReportGeneratorAgent", llm_provider)

    async def execute(
        self,
        dimension: str,
        survey_stats: Dict[str, Any],
        maturity_assessment: Dict[str, Any],
        questions_data: List[Dict[str, Any]],
        customer_name: str = "Organization"
    ) -> AgentResult:
        """
        Generate comprehensive report

        Args:
            dimension: Dimension name
            survey_stats: Output from SurveyParserAgent
            maturity_assessment: Output from MaturityAssessorAgent
            questions_data: Original survey data
            customer_name: Customer organization name

        Returns:
            AgentResult with generated report
        """
        start_time = time.time()
        self.log_execution("START", f"Generating report for {dimension}")

        try:
            # Step 1: Generate executive summary
            self.log_execution("STEP_1", "Generating executive summary")
            executive_summary = await self._generate_executive_summary(
                dimension, survey_stats, maturity_assessment
            )

            # Step 2: Generate detailed sections
            self.log_execution("STEP_2", "Generating report sections")
            sections = await self._generate_sections(
                dimension, survey_stats, maturity_assessment, questions_data
            )

            # Step 3: Generate action items
            self.log_execution("STEP_3", "Generating action items")
            action_items = await self._generate_action_items(
                dimension, survey_stats, maturity_assessment
            )

            # Step 4: Generate roadmap
            self.log_execution("STEP_4", "Generating roadmap")
            roadmap = await self._generate_roadmap(
                dimension, maturity_assessment, action_items
            )

            # Step 5: Prepare visual data
            self.log_execution("STEP_5", "Preparing visual data")
            visuals = self._prepare_visuals(survey_stats, maturity_assessment)

            # Build report
            report = GeneratedReport(
                dimension=dimension,
                executive_summary=executive_summary,
                sections=sections,
                action_items=action_items,
                roadmap=roadmap,
                visuals=visuals,
                metadata={
                    "customer_name": customer_name,
                    "generation_timestamp": time.time(),
                    "avg_score": survey_stats.get('overall', {}).get('avg_score'),
                    "composite_maturity": maturity_assessment.get('composite_score')
                }
            )

            execution_time = time.time() - start_time
            self.log_execution("COMPLETE", f"Generated report in {execution_time:.2f}s")

            return AgentResult(
                success=True,
                agent_name=self.agent_name,
                output=report.model_dump(),
                execution_time_seconds=execution_time
            )

        except Exception as e:
            self.logger.error(f"Error in ReportGeneratorAgent: {e}", exc_info=True)
            return AgentResult(
                success=False,
                agent_name=self.agent_name,
                output={},
                error=str(e),
                execution_time_seconds=time.time() - start_time
            )

    async def _generate_executive_summary(
        self,
        dimension: str,
        survey_stats: Dict,
        maturity_assessment: Dict
    ) -> str:
        """Generate 1-2 page executive summary"""
        system_prompt = """You are a senior consultant crafting an executive summary.
Write a concise (1-2 pages), high-impact summary that:
- Highlights key findings (cite scores and evidence)
- States current maturity level
- Identifies top 3 strategic priorities
- Uses consultative, professional tone
Output in Markdown format."""

        overall = survey_stats.get('overall', {})
        composite_score = maturity_assessment.get('composite_score', 2.0)

        user_prompt = f"""Create an executive summary for {dimension}:

Key Metrics:
- Average Score: {overall.get('avg_score', 'N/A')}/10
- Response Rate: {overall.get('response_rate', 0)}%
- Composite Maturity Score: {composite_score}/5

Maturity Assessment:
{json.dumps(maturity_assessment, indent=2)}

Top Comment Themes:
{', '.join(survey_stats.get('comment_themes', []))}

Write a compelling executive summary in Markdown."""

        response = await self.call_llm(system_prompt, user_prompt, max_tokens=3000)
        return response

    async def _generate_sections(
        self,
        dimension: str,
        survey_stats: Dict,
        maturity_assessment: Dict,
        questions_data: List[Dict]
    ) -> List[ReportSection]:
        """Generate detailed report sections"""
        sections = []

        # Section 1: Current State Assessment
        sections.append(await self._generate_current_state_section(survey_stats))

        # Section 2: Category Analysis
        sections.append(await self._generate_category_analysis_section(survey_stats))

        # Section 3: Process Analysis
        sections.append(await self._generate_process_analysis_section(survey_stats))

        # Section 4: Lifecycle Analysis
        sections.append(await self._generate_lifecycle_analysis_section(survey_stats))

        # Section 5: Maturity Assessment (comprehensive)
        sections.append(await self._generate_maturity_section(
            dimension, maturity_assessment
        ))

        # Section 6: Question-Level Analysis
        sections.append(self._generate_question_level_section(questions_data))

        return sections

    async def _generate_current_state_section(self, survey_stats: Dict) -> ReportSection:
        """Generate current state assessment section"""
        overall = survey_stats.get('overall', {})
        content = f"""## Current State Assessment

**Overview Metrics:**
- Average Score: {overall.get('avg_score', 'N/A')}/10
- Median Score: {overall.get('median_score', 'N/A')}/10
- Score Range: {overall.get('min_score', 0)} - {overall.get('max_score', 0)}
- Total Questions: {overall.get('total_questions', 0)}
- Total Responses: {overall.get('total_responses', 0)}
- Response Rate: {overall.get('response_rate', 0)}%

**Score Distribution:**
"""
        score_dist = survey_stats.get('score_distribution', {})
        for range_name, count in score_dist.items():
            content += f"- {range_name}: {count} questions\n"

        return ReportSection(
            section_id="current_state",
            title="Current State Assessment",
            content=content
        )

    async def _generate_category_analysis_section(self, survey_stats: Dict) -> ReportSection:
        """Generate category analysis section"""
        content = "## Analysis by Category\n\n"
        content += "| Category | Avg Score | % High (8-10) | % Medium (5-7) | % Low (1-4) | Response Count |\n"
        content += "|----------|-----------|---------------|----------------|-------------|----------------|\n"

        by_category = survey_stats.get('by_category', {})
        for category, data in by_category.items():
            avg = data.get('avg_score', 0)
            dist = data.get('score_distribution', {})
            pct_high = dist.get('pct_high', 0)
            pct_med = dist.get('pct_medium', 0)
            pct_low = dist.get('pct_low', 0)
            count = data.get('count', 0)

            content += f"| {category} | {avg:.2f} | {pct_high:.1f}% | {pct_med:.1f}% | {pct_low:.1f}% | {count} |\n"

        return ReportSection(
            section_id="category_analysis",
            title="Analysis by Category",
            content=content
        )

    async def _generate_process_analysis_section(self, survey_stats: Dict) -> ReportSection:
        """Generate process analysis section"""
        content = "## Analysis by Process\n\n"
        content += "| Process | Avg Score | % High (8-10) | % Medium (5-7) | % Low (1-4) | Response Count |\n"
        content += "|---------|-----------|---------------|----------------|-------------|----------------|\n"

        by_process = survey_stats.get('by_process', {})
        for process, data in by_process.items():
            avg = data.get('avg_score', 0)
            dist = data.get('score_distribution', {})
            pct_high = dist.get('pct_high', 0)
            pct_med = dist.get('pct_medium', 0)
            pct_low = dist.get('pct_low', 0)
            count = data.get('count', 0)

            content += f"| {process} | {avg:.2f} | {pct_high:.1f}% | {pct_med:.1f}% | {pct_low:.1f}% | {count} |\n"

        return ReportSection(
            section_id="process_analysis",
            title="Analysis by Process",
            content=content
        )

    async def _generate_lifecycle_analysis_section(self, survey_stats: Dict) -> ReportSection:
        """Generate lifecycle analysis section"""
        content = "## Analysis by Lifecycle Stage\n\n"
        content += "| Lifecycle Stage | Avg Score | % High (8-10) | % Medium (5-7) | % Low (1-4) | Response Count |\n"
        content += "|----------------|-----------|---------------|----------------|-------------|----------------|\n"

        by_lifecycle = survey_stats.get('by_lifecycle', {})
        for stage, data in by_lifecycle.items():
            avg = data.get('avg_score', 0)
            dist = data.get('score_distribution', {})
            pct_high = dist.get('pct_high', 0)
            pct_med = dist.get('pct_medium', 0)
            pct_low = dist.get('pct_low', 0)
            count = data.get('count', 0)

            content += f"| {stage} | {avg:.2f} | {pct_high:.1f}% | {pct_med:.1f}% | {pct_low:.1f}% | {count} |\n"

        return ReportSection(
            section_id="lifecycle_analysis",
            title="Analysis by Lifecycle Stage",
            content=content
        )

    async def _generate_maturity_section(
        self,
        dimension: str,
        maturity_assessment: Dict
    ) -> ReportSection:
        """Generate comprehensive maturity assessment section"""
        content = f"""## Maturity Assessment

**Composite Maturity Score:** {maturity_assessment.get('composite_score', 0)}/5

### Framework-Specific Maturity Levels

"""
        maturity_levels = maturity_assessment.get('maturity_levels', [])
        for ml in maturity_levels:
            content += f"""#### {ml.get('framework')}
- **Current Level:** {ml.get('current_level')}
- **Score:** {ml.get('score')}/5
- **Key Gaps:**
"""
            for gap in ml.get('gaps', []):
                content += f"  - {gap}\n"

            content += "- **Best Practices:**\n"
            for practice in ml.get('best_practices', []):
                content += f"  - {practice}\n"
            content += "\n"

        content += "\n### Priority Maturity Gaps\n\n"
        priority_gaps = maturity_assessment.get('priority_gaps', [])
        for i, gap in enumerate(priority_gaps, 1):
            content += f"""**{i}. {gap.get('gap_name')}** (Priority: {gap.get('priority')})
- **Framework:** {gap.get('framework')}
- **Business Impact:** {gap.get('business_impact')}
- **Urgency:** {gap.get('urgency')}
- **Complexity:** {gap.get('complexity')}
- **Description:** {gap.get('description')}

"""

        return ReportSection(
            section_id="maturity_assessment",
            title="Maturity Assessment",
            content=content
        )

    def _generate_question_level_section(self, questions_data: List[Dict]) -> ReportSection:
        """Generate question-level analysis section"""
        content = "## Question-Level Analysis\n\n"
        content += "| Q# | Question | Category | Process | Lifecycle | Avg Score |\n"
        content += "|----|----------|----------|---------|-----------|-----------|\ n"

        for q in questions_data:
            q_id = q.get('question_id', '-')
            q_text = q.get('text', q.get('question', 'N/A')).replace('|', '\\|')
            category = q.get('category', '-')
            process = q.get('process', '-')
            lifecycle = q.get('lifecycle_stage', '-')
            avg_score = q.get('avg_score', 'N/A')
            avg_str = f"{avg_score:.2f}" if isinstance(avg_score, (int, float)) else str(avg_score)

            content += f"| {q_id} | {q_text[:100]} | {category} | {process} | {lifecycle} | {avg_str} |\n"

        return ReportSection(
            section_id="question_level",
            title="Question-Level Analysis",
            content=content
        )

    async def _generate_action_items(
        self,
        dimension: str,
        survey_stats: Dict,
        maturity_assessment: Dict
    ) -> List[Dict[str, Any]]:
        """Generate prioritized action items with RICE scoring"""
        system_prompt = """You are a senior consultant creating prioritized action items.
For each gap, create specific, actionable initiatives with:
- Clear description
- Owner role (e.g., CDO, Data Steward)
- Timeline (Q1-Q4 2026)
- Expected outcome
- RICE score (Reach × Impact × Confidence / Effort)
- Framework reference

Output as JSON array."""

        priority_gaps = maturity_assessment.get('priority_gaps', [])
        user_prompt = f"""Create 5-8 prioritized action items for {dimension}:

Priority Gaps:
{json.dumps(priority_gaps, indent=2)}

Output JSON array of action items."""

        try:
            response = await self.call_llm(system_prompt, user_prompt, max_tokens=2000)
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                return json.loads(json_str)
        except Exception as e:
            self.logger.warning(f"Action item generation failed: {e}")

        # Fallback: Generate basic action items from gaps
        return [
            {
                "action": f"Address {gap.get('gap_name')}",
                "priority": gap.get('priority', 'High'),
                "owner": "Data Management Team",
                "timeline": "Q2 2026",
                "expected_outcome": gap.get('business_impact', 'Improvement'),
                "framework": gap.get('framework', 'DAMA-DMBOK')
            }
            for gap in priority_gaps[:5]
        ]

    async def _generate_roadmap(
        self,
        dimension: str,
        maturity_assessment: Dict,
        action_items: List[Dict]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate 6-12 month roadmap"""
        return {
            "Phase 1: Foundation (0-6 months)": [
                item for item in action_items if "Q1" in item.get('timeline', '') or "Q2" in item.get('timeline', '')
            ][:3],
            "Phase 2: Enhancement (6-12 months)": [
                item for item in action_items if "Q3" in item.get('timeline', '') or "Q4" in item.get('timeline', '')
            ][:3],
            "Phase 3: Optimization (12+ months)": [
                {"action": "Continuous improvement initiatives", "priority": "Medium", "owner": "Data Governance", "timeline": "Ongoing", "expected_outcome": "Sustained excellence"}
            ]
        }

    def _prepare_visuals(
        self,
        survey_stats: Dict,
        maturity_assessment: Dict
    ) -> Dict[str, Any]:
        """Prepare data for graphs and word clouds"""
        return {
            "category_scores": {
                name: data.get('avg_score', 0)
                for name, data in survey_stats.get('by_category', {}).items()
            },
            "maturity_by_framework": {
                ml.get('framework', 'Unknown'): ml.get('score', 0)
                for ml in maturity_assessment.get('maturity_levels', [])
            },
            "score_distribution": survey_stats.get('score_distribution', {}),
            "word_cloud_themes": survey_stats.get('comment_themes', [])
        }
