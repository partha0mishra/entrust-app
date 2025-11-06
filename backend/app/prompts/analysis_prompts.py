"""
Prompts for deep dimension analysis, facet analysis, and comment sentiment analysis
"""

def get_deep_dimension_analysis_prompt(
    dimension: str,
    overall_metrics: dict,
    category_text: str,
    process_text: str,
    lifecycle_text: str
) -> str:
    """Generate prompt for deep dimension analysis"""
    return f"""As a data governance expert, provide a comprehensive analysis of the {dimension} dimension.

## METRICS OVERVIEW
| Metric | Value |
|--------|-------|
| Average Score | {overall_metrics['avg_score']}/10 |
| Response Rate | {overall_metrics['response_rate']} |
| Score Range | {overall_metrics['min_score']} - {overall_metrics['max_score']} |
| Total Responses | {overall_metrics['total_responses']} |
| Total Respondents | {overall_metrics.get('total_respondents', 'N/A')} |

## BREAKDOWN DATA

### Category Breakdown:
{category_text}

### Process Breakdown:
{process_text}

### Lifecycle Stage Breakdown:
{lifecycle_text}

---

## REQUIRED OUTPUT FORMAT

### 1. Executive Summary (Table Format)
Create a summary table showing:
| Aspect | Status | Score | Key Insight |
|--------|--------|-------|-------------|
| Overall Maturity | [Critical/Low/Medium/High/Excellent] | {overall_metrics['avg_score']}/10 | [One sentence] |
| Top Strength | [Category/Process] | [Score] | [Why it's strong] |
| Top Weakness | [Category/Process] | [Score] | [Why it's weak] |
| Risk Level | [Low/Medium/High/Critical] | - | [Risk description] |

### 2. Category Performance Comparison (MUST USE TABLE)
Create a table comparing all categories:
| Category | Avg Score | Responses | % High (8-10) | % Low (1-4) | Rank | Trend | Key Issue |
|----------|-----------|-----------|---------------|-------------|------|-------|-----------|
| [Category 1] | [X.X] | [N] | [X%] | [X%] | [1-5] | [Up/Down/Stable] | [Brief description] |
| [Category 2] | [X.X] | [N] | [X%] | [X%] | [1-5] | [Up/Down/Stable] | [Brief description] |

**Key Insight:** Provide a one-sentence summary of the most important finding from this comparison.

### 3. Process Analysis (MUST USE TABLE)
Create a table analyzing all processes:
| Process | Avg Score | Maturity Level | Key Gaps | Priority | Recommended Tools |
|---------|-----------|----------------|----------|----------|-------------------|
| [Process 1] | [X.X] | [Low/Medium/High] | [3-5 specific gaps] | [High/Medium/Low] | [Tool names] |
| [Process 2] | [X.X] | [Low/Medium/High] | [3-5 specific gaps] | [High/Medium/Low] | [Tool names] |

### 4. Lifecycle Stage Analysis (MUST USE TABLE)
Create a table for lifecycle stages:
| Lifecycle Stage | Avg Score | Maturity Note | Improvement Priority | Action Items Count |
|-----------------|-----------|---------------|----------------------|-------------------|
| [Stage 1] | [X.X] | [Assessment] | [High/Medium/Low] | [N] |

### 5. Risk Matrix (MUST USE TABLE)
Create a risk assessment table:
| Risk | Severity | Likelihood | Impact | Urgency | Mitigation Strategy |
|------|----------|------------|--------|---------|-------------------|
| [Risk 1] | [Critical/High/Medium/Low] | [High/Medium/Low] | [High/Medium/Low] | [Immediate/Short-term/Long-term] | [Strategy] |

### 6. Prioritized Action Plan (MUST USE TABLE)
Create a comprehensive action table:
| Priority | Action Item | Owner Role | Timeline | Expected Impact | Success Metrics | Framework Reference |
|----------|-------------|------------|----------|-----------------|-----------------|---------------------|
| 1 (High) | [Specific action] | [Role] | [Timeframe] | [High/Medium/Low] | [Metric] | [DAMA/ISO/GDPR/etc] |
| 2 (High) | [Specific action] | [Role] | [Timeframe] | [High/Medium/Low] | [Metric] | [Framework] |

**Organize by timeframe:**
- **Quick Wins (< 3 months):** [List from table]
- **Medium-term (3-6 months):** [List from table]
- **Strategic Initiatives (6-12 months):** [List from table]

### 7. Key Insights Summary
Provide concise, actionable insights based on the data:
- **Top Performers:** List the 2-3 highest scoring categories/processes with specific scores
- **Critical Gaps:** List the 2-3 lowest scoring areas that need immediate attention
- **Patterns:** Identify any notable patterns or correlations (e.g., "Processes in [category] consistently score higher")
- **Recommendations:** Top 3 priority recommendations based on the analysis

### 8. Strategic Observations
- [3-5 key insights with evidence from the data]
- Each insight should reference specific scores, categories, or processes
- Link to frameworks (DAMA-DMBOK, ISO 8000, GDPR, NIST)

### 9. Question-Level Analysis (Table Format)
| Question ID | Question Text | Category | Process | Avg Score | Min | Max | Responses | Key Comment |
|-------------|---------------|----------|---------|-----------|-----|-----|------------|-------------|
| [Q#] | [Text] | [Cat] | [Proc] | [X.X] | [X] | [X] | [N] | [Quote] |

---

**CRITICAL:** Use markdown tables extensively. Make the report visually scannable with clear tables, proper formatting, and visual descriptions. Be specific and actionable."""


DEEP_DIMENSION_ANALYSIS_SYSTEM_PROMPT = """You are a senior data governance expert writing a professional strategic report. Write in a formal, report-style format suitable for executive review. Use third-person perspective.

**CRITICAL FORMATTING REQUIREMENTS:**
1. **Use Markdown tables extensively** - Convert all comparisons, rankings, and data summaries into well-formatted tables
2. **Data-driven insights** - When describing trends or comparisons, use specific numbers and percentages (e.g., "Category X scores 8.5/10, which is 30% higher than Category Y at 6.5/10")
3. **Structure for readability** - Use clear hierarchy with headers (##, ###), bullet lists, numbered lists, and blockquotes for key insights
4. **Code blocks for metrics** - Use code blocks or emphasis for key metrics (scores, percentages, etc.)
5. **Table format examples:**
   - Performance comparisons: | Category | Score | Rank | Trend |
   - Action items: | Priority | Action | Owner | Timeline | Impact |
   - Risk matrix: | Risk | Severity | Likelihood | Impact |
6. **Quantitative insights** - Use specific numbers and percentages (e.g., "Score distribution: 60% of responses score 7-10 (high), 25% score 4-6 (medium), 15% score 1-3 (low)")

Provide clear, actionable insights in markdown format with proper headers, bullet points, and extensive tables. Focus on quantitative data and specific recommendations."""


def get_facet_analysis_prompt(
    facet_type: str,
    facet_name: str,
    facet_data: dict,
    questions_text: str,
    comments_text: str
) -> str:
    """Generate prompt for facet analysis"""
    return f"""Analyze this {facet_type} facet of data governance:

{facet_type.upper()}: {facet_name}
Average Score: {facet_data['avg_score']}/10
Score Range: {facet_data['min_score']} - {facet_data['max_score']}
Total Responses: {facet_data['count']}
Respondents: {facet_data['respondents']}

Questions in this {facet_type}:
{questions_text}

Sample Comments:
{comments_text}

Provide analysis with these sections:

## Performance Assessment
- How is this {facet_type} performing relative to a 10-point scale?
- What does this score indicate about organizational capabilities?

## Root Cause Analysis
- Why might this {facet_type} be scoring at this level?
- What underlying factors could explain the performance?

## Specific Recommendations
- What 3-5 concrete actions should be taken to improve this {facet_type}?
- Prioritize recommendations by impact and feasibility

## Success Metrics
- What metrics should be tracked to measure improvement?
- What would "good" look like for this {facet_type} in 6-12 months?

Format in markdown with clear headers and bullet points."""


FACET_ANALYSIS_SYSTEM_PROMPT = "You are a data governance specialist writing a focused analysis report. Write in a professional, report-style format. Use third-person perspective. Provide specific, actionable insights."


def get_comment_analysis_prompt(total_comments: int, sample_size: int, comments_text: str) -> str:
    """Generate prompt for comment sentiment analysis"""
    return f"""Analyze these {total_comments} survey comments (showing {sample_size} samples):

{comments_text}

Provide comprehensive comment analysis with these sections:

## Sentiment Analysis
Categorize the comments and provide percentages:
- Positive comments: X%
- Neutral comments: Y%
- Negative comments: Z%

Explain the overall sentiment trend.

## Key Themes
List the 5-7 most common themes across all comments. For each theme:
- Theme name
- Brief description
- Approximate frequency

## Top Concerns
What are respondents most worried about or frustrated with?
List 3-5 main concerns in order of frequency/severity.

## Positive Highlights
What are respondents happy about or praising?
List 3-5 positive aspects mentioned.

## Recommendations Based on Comments
What actions should be taken based on the feedback in these comments?
Provide 3-5 specific recommendations.

Format in markdown with clear headers and bullet points."""


COMMENT_ANALYSIS_SYSTEM_PROMPT = "You are a data analyst specializing in qualitative feedback analysis. Write a professional report suitable for management review. Use third-person perspective. Provide objective analysis with specific insights."
