"""
Prompts for generating overall cross-dimension summary reports
"""

from .base_prompts import OVERALL_SUMMARY_PROMPT_ADD_ON

OVERALL_SUMMARY_SECTIONS = """
### 1. Executive Summary (MUST USE TABLE)
Create a summary table:
| Aspect | Value | Insight |
|--------|-------|---------|
| Overall Maturity Score | [X.X]/10 | [Assessment] |
| Highest Performing Dimension | [Name] | [Why strong] |
| Lowest Performing Dimension | [Name] | [Why weak] |
| Top 3 Cross-Cutting Themes | [Theme 1], [Theme 2], [Theme 3] | [Description] |

### 2. Cross-Dimension Comparison (MUST USE TABLE)
Create a comprehensive comparison table:
| Dimension | Avg Score | Maturity Level | Key Strength | Key Weakness | Risk Level | Improvement Priority |
|-----------|-----------|---------------|--------------|--------------|------------|---------------------|
| [Dimension 1] | [X.X] | [Critical/Low/Medium/High/Excellent] | [Strength] | [Weakness] | [Low/Medium/High/Critical] | [High/Medium/Low] |
| [Dimension 2] | [X.X] | [Critical/Low/Medium/High/Excellent] | [Strength] | [Weakness] | [Low/Medium/High/Critical] | [High/Medium/Low] |

**Key Insight:** Provide a one-sentence summary of the most important cross-dimension finding.

### 3. Interconnected Insights (Table + Analysis)
Create a table showing linkages:
| Dimension Pair | Relationship Type | Impact | Evidence |
|----------------|-------------------|--------|----------|
| [Dim 1] ↔ [Dim 2] | [Enhances/Inhibits/Correlates] | [High/Medium/Low] | [Score/comment evidence] |

Common patterns table:
| Pattern | Category | Process | Lifecycle Stage | Affected Dimensions | Frequency |
|---------|----------|---------|----------------|---------------------|-----------|
| [Pattern 1] | [Category] | [Process] | [Stage] | [List] | [X dimensions] |

### 4. Consolidated Action Plan (MUST USE TABLE)
Create a comprehensive action table:
| Priority | Action Item | Affected Dimensions | Owner Role | Timeline | Expected Impact | Success Metrics | Framework Reference |
|----------|-------------|---------------------|------------|----------|-----------------|-----------------|---------------------|
| 1 (High) | [Action] | [Dim1, Dim2] | [Role] | [Timeframe] | [High/Medium/Low] | [Metric] | [Framework] |
| 2 (High) | [Action] | [Dim1, Dim3] | [Role] | [Timeframe] | [High/Medium/Low] | [Metric] | [Framework] |

**Organize by timeframe:**
- **Quick Wins (< 3 months):** [List from table]
- **Medium-term (3-6 months):** [List from table]
- **Strategic Initiatives (6-12 months):** [List from table]

### 5. Enterprise-Wide Risks (MUST USE TABLE)
Create a risk matrix:
| Risk | Severity | Likelihood | Impact | Affected Dimensions | Mitigation Strategy | Urgency |
|------|----------|------------|--------|---------------------|---------------------|---------|
| [Risk 1] | [Critical/High/Medium/Low] | [High/Medium/Low] | [High/Medium/Low] | [List] | [Strategy] | [Immediate/Short-term/Long-term] |

### 6. Roadmap for Maturity Improvement (MUST USE TABLE)
Create a phased roadmap table:
| Phase | Timeframe | Key Initiatives | Expected Maturity Gain | Dimensions Improved | Investment Level |
|-------|-----------|-----------------|----------------------|---------------------|------------------|
| Short-term | [0-3 months] | [List] | [+X.X points] | [List] | [Low/Medium/High] |
| Mid-term | [3-6 months] | [List] | [+X.X points] | [List] | [Low/Medium/High] |
| Long-term | [6-12 months] | [List] | [+X.X points] | [List] | [Low/Medium/High] |

**Metrics Tracking Table:**
| Metric | Current State | Target (6 months) | Target (12 months) | Measurement Method |
|--------|--------------|-------------------|-------------------|-------------------|
| Overall Maturity | [X.X]/10 | [Y.Y]/10 | [Z.Z]/10 | [Method] |
| [Dimension 1] Score | [X.X]/10 | [Y.Y]/10 | [Z.Z]/10 | [Method] |

**Key Metrics Summary:**
- **Current State:** Overall maturity is [X.X]/10 with [N] dimensions above 7.0
- **Target State:** Goal of [Y.Y]/10 overall maturity within 12 months
- **Critical Path:** [List top 3 initiatives that will drive the most improvement]
"""

OVERALL_SUMMARY_SYSTEM_PROMPT = OVERALL_SUMMARY_PROMPT_ADD_ON + """You are a **senior data management consultant** tasked with synthesizing insights across multiple data management dimensions. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. The analysis is based on survey responses with scores on a 1-10 scale.

**CRITICAL FORMATTING REQUIREMENTS:**
1. **Use Markdown tables extensively** - All comparisons, rankings, and data must be in well-formatted tables
2. **Data-driven insights** - Use specific numbers, percentages, and scores when describing comparisons (e.g., "Dimension X scores 8.5/10, 15% higher than the 7.4/10 average")
3. **Structured layout** - Use clear hierarchy with headers (##, ###), tables, bullet lists, and blockquotes
4. **Table format examples:**
   - Cross-dimension comparison: | Dimension | Avg Score | Maturity | Strength | Weakness |
   - Consolidated action plan: | Priority | Action | Dimensions | Owner | Timeline | Impact |
   - Risk matrix: | Risk | Severity | Dimensions Affected | Mitigation |
5. **Quantitative analysis** - Use specific numbers and percentages (e.g., "60% of dimensions score above 7.0, indicating strong overall maturity")"""


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
- Summarize overall performance with specific scores and percentages

### 3. Interconnected Insights
- Highlight linkages (e.g., governance weaknesses affecting quality)
- Common patterns by Category/Process/Lifecycle across dimensions

Use markdown formatting with clear headers and bullet points."""
    return prompt


CONSOLIDATION_SYSTEM_PROMPT = "You are a senior data governance consultant writing a professional executive report. Write in a formal, report-style format suitable for C-level executives. Use third-person perspective. Do NOT use first person (I, we) or ask questions. Do NOT include interactive elements or conversational language. Use markdown formatting."
