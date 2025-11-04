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

METRICS:
- Average Score: {overall_metrics['avg_score']}/10
- Response Rate: {overall_metrics['response_rate']}
- Score Range: {overall_metrics['min_score']} - {overall_metrics['max_score']}
- Total Responses: {overall_metrics['total_responses']}

CATEGORY BREAKDOWN:
{category_text}

PROCESS BREAKDOWN:
{process_text}

LIFECYCLE STAGE BREAKDOWN:
{lifecycle_text}

Provide a comprehensive analysis with the following sections:

## Strategic Observations
- What do these scores indicate about organizational maturity in {dimension}?
- Which areas show strength vs weakness?
- Are there concerning patterns or trends?

## Category Analysis
- Compare category performance
- Identify highest/lowest performing categories
- Explain potential reasons for category performance differences

## Process Analysis
- Which processes need attention?
- Are processes balanced or showing uneven maturity?
- What process improvements should be prioritized?

## Lifecycle Analysis
- Which lifecycle stages are problematic?
- Is there evidence of progression issues?
- What lifecycle improvements are needed?

## Actionable Recommendations
Provide 5-7 specific, prioritized actions organized by timeframe:

**Quick Wins (< 3 months):**
- [specific actions that can be completed quickly]

**Medium-term Improvements (3-6 months):**
- [actions requiring more planning and resources]

**Strategic Initiatives (6-12 months):**
- [major transformational efforts]

Format your response in markdown with clear headers and bullet points. Be specific and actionable."""


DEEP_DIMENSION_ANALYSIS_SYSTEM_PROMPT = "You are a senior data governance expert writing a professional strategic report. Write in a formal, report-style format suitable for executive review. Use third-person perspective. Provide clear, actionable insights in markdown format with proper headers, bullet points, and line breaks."


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
