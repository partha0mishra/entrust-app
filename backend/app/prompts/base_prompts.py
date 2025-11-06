"""
Base prompts shared across all LLM service calls
"""

# Shared prompt add-on used for dimension summaries
PROMPT_ADD_ON = """## PROMPT ADD-ON
You are a senior data governance consultant.
**DEEP DRILL-DOWN REQUIRED**:
**Step 1**: Compute stats (avg, % high/low) by Category, Process, Lifecycle Stage.
**Step 2**: Draft visually appealing, well-formatted tables with proper alignment.
**Step 3**: Write observations with evidence.
**Step 4**: Prioritize actions (Risk × Impact).
**Step 5**:
- For **every Category, Process, and Lifecycle Stage**, provide:
  - Full score breakdown in table format
  - All comments (with sentiment/theme) in organized tables
  - 3–6 **best practices** (cite DAMA, GDPR, ISO 8000, NIST) in table format
  - 3–6 **observations**
  - 3–6 **areas for improvement**
  - 3–8 **action items** in detailed tables (priority, owner, tool, timeline, framework)
- **CRITICAL: Use tables extensively for all data, metrics, comparisons, and action items**
- **Table formatting requirements**:
  - Use proper markdown table syntax with aligned columns
  - Include clear headers with bold text
  - Ensure tables are readable and scannable
  - Use consistent formatting across all tables
  - Add visual separators between sections
- **Do not summarize** — be exhaustive.
- **Cite Q# everywhere**.
- **Self-score depth ≥ 9** or revise.

---
"""

# Shared prompt add-on for overall summaries
OVERALL_SUMMARY_PROMPT_ADD_ON = """## PROMPT ADD-ON
You are a senior data governance consultant.
**Step 1**: Compute stats (avg, % high/low) by Category, Process, Lifecycle Stage.
**Step 2**: Draft tables.
**Step 3**: Write observations with evidence.
**Step 4**: Prioritize actions (Risk × Impact).
**Step 5**: Self-score (1–10). Revise if <8.
**Output ONLY the Markdown report**.

---
"""

# Default system prompt for generic dimensions
DEFAULT_SYSTEM_PROMPT = "You are a data governance expert writing a professional report analyzing survey responses with scores on a 1-10 scale. Write in a formal, report-style format suitable for executive review. Use third-person perspective. DO NOT use first person (I, we) or ask questions. DO NOT include interactive elements like 'Let me analyze' or 'Would you like'. Provide clear, actionable insights in markdown format with proper headers, bullet points, and line breaks."

# Default user prompt template for generic dimensions
DEFAULT_USER_PROMPT_TEMPLATE = """
Provide a concise summary of the current state and actionable suggestions for improvement.
"""
