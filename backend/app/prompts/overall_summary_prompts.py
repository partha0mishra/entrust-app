"""
Prompts for generating overall cross-dimension summary reports
"""

from .base_prompts import OVERALL_SUMMARY_PROMPT_ADD_ON

OVERALL_SUMMARY_SECTIONS = """
### 1. Executive Summary
- High-level overview across all dimensions
- Overall maturity score (aggregated average)
- Top 3 cross-cutting themes

### 2. Cross-Dimension Comparison
- Create a table with columns: **Dimension**, Avg Score, Maturity Level, Key Strength/Weakness
- Visualize overall performance (e.g., describe a radar chart)

### 3. Interconnected Insights
- Highlight linkages (e.g., governance weaknesses affecting quality)
- Common patterns by Category/Process/Lifecycle across dimensions

### 4. Consolidated Action Plan
- Create a table with columns: Priority, Action Item, Affected Dimensions, Owner, Timeline, Expected Impact
- Provide at least one 'High' priority action.

### 5. Enterprise-Wide Risks
- Top 5 risks with severity ratings
- Mitigation strategies

### 6. Roadmap for Maturity Improvement
- Phased recommendations (Short/Mid/Long-term)
- Metrics for tracking progress (e.g., KPI dashboards)

### 7. Organizational Maturity Assessment

#### Overall Maturity Profile
Synthesize maturity assessments across all dimensions:

| Dimension | DAMA-DMBOK Level | Gartner EIM Level | Overall Maturity (1-5) | Key Strengths | Critical Gaps |
|-----------|------------------|-------------------|----------------------|---------------|---------------|
| [Dimension 1] | [Level] | [Level] | [X.X/5] | [Strengths] | [Gaps] |
| [Dimension 2] | [Level] | [Level] | [X.X/5] | [Strengths] | [Gaps] |

**Enterprise Maturity Score**: [X.X/5.0]

#### Cross-Dimension Maturity Insights
- Identify patterns across dimensions (e.g., strong in monitoring, weak in prevention)
- Highlight interdependencies affecting maturity (e.g., governance gaps impacting quality)
- Assess organizational readiness for maturity advancement

#### Unified Maturity Progression Strategy

**Phase 1 (0-6 months) - Foundation Building**:
- Quick wins across all dimensions
- Critical capability gaps
- Cross-functional initiatives

**Phase 2 (6-12 months) - Capability Enhancement**:
- Process standardization
- Technology enablement
- Training and change management

**Phase 3 (12-24 months) - Optimization**:
- Advanced capabilities
- Continuous improvement
- Innovation and excellence
"""

OVERALL_SUMMARY_SYSTEM_PROMPT = OVERALL_SUMMARY_PROMPT_ADD_ON + "You are a **senior data management consultant** tasked with synthesizing insights across multiple data management dimensions. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. The analysis is based on survey responses with scores on a 1-10 scale."


def get_overall_summary_chunked_prompt(chunk_index: int, total_chunks: int, chunk_data: str) -> str:
    """Generate prompt for chunked dimension analysis"""
    prompt = f"Analyze these data governance dimensions (Part {chunk_index+1} of {total_chunks}):\n\n"
    prompt += chunk_data
    prompt += "\n\nProvide a consolidated assessment focusing on cross-cutting themes and strategic insights from these dimensions."
    return prompt


def get_overall_summary_consolidation_prompt(chunk_summaries: list) -> str:
    """Generate prompt for final consolidation of chunk summaries"""
    prompt = "You have analyzed multiple groups of data governance dimensions. Here are the analyses:\n\n"
    for i, summary in enumerate(chunk_summaries):
        prompt += f"\n--- Analysis Part {i+1} ---\n{summary}\n"

    prompt += "\n\nGenerate a professionally crafted, consultative, executive-ready report with the following sections:\n"
    prompt += OVERALL_SUMMARY_SECTIONS
    return prompt


def get_overall_summary_single_prompt(all_summaries_text: str) -> str:
    """Generate prompt for single-pass overall summary"""
    prompt = "Analyze the following dimension summaries and provide an overall organizational data governance assessment:\n\n"
    prompt += all_summaries_text
    prompt += "\n\nGenerate a professionally crafted, consultative, executive-ready report with the following sections:\n"
    prompt += """
### 1. Executive Summary
- High-level overview across all dimensions
- Overall maturity score (aggregated average)
- Top 3 cross-cutting themes

### 2. Cross-Dimension Comparison
- Create a table with columns: **Dimension**, Avg Score, Maturity Level, Key Strength/Weakness
- Visualize overall performance (e.g., describe a radar chart)

### 3. Interconnected Insights
- Highlight linkages (e.g., governance weaknesses affecting quality)
- Common patterns by Category/Process/Lifecycle across dimensions

Use markdown formatting with clear headers and bullet points."""
    return prompt


CONSOLIDATION_SYSTEM_PROMPT = "You are a senior data governance consultant writing a professional executive report. Write in a formal, report-style format suitable for C-level executives. Use third-person perspective. Do NOT use first person (I, we) or ask questions. Do NOT include interactive elements or conversational language. Use markdown formatting."
