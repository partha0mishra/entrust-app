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
**MUST create a well-formatted table:**

| Dimension | Avg Score | Maturity Level | Key Strength | Key Weakness |
|-----------|-----------|---------------|--------------|--------------|
| [Dimension 1] | X.X/10 | High/Medium/Low | [Strength] | [Weakness] |
| [Dimension 2] | X.X/10 | High/Medium/Low | [Strength] | [Weakness] |

**Performance Visualization:** [Describe overall performance pattern, e.g., "Strong in security (8.2), weak in documentation (4.5)"]

### 3. Interconnected Insights
- Highlight linkages (e.g., governance weaknesses affecting quality)
- Common patterns by Category/Process/Lifecycle across dimensions

### 4. Consolidated Action Plan
**MUST create a comprehensive, well-formatted table:**

| Priority | Action Item | Affected Dimensions | Owner Role | Timeline | Expected Impact | Framework Reference |
|----------|-------------|---------------------|------------|----------|-----------------|---------------------|
| High | [Action 1] | [Dimension list] | [Role] | [Timeline] | [Impact description] | [Framework] |
| High | [Action 2] | [Dimension list] | [Role] | [Timeline] | [Impact description] | [Framework] |
| Medium | [Action 3] | [Dimension list] | [Role] | [Timeline] | [Impact description] | [Framework] |
| Low | [Action 4] | [Dimension list] | [Role] | [Timeline] | [Impact description] | [Framework] |

**Note:** At least one action must be marked as 'High' priority.

### 5. Enterprise-Wide Risks
**MUST present in table format:**

| Rank | Risk | Severity | Affected Dimensions | Likelihood | Impact | Mitigation Strategy | Urgency |
|------|------|----------|---------------------|------------|--------|---------------------|---------|
| 1 | [Risk 1] | Critical/High/Medium/Low | [Dimensions] | High/Medium/Low | High/Medium/Low | [Strategy] | Immediate/Short-term/Long-term |
| 2 | [Risk 2] | Critical/High/Medium/Low | [Dimensions] | High/Medium/Low | High/Medium/Low | [Strategy] | Immediate/Short-term/Long-term |
| 3 | [Risk 3] | Critical/High/Medium/Low | [Dimensions] | High/Medium/Low | High/Medium/Low | [Strategy] | Immediate/Short-term/Long-term |
| 4 | [Risk 4] | Critical/High/Medium/Low | [Dimensions] | High/Medium/Low | High/Medium/Low | [Strategy] | Immediate/Short-term/Long-term |
| 5 | [Risk 5] | Critical/High/Medium/Low | [Dimensions] | High/Medium/Low | High/Medium/Low | [Strategy] | Immediate/Short-term/Long-term |

### 6. Roadmap for Maturity Improvement
**MUST present in table format:**

**Phased Recommendations:**

| Phase | Timeline | Key Initiatives | Expected Outcomes | Success Metrics | Owner |
|-------|----------|------------------|-------------------|-----------------|-------|
| Short-term | 0-3 months | [Initiative 1, 2, 3] | [Outcomes] | [Metrics] | [Role] |
| Mid-term | 3-6 months | [Initiative 1, 2, 3] | [Outcomes] | [Metrics] | [Role] |
| Long-term | 6-12 months | [Initiative 1, 2, 3] | [Outcomes] | [Metrics] | [Role] |

**Progress Tracking Metrics:**

| Metric | Current Baseline | Target (3M) | Target (6M) | Target (12M) | Measurement Method |
|--------|------------------|-------------|------------|--------------|-------------------|
| Overall Maturity Score | X.X/10 | X.X/10 | X.X/10 | X.X/10 | [Method] |
| [Metric 2] | [Current] | [3M] | [6M] | [12M] | [Method] |
| [Metric 3] | [Current] | [3M] | [6M] | [12M] | [Method] |
"""

OVERALL_SUMMARY_SYSTEM_PROMPT = OVERALL_SUMMARY_PROMPT_ADD_ON + "You are a **senior data management consultant** tasked with synthesizing insights across multiple data management dimensions. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. **CRITICALLY IMPORTANT: Use well-formatted markdown tables extensively for all cross-dimension comparisons, action plans, risks, and metrics. Tables must be properly aligned, scannable, and visually appealing for human readers.** The analysis is based on survey responses with scores on a 1-10 scale."


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
    prompt += "\n\nGenerate a professionally crafted, consultative, executive-ready report with the following sections. **USE TABLES EXTENSIVELY** for all data and comparisons:\n"
    prompt += """
### 1. Executive Summary
- High-level overview across all dimensions
- Overall maturity score (aggregated average)
- Top 3 cross-cutting themes

### 2. Cross-Dimension Comparison
**MUST create a well-formatted table:**

| Dimension | Avg Score | Maturity Level | Key Strength | Key Weakness |
|-----------|-----------|---------------|--------------|--------------|
| [Dimension 1] | X.X/10 | High/Medium/Low | [Strength] | [Weakness] |
| [Dimension 2] | X.X/10 | High/Medium/Low | [Strength] | [Weakness] |

**Performance Visualization:** [Describe overall performance pattern]

### 3. Interconnected Insights
- Highlight linkages (e.g., governance weaknesses affecting quality)
- Common patterns by Category/Process/Lifecycle across dimensions

**Format in markdown with:**
- Clear headers and section breaks
- **Extensive use of well-formatted tables** for all data
- Proper table alignment and spacing
- Visual clarity for human readers"""
    return prompt


CONSOLIDATION_SYSTEM_PROMPT = "You are a senior data governance consultant writing a professional executive report. Write in a formal, report-style format suitable for C-level executives. Use third-person perspective. Do NOT use first person (I, we) or ask questions. Do NOT include interactive elements or conversational language. **CRITICALLY IMPORTANT: Use well-formatted markdown tables extensively for all data, comparisons, and structured information. Tables must be properly aligned and visually clear for human readers.** Use markdown formatting."
