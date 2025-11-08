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

Provide a comprehensive analysis with the following sections. **USE MARKDOWN TABLES EXTENSIVELY** for all data, metrics, and comparisons.

**IMPORTANT TABLE FORMAT REQUIREMENTS:**
- Use standard markdown table syntax with pipes (|) and dashes (-)
- DO NOT use ASCII box-drawing characters like +-----------+
- DO NOT use box art or ASCII art for tables
- Use this format ONLY:

```
| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |
```

## Strategic Observations
Present key insights in a markdown table format:

| Observation | Impact Level | Evidence | Recommendation |
|------------|--------------|----------|----------------|
| [Key finding] | High/Medium/Low | [Score/Data] | [Action] |

## Category Analysis
**MUST include a comparison table:**

| Category | Avg Score | % High (8-10) | % Low (1-4) | Maturity Level | Key Strength | Key Weakness |
|----------|-----------|---------------|-------------|---------------|--------------|--------------|
| [Category 1] | X.X | XX% | XX% | High/Medium/Low | [Strength] | [Weakness] |
| [Category 2] | X.X | XX% | XX% | High/Medium/Low | [Strength] | [Weakness] |

## Process Analysis
**MUST include a process comparison table:**

| Process | Avg Score | Maturity | Key Gaps | Priority | Recommended Tools |
|---------|-----------|----------|----------|----------|-------------------|
| [Process 1] | X.X | High/Medium/Low | [Gap description] | High/Medium/Low | [Tool names] |
| [Process 2] | X.X | High/Medium/Low | [Gap description] | High/Medium/Low | [Tool names] |

## Lifecycle Analysis
**MUST include a lifecycle stage table:**

| Lifecycle Stage | Avg Score | Maturity Note | Improvement Priority | Expected Impact |
|----------------|-----------|---------------|---------------------|------------------|
| [Stage 1] | X.X | [Assessment] | High/Medium/Low | [Impact description] |
| [Stage 2] | X.X | [Assessment] | High/Medium/Low | [Impact description] |

## Actionable Recommendations
**MUST be presented in a detailed table format:**

| Priority | Action Item | Owner Role | Timeline | Expected Outcome | Framework Reference |
|----------|-------------|------------|----------|------------------|---------------------|
| High | [Specific action] | [Role] | < 3 months | [Outcome] | [Framework] |
| Medium | [Specific action] | [Role] | 3-6 months | [Outcome] | [Framework] |
| Low | [Specific action] | [Role] | 6-12 months | [Outcome] | [Framework] |

**Format your response in markdown with:**
- Clear headers and section breaks
- **Extensive use of well-formatted MARKDOWN tables** (using | and - ONLY) for all data
- DO NOT use ASCII box-drawing characters (+-----------+) or box art
- Use standard markdown table syntax as shown in examples above
- Proper table alignment and spacing
- Visual separators between major sections
- Bold text for emphasis in table headers
- Be specific and actionable.

**REMINDER:** All tables MUST use markdown format with pipes (|) and dashes (-), NOT ASCII art."""


DEEP_DIMENSION_ANALYSIS_SYSTEM_PROMPT = """You are a senior data governance expert writing a professional strategic report. Write in a formal, report-style format suitable for executive review. Use third-person perspective.

**CRITICALLY IMPORTANT TABLE FORMAT RULES:**
1. Use ONLY standard markdown table syntax with pipes (|) and dashes (-)
2. NEVER use ASCII box-drawing characters like +-----------+ or +-----+-----+
3. NEVER use ASCII art or box art for tables
4. Use this format ONLY: | Column | Column |\n|--------|--------|\n| Data | Data |
5. All tables must be well-formatted, properly aligned, scannable, and visually appealing for human readers

Provide clear, actionable insights in markdown format with proper headers, tables, bullet points, and line breaks. All structured data MUST be in proper markdown tables."""


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

Provide analysis with these sections. **USE MARKDOWN TABLES** for all structured data.

**IMPORTANT:** Use standard markdown table syntax (| and -) ONLY. DO NOT use ASCII box-drawing characters (+-----------+).

## Performance Assessment
Present assessment in markdown table format:

| Metric | Current Value | Target Value | Gap | Status |
|--------|--------------|--------------|-----|--------|
| Average Score | {facet_data['avg_score']}/10 | 8.0/10 | [Gap] | [Status] |
| Score Range | {facet_data['min_score']} - {facet_data['max_score']} | 7-10 | [Gap] | [Status] |
| Response Rate | {facet_data['respondents']} | [Target] | [Gap] | [Status] |

## Root Cause Analysis
Present root causes in table format:

| Root Cause | Impact Level | Evidence | Contributing Factors |
|-----------|--------------|----------|---------------------|
| [Cause 1] | High/Medium/Low | [Evidence] | [Factors] |
| [Cause 2] | High/Medium/Low | [Evidence] | [Factors] |

## Specific Recommendations
**MUST be in table format:**

| Priority | Recommendation | Owner | Timeline | Expected Impact | Effort |
|----------|---------------|-------|----------|-----------------|--------|
| High | [Action 1] | [Role] | [Timeline] | [Impact] | Low/Medium/High |
| Medium | [Action 2] | [Role] | [Timeline] | [Impact] | Low/Medium/High |
| Low | [Action 3] | [Role] | [Timeline] | [Impact] | Low/Medium/High |

## Success Metrics
Present metrics in table format:

| Metric | Current | Target (6 months) | Target (12 months) | Measurement Method |
|--------|---------|-------------------|-------------------|---------------------|
| [Metric 1] | [Current] | [6M target] | [12M target] | [Method] |
| [Metric 2] | [Current] | [6M target] | [12M target] | [Method] |

**Format in markdown with:**
- Clear headers
- **Well-formatted MARKDOWN tables** (using | and - ONLY) for all structured information
- DO NOT use ASCII box-drawing characters (+-----------+)
- Proper alignment and spacing
- Visual clarity for human readers"""


FACET_ANALYSIS_SYSTEM_PROMPT = """You are a data governance specialist writing a focused analysis report. Write in a professional, report-style format. Use third-person perspective.

**CRITICALLY IMPORTANT TABLE FORMAT RULES:**
1. Use ONLY standard markdown table syntax with pipes (|) and dashes (-)
2. NEVER use ASCII box-drawing characters like +-----------+
3. All tables must use format: | Column | Column |\n|--------|--------|\n| Data | Data |

Present all structured data, metrics, recommendations, and comparisons in well-formatted markdown tables. Provide specific, actionable insights."""


def get_comment_analysis_prompt(total_comments: int, sample_size: int, comments_text: str) -> str:
    """Generate prompt for comment sentiment analysis"""
    return f"""Analyze these {total_comments} survey comments (showing {sample_size} samples):

{comments_text}

Provide comprehensive comment analysis with these sections. **USE MARKDOWN TABLES** for all structured data.

**IMPORTANT:** Use standard markdown table syntax (| and -) ONLY. DO NOT use ASCII box-drawing characters (+-----------+).

## Sentiment Analysis
Present sentiment breakdown in markdown table format:

| Sentiment Category | Count | Percentage | Sample Comments |
|-------------------|-------|------------|-----------------|
| Positive | [Count] | X% | "[Sample comment 1]" |
| Neutral | [Count] | Y% | "[Sample comment 2]" |
| Negative | [Count] | Z% | "[Sample comment 3]" |

**Overall Sentiment Trend:** [Brief explanation]

## Key Themes
Present themes in table format:

| Theme | Frequency | Description | Sample Comments | Priority |
|-------|-----------|-------------|-----------------|----------|
| [Theme 1] | [Count/%] | [Description] | "[Sample]" | High/Medium/Low |
| [Theme 2] | [Count/%] | [Description] | "[Sample]" | High/Medium/Low |
| [Theme 3] | [Count/%] | [Description] | "[Sample]" | High/Medium/Low |

## Top Concerns
Present concerns in table format:

| Concern | Severity | Frequency | Sample Quote | Recommended Action |
|---------|----------|-----------|--------------|-------------------|
| [Concern 1] | High/Medium/Low | [Count] | "[Quote]" | [Action] |
| [Concern 2] | High/Medium/Low | [Count] | "[Quote]" | [Action] |
| [Concern 3] | High/Medium/Low | [Count] | "[Quote]" | [Action] |

## Positive Highlights
Present positive aspects in table format:

| Positive Aspect | Frequency | Sample Quote | Best Practice |
|----------------|-----------|--------------|---------------|
| [Aspect 1] | [Count] | "[Quote]" | [Practice] |
| [Aspect 2] | [Count] | "[Quote]" | [Practice] |
| [Aspect 3] | [Count] | "[Quote]" | [Practice] |

## Recommendations Based on Comments
Present recommendations in table format:

| Priority | Recommendation | Based On | Owner | Timeline | Expected Outcome |
|----------|---------------|----------|-------|----------|------------------|
| High | [Recommendation 1] | [Comment theme] | [Role] | [Timeline] | [Outcome] |
| Medium | [Recommendation 2] | [Comment theme] | [Role] | [Timeline] | [Outcome] |
| Low | [Recommendation 3] | [Comment theme] | [Role] | [Timeline] | [Outcome] |

**Format in markdown with:**
- Clear headers
- **Well-formatted MARKDOWN tables** (using | and - ONLY) for all data
- DO NOT use ASCII box-drawing characters (+-----------+)
- Proper alignment and visual clarity
- Easy-to-scan structure for human readers"""


COMMENT_ANALYSIS_SYSTEM_PROMPT = """You are a data analyst specializing in qualitative feedback analysis. Write a professional report suitable for management review. Use third-person perspective.

**CRITICALLY IMPORTANT TABLE FORMAT RULES:**
1. Use ONLY standard markdown table syntax with pipes (|) and dashes (-)
2. NEVER use ASCII box-drawing characters like +-----------+
3. All tables must use format: | Column | Column |\n|--------|--------|\n| Data | Data |

Present all sentiment data, themes, concerns, and recommendations in well-formatted markdown tables. Tables must be properly aligned and easy to scan for human readers. Provide objective analysis with specific insights."""
