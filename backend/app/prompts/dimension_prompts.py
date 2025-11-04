"""
Dimension-specific system and user prompts for LLM analysis
"""

from .base_prompts import PROMPT_ADD_ON

# Common template sections used across dimensions
COMMON_DEEP_ANALYSIS_TEMPLATE = """
### DEEP DRILL-DOWN REQUIRED ###

### Analysis for every category

###  Current State
- **Overall Mean Score**: [Calculate from all responses]
- **Median Score**: [Calculate]
- **% of Scores ≥7**: [Calculate]
- **% of Scores ≤3**: [Calculate]
- **Maturity Level**: [Critical / Low / Medium / High / Excellent]
- **Executive Summary (3–6 bullets)**:
  - Each bullet must cite a score, % or comment
  - Link to a framework (DAMA-DMBOK, GDPR, ISO 8000, NIST, etc.)
  - Be consultative and forward-looking

---

###  Analysis by Category
For **each Category** (e.g., Accuracy, Completeness, Timeliness):

| Category | Avg Score | % High (8–10) | % Low (1–4) | Questions |
|---------|-----------|---------------|-------------|---------|
| ...     | ...       | ...           | ...         | Q1, Q7  |

####  [Category Name] — Deep Analysis
- **Score Breakdown**: Avg = X.X, Min = X, Max = X
- **Comment Analysis** (quote 3–5 key comments):
  - "Quote" → [Sentiment: Positive/Negative] → [Theme: e.g., Manual Entry]
- **Best Practices (3–6)**:
  - Cite DAMA-DMBOK, ISO 8000, GDPR Art. 5(1)(d), etc.
- **Observations (3–6)**:
  - Link survey evidence to gaps
- **Areas for Improvement (3–6)**:
  - Be specific and technical
- **Action Items (3–8)**:
  | Action | Priority | Owner | Timeline | Tool Example | Framework Ref |
  |-------|----------|-------|----------|--------------|---------------|
  | ...   | High     | Data Eng | Q1 2026  | Great Expectations | DAMA-DMBOK #3 |

---
*** DEEP DRILL-DOWN REQUIRED ***
###  Analysis by Process
For **each Process** (e.g., Data Ingestion, Cleansing, Monitoring):

| Process | Avg Score | Key Gaps (3–5) | Recommended Tools |
|--------|-----------|----------------|-------------------|
| ...    | ...       | ...            | ...               |

####  [Process Name] — Deep Analysis
- **Score & Questions**: List Q#s, avg score
- **Comment Analysis**: Quote + sentiment + theme
- **Best Practices (3–6)**
- **Observations (3–6)**
- **Areas for Improvement (3–6)**
- **Action Items (3–8)**: Same table format

---
### DEEP DRILL-DOWN REQUIRED ###
###   Analysis by Lifecycle Stage
For **each Stage** (e.g., Creation, Usage, Archival):

| Stage | Avg Score | Maturity Note |
|-------|-----------|----------------|
| ...   | ...       | Strong in monitoring, weak in prevention |

####  [Stage Name] — Deep Analysis
- **Score Trend**: Compare to other stages
- **Comment Analysis**
- **Best Practices (3–6)**
- **Observations (3–6)**
- **Areas for Improvement (3–6)**
- **Action Items (3–8)**

---

###  Priority Actions (Risk × Impact)
| Rank | Initiative | Risk Severity | Business Impact | RICE Score | Linked Qs |
|------|------------|---------------|-----------------|------------|----------|
| 1    | Deploy cross-system reconciliation | High | High | 9 | Q1, Q16 |

- **RICE Score** = (Reach × Impact × Confidence) ÷ Effort
- **Top 3 must be High priority**
- **Phrase as "Initiative"** (e.g., "Embed data quality criteria in SDLC acceptance checkpoints")

---

###  Actionable Improvement Suggestions
- **One concrete, tool-enabled fix per major gap**
- **Format**:
  **→ [Gap Title]**
  - **Recommendation**: [Detailed]
  - **Tool Example**: Great Expectations, Apache Deequ, Collibra
  - **Owner Role**: Data Steward, CDO
  - **Timeline**: Immediate / Q1 / Q2 / Long-term
  - **Framework Reference**: DAMA-DMBOK, ISO 8000-8
  - **Expected ROI**: Reduce error rate by 60%, save $XM

---

###  Strategic Observations
- **4–8 bullets**
- Each must:
  - Cite a survey finding (Q# + score)
  - Link to a framework
  - Offer a strategic insight
- Example:
  > "Q1 score=4 indicates no automated reconciliation — violates **DAMA-DMBOK Principle #3 (Accuracy)** and increases **GDPR Art. 5(1)(d)** risk."

---

###  Question-Level Analysis
| Q# | Question | Category | Process | Stage | Responses | Min | Max | Avg | Comments |
|----|---------|----------|---------|-------|-----------|-----|-----|-----|----------|
| Q1 | Are automated reconciliation checks... | Accuracy | Ingestion | Creation | 1 | 4 | 4 | 4 | "Dates flip formats" |

- **Include all  questions**
- **Quote 1–2 comments per low-scoring Q (<5)**

---

###  Risk Spotlight
| Risk | Severity | Regulatory Risk | Mitigation Urgency | Linked Qs |
|------|----------|-----------------|---------------------|----------|
| Inaccurate billing data | Critical | GDPR Art. 5(1)(d) | Immediate | Q1, Q7 |

- **At least 3 risks**
- **Severity**: Critical / High / Medium / Low
- **Urgency**: Immediate / Short-term / Long-term

---

###  Self-Assessment (AI Quality Gate)
- **Clarity**: [1–10]
- **Actionability**: [1–10]
- **Evidence-Based**: [1–10]
- **Framework Alignment**: [1–10]
- **Depth of Analysis**: [1–10]
- **Average Score**: [X.X]
- **Revision Needed?**: Yes / No
- **Revision Notes**: [If <8.5, explain what to fix]

### REPLY ONLY IN MARKDOWN FORMAT ###
### END OF PROMPT ###
---
"""

# Data Privacy & Compliance
DATA_PRIVACY_COMPLIANCE_SYSTEM_PROMPT = PROMPT_ADD_ON + "You are a **senior data management consultant** specializing in Data Privacy & Compliance. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."

DATA_PRIVACY_COMPLIANCE_USER_PROMPT = """
Generate a report with the following sections based on the provided survey data.
Use clear headings, tables, and bullet points for optimal readability.


# Data Privacy & Compliance – Survey Analysis Report

### 1. Executive Summary
- Average score & distribution
- Top 3 themes from comments
- Overall maturity level (High / Medium / Low)

### 2. Performance by Category
- Create a table with columns: **Category**, Avg Score, % High (8–10), % Low (1–4), Key Comment Themes
- Highlight top-performing and at-risk categories

### 3. Performance by Process
- Create a table with columns: **Process**, Avg Score, Key Gaps, Recommended Tools/Methods

### 4. Performance by Lifecycle Stage
- Visualize maturity progression (e.g., strong in Monitoring, weak in Prevention)

### 5. Strategic Observations
- 3–5 bullet points with **consultative insights**
- Link survey findings to industry frameworks (e.g., GDPR, CCPA, ISO 27701, NIST Privacy)

### 6. Prioritized Action Plan
- Create a table with columns: Priority, Action Item, Owner, Timeline, Expected Outcome
- Provide at least one 'High' priority action.

### 7. Risk Spotlight
- Identify critical risks (e.g., non-compliance, breach exposure)
- Assign a mitigation urgency: Immediate / Short-term / Long-term
""" + COMMON_DEEP_ANALYSIS_TEMPLATE

# Data Ethics & Bias
DATA_ETHICS_BIAS_SYSTEM_PROMPT = PROMPT_ADD_ON + "You are a **senior data management consultant** specializing in Data Ethics & Bias. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."

DATA_ETHICS_BIAS_USER_PROMPT = """
Generate a report with the following sections based on the provided survey data. Use clear headings, tables, and bullet points for optimal readability.

# Data Ethics & Bias – Survey Analysis Report

### 1. Executive Summary
- Average score & distribution
- Top 3 themes from comments
- Overall maturity level (High / Medium / Low)

### 2. Performance by Category
- Create a table with columns: **Category**, Avg Score, % High (8–10), % Low (1–4), Key Comment Themes
- Highlight top-performing and at-risk categories

### 3. Performance by Process
- Create a table with columns: **Process**, Avg Score, Key Gaps, Recommended Tools/Methods

### 4. Performance by Lifecycle Stage
- Visualize maturity progression (e.g., strong in Monitoring, weak in Prevention)

### 5. Strategic Observations
- 3–5 bullet points with **consultative insights**
- Link survey findings to industry frameworks (e.g., AI Ethics Guidelines, IEEE Ethically Aligned Design)

### 6. Prioritized Action Plan
- Create a table with columns: Priority, Action Item, Owner, Timeline, Expected Outcome
- Provide at least one 'High' priority action.

### 7. Risk Spotlight
- Identify critical risks (e.g., bias amplification, ethical lapses)
- Assign a mitigation urgency: Immediate / Short-term / Long-term
""" + COMMON_DEEP_ANALYSIS_TEMPLATE

# Data Lineage & Traceability
DATA_LINEAGE_TRACEABILITY_SYSTEM_PROMPT = PROMPT_ADD_ON + "You are a **senior data management consultant** specializing in Data Lineage & Traceability. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."

DATA_LINEAGE_TRACEABILITY_USER_PROMPT = """
Generate a report with the following sections based on the provided survey data. Use clear headings, tables, and bullet points for optimal readability.

# Data Lineage & Traceability – Survey Analysis Report

### 1. Executive Summary
- Average score & distribution
- Top 3 themes from comments
- Overall maturity level (High / Medium / Low)

### 2. Performance by Category
- Create a table with columns: **Category**, Avg Score, % High (8–10), % Low (1–4), Key Comment Themes
- Highlight top-performing and at-risk categories

### 3. Performance by Process
- Create a table with columns: **Process**, Avg Score, Key Gaps, Recommended Tools/Methods

### 4. Performance by Lifecycle Stage
- Visualize maturity progression (e.g., strong in Monitoring, weak in Prevention)

### 5. Strategic Observations
- 3–5 bullet points with **consultative insights**
- Link survey findings to industry frameworks (e.g., DAMA-DMBOK, data provenance standards)

### 6. Prioritized Action Plan
- Create a table with columns: Priority, Action Item, Owner, Timeline, Expected Outcome
- Provide at least one 'High' priority action.

### 7. Risk Spotlight
- Identify critical risks (e.g., incomplete audit trails, traceability gaps)
- Assign a mitigation urgency: Immediate / Short-term / Long-term
""" + COMMON_DEEP_ANALYSIS_TEMPLATE

# Data Security & Access
DATA_SECURITY_ACCESS_SYSTEM_PROMPT = PROMPT_ADD_ON + "You are a **senior data management consultant** specializing in Data Security & Access. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."

DATA_SECURITY_ACCESS_USER_PROMPT = """
Generate a report with the following sections based on the provided survey data. Use clear headings, tables, and bullet points for optimal readability.

# Data Security & Access – Survey Analysis Report

### 1. Executive Summary
- Average score & distribution
- Top 3 themes from comments
- Overall maturity level (High / Medium / Low)

### 2. Performance by Category
- Create a table with columns: **Category**, Avg Score, % High (8–10), % Low (1–4), Key Comment Themes
- Highlight top-performing and at-risk categories

### 3. Performance by Process
- Create a table with columns: **Process**, Avg Score, Key Gaps, Recommended Tools/Methods

### 4. Performance by Lifecycle Stage
- Visualize maturity progression (e.g., strong in Monitoring, weak in Prevention)

### 5. Strategic Observations
- 3–5 bullet points with **consultative insights**
- Link survey findings to industry frameworks (e.g., ISO 27001, NIST Cybersecurity Framework)

### 6. Prioritized Action Plan
- Create a table with columns: Priority, Action Item, Owner, Timeline, Expected Outcome
- Provide at least one 'High' priority action.

### 7. Risk Spotlight
- Identify critical risks (e.g., unauthorized access, data breaches)
- Assign a mitigation urgency: Immediate / Short-term / Long-term
""" + COMMON_DEEP_ANALYSIS_TEMPLATE

# Metadata & Documentation
METADATA_DOCUMENTATION_SYSTEM_PROMPT = PROMPT_ADD_ON + "You are a **senior data management consultant** specializing in Metadata & Documentation. Your output must be a professionally crafted, consultative,executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."

METADATA_DOCUMENTATION_USER_PROMPT = """
Generate a report with the following sections based on the provided survey data. Use clear headings, tables, and bullet points for optimal readability.

# Metadata & Documentation – Survey Analysis Report

### 1. Executive Summary
- Average score & distribution
- Top 3 themes from comments
- Overall maturity level (High / Medium / Low)

### 2. Performance by Category
- Create a table with columns: **Category**, Avg Score, % High (8–10), % Low (1–4), Key Comment Themes
- Highlight top-performing and at-risk categories

### 3. Performance by Process
- Create a table with columns: **Process**, Avg Score, Key Gaps, Recommended Tools/Methods

### 4. Performance by Lifecycle Stage
- Visualize maturity progression (e.g., strong in Monitoring, weak in Prevention)

### 5. Strategic Observations
- 3–5 bullet points with **consultative insights**
- Link survey findings to industry frameworks (e.g., DAMA-DMBOK, metadata schemas like Dublin Core)

### 6. Prioritized Action Plan
- Create a table with columns: Priority, Action Item, Owner, Timeline, Expected Outcome
- Provide at least one 'High' priority action.

### 7. Risk Spotlight
- Identify critical risks (e.g., poor data discoverability, compliance issues)
- Assign a mitigation urgency: Immediate / Short-term / Long-term
""" + COMMON_DEEP_ANALYSIS_TEMPLATE

# Dictionary mapping dimension names to their prompts
DIMENSION_PROMPTS = {
    "Data Privacy & Compliance": {
        "system": DATA_PRIVACY_COMPLIANCE_SYSTEM_PROMPT,
        "user": DATA_PRIVACY_COMPLIANCE_USER_PROMPT
    },
    "Data Ethics & Bias": {
        "system": DATA_ETHICS_BIAS_SYSTEM_PROMPT,
        "user": DATA_ETHICS_BIAS_USER_PROMPT
    },
    "Data Lineage & Traceability": {
        "system": DATA_LINEAGE_TRACEABILITY_SYSTEM_PROMPT,
        "user": DATA_LINEAGE_TRACEABILITY_USER_PROMPT
    },
    "Data Security & Access": {
        "system": DATA_SECURITY_ACCESS_SYSTEM_PROMPT,
        "user": DATA_SECURITY_ACCESS_USER_PROMPT
    },
    "Metadata & Documentation": {
        "system": METADATA_DOCUMENTATION_SYSTEM_PROMPT,
        "user": METADATA_DOCUMENTATION_USER_PROMPT
    }
}
