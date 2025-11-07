"""
Dimension-specific system and user prompts for LLM analysis
"""

from .base_prompts import PROMPT_ADD_ON

# Maturity Analysis Template - Comprehensive framework-based assessment
MATURITY_ANALYSIS_TEMPLATE = """
---

###  Maturity Analysis & Framework Validation

**CRITICAL INSTRUCTION**: This section must leverage the industry frameworks and best practices provided in the RAG context above. Validate survey findings against established maturity models (DAMA-DMBOK, Gartner EIM, CMMI/DMM, ISO standards) and provide evidence-based maturity assessment.

#### Maturity Framework Mapping

Based on survey scores, comments, and alignment with industry frameworks from the knowledge base, assess organizational maturity across multiple dimensions:

| Framework | Current Maturity Level | Score (1-5) | Key Evidence from Survey | Alignment Assessment |
|-----------|----------------------|-------------|--------------------------|---------------------|
| **DAMA-DMBOK** | [Initial/Repeatable/Defined/Managed/Optimized] | [X.X/5] | [Cite specific Q# and scores] | [Strong/Moderate/Weak alignment with framework principles] |
| **Gartner EIM** | [Awareness/Reactive/Intentional/Managed/Effective] | [X.X/5] | [Cite specific Q# and scores] | [Assessment of EIM stage characteristics] |
| **CMMI/DMM** | [Initial/Managed/Defined/Quantitatively Managed/Optimizing] | [X.X/5] | [Cite specific Q# and scores] | [Process maturity indicators] |
| **ISO Standards** | [Ad-hoc/Repeatable/Defined/Managed/Optimized] | [X.X/5] | [Cite specific Q# and scores] | [Compliance and control maturity] |

**Composite Maturity Score**: [X.X/5.0] - [Maturity Level Name]

#### Detailed Maturity Characteristics

**Current State Assessment** (based on survey evidence and framework alignment):

1. **Process Maturity**
   - **Formalization Level**: [Ad-hoc / Documented / Standardized / Measured / Optimized]
     - Evidence: [Reference specific questions, scores, and comments]
     - Framework alignment: [How this aligns with DAMA-DMBOK/CMMI levels]
   - **Automation & Tooling**: [X% automated based on survey responses]
     - Gaps identified: [List 3-5 automation gaps with Q# references]
     - Industry benchmark comparison: [Compare to framework recommendations]

2. **Governance Maturity**
   - **Policy & Standards**: [Absent / Emerging / Established / Enforced / Continuously Improved]
     - Evidence: [Q#s, scores, comment themes]
     - Framework validation: [Against DAMA-DMBOK governance principles]
   - **Roles & Accountability**: [Clarity level and enforcement]
     - Survey findings: [Specific evidence]
     - Best practice gap: [What frameworks recommend vs. current state]

3. **Capability Maturity**
   - **Skills & Competency**: [Assessment based on execution quality indicators]
     - Evidence from survey: [Pattern analysis from comments and scores]
     - Training needs: [Identified gaps vs. framework requirements]
   - **Technology Enablement**: [Tool sophistication and integration]
     - Current state: [Based on survey responses about tools/processes]
     - Target state: [What frameworks recommend]

4. **Cultural Maturity**
   - **Data Awareness**: [Organizational understanding and prioritization]
     - Indicators: [From comment analysis and score patterns]
   - **Continuous Improvement**: [Evidence of proactive vs. reactive approaches]
     - Survey evidence: [Specific examples]
     - Framework comparison: [Against mature organization characteristics]

#### Maturity Gap Analysis

Identify critical gaps between current state and framework-defined target state:

| Gap Category | Current Capability | Framework Target | Gap Severity | Business Impact | Evidence (Q#) |
|--------------|-------------------|------------------|--------------|-----------------|---------------|
| [Process/Governance/Technology/People] | [Description] | [What framework prescribes] | Critical/High/Medium/Low | [Specific impact] | [Q#s] |

**Top 5 Maturity Gaps** (Prioritized by risk and impact):

1. **[Gap Name]**: [Detailed description]
   - **Current State**: [What survey reveals - cite Q#, scores, comments]
   - **Framework Requirement**: [What DAMA-DMBOK/Gartner/CMMI prescribes]
   - **Gap Impact**: [Regulatory risk / Operational inefficiency / Data quality impact / etc.]
   - **Remediation Complexity**: [Low/Medium/High - with justification]
   - **Business Consequence if Unaddressed**: [Specific risks and costs]

2. **[Gap Name]**: [Continue pattern for all 5 gaps]

#### Maturity Progression Strategy

**Strategic Roadmap for Maturity Advancement** (aligned with framework progression paths):

##### Phase 1: Foundation Building (0-6 months) - Moving from [Current Level] to [Next Level]

**Objective**: [Specific maturity level advancement goal with framework reference]

**Critical Initiatives**:

1. **[Initiative Name]** - Priority: HIGH
   - **Description**: [Detailed action with specific deliverables]
   - **Framework Alignment**:
     - DAMA-DMBOK: [Specific principle/practice reference]
     - Gartner EIM: [Stage advancement requirement]
     - ISO Standard: [Control/requirement reference]
   - **Key Actions**:
     - Action 1: [Specific, measurable task]
     - Action 2: [Specific, measurable task]
     - Action 3: [Specific, measurable task]
   - **Resources Required**:
     - **People**: [Roles, FTE count]
     - **Technology**: [Tools, platforms - with specific recommendations]
     - **Budget**: [Estimated range with justification]
   - **Success Metrics**:
     - Metric 1: [Baseline → Target with measurement method]
     - Metric 2: [Baseline → Target with measurement method]
   - **Dependencies**: [What must be in place first]
   - **Risk Mitigation**: [Key risks and mitigation strategies]
   - **Expected Outcome**: [Tangible improvement with business value]

2. **[Initiative Name]** - Priority: HIGH
   [Continue same detailed structure]

3. **[Initiative Name]** - Priority: MEDIUM
   [Continue same detailed structure]

##### Phase 2: Capability Enhancement (6-12 months) - Advancing to [Target Level]

**Objective**: [Specific maturity level advancement goal]

**Key Initiatives**:

1. **[Initiative Name]** - Priority: HIGH
   [Same detailed structure as Phase 1]

2. **[Initiative Name]** - Priority: MEDIUM
   [Same detailed structure]

##### Phase 3: Optimization & Excellence (12-24 months) - Achieving [Advanced Level]

**Objective**: [Specific maturity level advancement goal]

**Key Initiatives**:

1. **[Initiative Name]** - Priority: MEDIUM
   [Same detailed structure]

2. **[Initiative Name]** - Priority: MEDIUM
   [Same detailed structure]

#### Maturity Progression Metrics & KPIs

Define quantitative indicators to track maturity advancement over time:

| Metric Category | Metric Name | Current Baseline | 6-Month Target | 12-Month Target | 24-Month Target | Measurement Method | Framework Reference |
|----------------|-------------|------------------|----------------|-----------------|-----------------|-------------------|---------------------|
| **Survey Scores** | Overall Dimension Average | [X.X/10] | [X.X/10] | [X.X/10] | [X.X/10] | Survey analytics | All frameworks |
| **Survey Scores** | % Scores ≥ 8 (High Performance) | [X%] | [X%] | [X%] | [X%] | Score distribution | Maturity threshold |
| **Survey Scores** | % Scores ≤ 4 (Critical Gaps) | [X%] | [X%] | [X%] | [X%] | Score distribution | Risk indicator |
| **Process Automation** | % Processes Automated | [X%] | [X%] | [X%] | [X%] | Process inventory | CMMI/DMM |
| **Governance** | Policy Compliance Rate | [X%] | [X%] | [X%] | [X%] | Audit findings | DAMA-DMBOK |
| **Data Quality** | [Dimension-specific metric] | [Baseline] | [Target] | [Target] | [Target] | [Method] | ISO 8000 |
| **Technology** | Tool Coverage/Integration | [X%] | [X%] | [X%] | [X%] | Technology audit | Gartner EIM |
| **Skills** | Certified Practitioners | [Count] | [Target] | [Target] | [Target] | Training records | DAMA/CDMP |
| **Culture** | Data Awareness Score | [X/10] | [X/10] | [X/10] | [X/10] | Culture survey | Organizational maturity |

**Leading Indicators** (Early warning/progress signals):
- [Indicator 1]: [Description and target trend]
- [Indicator 2]: [Description and target trend]
- [Indicator 3]: [Description and target trend]

**Lagging Indicators** (Outcome measures):
- [Indicator 1]: [Description and target outcome]
- [Indicator 2]: [Description and target outcome]

#### Maturity Benchmarking & Industry Comparison

**Industry Context** (based on framework research and standards):

- **Peer Comparison**: Organizations at [Similar Maturity Level] typically exhibit:
  - [Characteristic 1 with reference to frameworks]
  - [Characteristic 2 with reference to frameworks]
  - [Characteristic 3 with reference to frameworks]

- **Best-in-Class Characteristics** (from framework definitions):
  - [Characteristic 1 - what optimized/effective organizations do]
  - [Characteristic 2]
  - [Characteristic 3]

- **Gap to Industry Leaders**: [Analysis of what separates current state from excellence]

#### Critical Success Factors for Maturity Advancement

Based on framework research and industry best practices:

1. **[Success Factor 1]**: [Why it's critical, how to achieve it, framework reference]
2. **[Success Factor 2]**: [Why it's critical, how to achieve it, framework reference]
3. **[Success Factor 3]**: [Why it's critical, how to achieve it, framework reference]
4. **[Success Factor 4]**: [Why it's critical, how to achieve it, framework reference]
5. **[Success Factor 5]**: [Why it's critical, how to achieve it, framework reference]

#### Maturity-Related Risks & Mitigation

**Risks of Remaining at Current Maturity Level**:

| Risk | Likelihood | Impact | Business Consequence | Mitigation Strategy | Timeline |
|------|-----------|--------|---------------------|-------------------|----------|
| [Risk 1] | High/Medium/Low | Critical/High/Medium | [Specific consequence] | [Strategy] | [Urgency] |

**Change Management Considerations**:
- **Organizational Readiness**: [Assessment]
- **Stakeholder Alignment**: [Requirements for buy-in]
- **Resource Availability**: [Constraints and solutions]
- **Cultural Barriers**: [Identified resistance points and strategies]

#### Framework-Specific Recommendations

**DAMA-DMBOK Alignment**:
- Current positioning: [Level and justification]
- Priority practices to adopt: [List 3-5 with references]
- Knowledge areas needing focus: [Specific DMBOK knowledge areas]

**Gartner EIM Progression**:
- Current stage assessment: [Stage and characteristics]
- Next stage requirements: [What's needed to advance]
- Strategic priorities: [Aligned with Gartner recommendations]

**CMMI/DMM Application**:
- Process areas assessment: [Current maturity by process area]
- Improvement priorities: [Which process areas to focus on]
- Capability building: [Specific CMMI practices to implement]

**ISO Standards Compliance**:
- Current compliance gaps: [Against relevant ISO standards]
- Certification readiness: [Assessment]
- Compliance roadmap: [Steps toward full compliance]

#### Executive Summary: Maturity Analysis

**Maturity Verdict**: [Overall assessment in 2-3 sentences]

**Key Findings**:
1. [Finding 1 with framework validation]
2. [Finding 2 with framework validation]
3. [Finding 3 with framework validation]

**Strategic Imperatives** (Top 3 actions to advance maturity):
1. [Imperative 1]: [Why critical, expected impact, framework alignment]
2. [Imperative 2]: [Why critical, expected impact, framework alignment]
3. [Imperative 3]: [Why critical, expected impact, framework alignment]

**Expected Outcomes** (if roadmap executed):
- **6 months**: [Maturity level, key improvements]
- **12 months**: [Maturity level, key improvements]
- **24 months**: [Maturity level, key improvements]
- **Business Value**: [Quantified benefits - risk reduction, efficiency gains, compliance, revenue protection]

---
"""

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

###  Organizational Maturity Assessment

Evaluate the organization's maturity level in this dimension using established maturity models:

#### Maturity Level Analysis
Map current survey scores and themes to maturity levels from multiple frameworks:

| Framework | Current Level | Key Indicators | Maturity Score (1-5) |
|-----------|---------------|----------------|---------------------|
| **DAMA-DMBOK** | [Initial/Repeatable/Defined/Managed/Optimized] | [Evidence from survey] | [X/5] |
| **Gartner EIM** | [Awareness/Reactive/Intentional/Managed/Effective] | [Evidence from survey] | [X/5] |
| **CMMI/DMM** | [Initial/Managed/Defined/Quantitatively Managed/Optimizing] | [Evidence from survey] | [X/5] |

**Overall Maturity Assessment**: [X.X/5.0]

#### Maturity Level Description
- **Current State**: [Detailed description of current maturity based on survey scores]
  - Avg score of X.X indicates [maturity level]
  - Key characteristics observed: [list 3-5 observations]
  - Alignment with maturity models: [explain positioning]

#### Gap Analysis
Identify gaps between current and target maturity levels:

| Gap Area | Current Capability | Target Capability | Priority | Impact |
|----------|-------------------|-------------------|----------|--------|
| [Area] | [Description] | [Description] | High/Med/Low | [Impact description] |

**Critical Gaps** (Top 3-5):
1. **[Gap Name]**: [Description, evidence from survey, impact]
2. **[Gap Name]**: [Description, evidence from survey, impact]
3. **[Gap Name]**: [Description, evidence from survey, impact]

#### Maturity Progression Roadmap

**Short-term (0-6 months) - Moving to Next Level**:
1. **[Action]**: [Description, expected outcome, success criteria]
   - Framework alignment: [DAMA/Gartner/CMMI reference]
   - Resources needed: [people, tools, budget]
   - Success metrics: [KPIs]

2. **[Action]**: [Description, expected outcome, success criteria]
   - Framework alignment: [DAMA/Gartner/CMMI reference]
   - Resources needed: [people, tools, budget]
   - Success metrics: [KPIs]

**Medium-term (6-12 months) - Advancing Maturity**:
1. **[Action]**: [Description, expected outcome, success criteria]
   - Framework alignment: [DAMA/Gartner/CMMI reference]
   - Resources needed: [people, tools, budget]
   - Success metrics: [KPIs]

**Long-term (12-24 months) - Achieving Excellence**:
1. **[Action]**: [Description, expected outcome, success criteria]
   - Framework alignment: [DAMA/Gartner/CMMI reference]
   - Resources needed: [people, tools, budget]
   - Success metrics: [KPIs]

#### Maturity Success Indicators
Define measurable indicators for tracking maturity progression:

| Indicator | Current Value | Target (6mo) | Target (12mo) | Target (24mo) |
|-----------|--------------|--------------|---------------|---------------|
| Avg Survey Score | [X.X] | [X.X] | [X.X] | [X.X] |
| % Scores ≥8 | [X%] | [X%] | [X%] | [X%] |
| Process Automation | [X%] | [X%] | [X%] | [X%] |
| Policy Compliance | [X%] | [X%] | [X%] | [X%] |

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

### 8. Maturity Analysis & Framework Validation
**CRITICAL**: Leverage the RAG-provided industry frameworks and best practices to conduct a comprehensive maturity assessment. This section must validate survey findings against DAMA-DMBOK, Gartner EIM, CMMI/DMM, ISO 27701, GDPR, CCPA, NIST Privacy Framework, and other relevant standards provided in the knowledge base context above.
""" + MATURITY_ANALYSIS_TEMPLATE + COMMON_DEEP_ANALYSIS_TEMPLATE

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

### 8. Maturity Analysis & Framework Validation
**CRITICAL**: Leverage the RAG-provided industry frameworks and best practices to conduct a comprehensive maturity assessment. This section must validate survey findings against DAMA-DMBOK, Gartner EIM, CMMI/DMM, AI Ethics Guidelines, IEEE Ethically Aligned Design, and other relevant standards provided in the knowledge base context above.
""" + MATURITY_ANALYSIS_TEMPLATE + COMMON_DEEP_ANALYSIS_TEMPLATE

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

### 8. Maturity Analysis & Framework Validation
**CRITICAL**: Leverage the RAG-provided industry frameworks and best practices to conduct a comprehensive maturity assessment. This section must validate survey findings against DAMA-DMBOK, Gartner EIM, CMMI/DMM, data provenance standards, lineage best practices, and other relevant standards provided in the knowledge base context above.
""" + MATURITY_ANALYSIS_TEMPLATE + COMMON_DEEP_ANALYSIS_TEMPLATE

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

### 8. Maturity Analysis & Framework Validation
**CRITICAL**: Leverage the RAG-provided industry frameworks and best practices to conduct a comprehensive maturity assessment. This section must validate survey findings against DAMA-DMBOK, Gartner EIM, CMMI/DMM, NIST Cybersecurity Framework, ISO 27001, CIS Controls, and other relevant standards provided in the knowledge base context above.
""" + MATURITY_ANALYSIS_TEMPLATE + COMMON_DEEP_ANALYSIS_TEMPLATE

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

### 8. Maturity Analysis & Framework Validation
**CRITICAL**: Leverage the RAG-provided industry frameworks and best practices to conduct a comprehensive maturity assessment. This section must validate survey findings against DAMA-DMBOK, Gartner EIM, CMMI/DMM, metadata management standards (Dublin Core, etc.), data catalog best practices, and other relevant standards provided in the knowledge base context above.
""" + MATURITY_ANALYSIS_TEMPLATE + COMMON_DEEP_ANALYSIS_TEMPLATE

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
