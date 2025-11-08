"""
Prompts for generating overall cross-dimension summary reports
"""

from .base_prompts import OVERALL_SUMMARY_PROMPT_ADD_ON

# Enterprise Maturity Analysis Template
ENTERPRISE_MATURITY_ANALYSIS = """

---

###  Enterprise Data Maturity Analysis

**CRITICAL INSTRUCTION**: This section must leverage the industry frameworks and best practices provided in the RAG context. Synthesize maturity assessments from individual dimension reports and provide a comprehensive, enterprise-wide maturity analysis validated against DAMA-DMBOK, Gartner EIM, CMMI/DMM, and other relevant frameworks from the knowledge base.

#### Comprehensive Framework-Based Maturity Assessment

**Enterprise Maturity Scorecard** (Synthesized from all dimensions):

| Dimension | DAMA-DMBOK Maturity | Gartner EIM Stage | CMMI/DMM Level | Composite Score (1-5) | Survey Avg (1-10) | Maturity Gap | Priority |
|-----------|---------------------|-------------------|----------------|---------------------|------------------|--------------|----------|
| Data Privacy & Compliance | [Initial/Repeatable/Defined/Managed/Optimized] | [Awareness/Reactive/Intentional/Managed/Effective] | [1-5] | [X.X/5] | [X.X/10] | [High/Medium/Low] | [Critical/High/Medium/Low] |
| Data Ethics & Bias | [Level] | [Stage] | [1-5] | [X.X/5] | [X.X/10] | [Gap] | [Priority] |
| Data Lineage & Traceability | [Level] | [Stage] | [1-5] | [X.X/5] | [X.X/10] | [Gap] | [Priority] |
| Data Quality | [Level] | [Stage] | [1-5] | [X.X/5] | [X.X/10] | [Gap] | [Priority] |
| Data Governance & Management | [Level] | [Stage] | [1-5] | [X.X/5] | [X.X/10] | [Gap] | [Priority] |
| Data Security & Access | [Level] | [Stage] | [1-5] | [X.X/5] | [X.X/10] | [Gap] | [Priority] |
| Metadata & Documentation | [Level] | [Stage] | [1-5] | [X.X/5] | [X.X/10] | [Gap] | [Priority] |
| Data Value & Lifecycle Mgmt | [Level] | [Stage] | [1-5] | [X.X/5] | [X.X/10] | [Gap] | [Priority] |

**Enterprise Composite Maturity Score**: [X.X/5.0] - **Maturity Level**: [Initial/Repeatable/Defined/Managed/Optimized]

**Survey-Based Performance Score**: [X.X/10]

#### Enterprise Maturity Characteristics Profile

**1. Process & Operational Maturity**

- **Standardization Level**: [Ad-hoc / Emerging / Defined / Managed / Optimized]
  - **Assessment**: [Detailed description based on cross-dimension analysis]
  - **Key Evidence**: [Reference specific dimensions, scores, and patterns]
  - **Framework Validation**: [How this aligns with DAMA-DMBOK/CMMI maturity models]

- **Automation & Technology Enablement**: [X% automated enterprise-wide]
  - **Current State**: [Description of automation maturity across dimensions]
  - **Dimension Variability**: [Identify dimensions with high/low automation]
  - **Technology Stack Maturity**: [Assessment of tools and integration]
  - **Gaps**: [List 5-7 critical automation gaps with cross-dimension impact]

- **Process Integration**: [Siloed / Partially Integrated / Integrated / Optimized]
  - **Cross-Dimension Dependencies**: [Identify key process dependencies]
  - **Integration Maturity**: [Assessment of how well processes work together]
  - **Friction Points**: [Where processes conflict or create inefficiencies]

**2. Governance & Control Maturity**

- **Policy Framework**: [Absent / Fragmented / Established / Enforced / Continuously Improved]
  - **Coverage Assessment**: [Which dimensions have strong vs. weak policies]
  - **Enforcement Maturity**: [How well policies are enforced across dimensions]
  - **Gap Analysis**: [Policy gaps with business impact]

- **Roles & Accountability**: [Undefined / Emerging / Defined / Managed / Optimized]
  - **Data Ownership**: [Maturity of ownership model across dimensions]
  - **Stewardship Program**: [Assessment of data stewardship effectiveness]
  - **Decision Rights**: [Clarity and effectiveness of decision-making authority]

- **Compliance & Risk Management**: [Reactive / Managed / Proactive / Predictive]
  - **Regulatory Compliance**: [Assessment across privacy, security, quality regulations]
  - **Risk Identification**: [Maturity of risk assessment processes]
  - **Control Environment**: [Effectiveness of controls across dimensions]

**3. Data Management Capability Maturity**

- **Data Quality Management**: [Maturity assessment]
  - **Quality Framework**: [Existence and sophistication]
  - **Measurement & Monitoring**: [Maturity of quality metrics and tracking]
  - **Remediation Processes**: [How issues are identified and resolved]

- **Metadata & Master Data Management**: [Maturity assessment]
  - **Metadata Completeness**: [Coverage and quality across enterprise]
  - **MDM Maturity**: [Master data management sophistication]
  - **Data Cataloging**: [Discovery and cataloging capabilities]

- **Data Architecture & Integration**: [Maturity assessment]
  - **Architecture Governance**: [Consistency and standardization]
  - **Integration Patterns**: [Sophistication of data integration]
  - **Technology Debt**: [Assessment of legacy systems impact]

**4. Organizational & Cultural Maturity**

- **Data Culture**: [Awareness / Reactive / Proactive / Data-Driven / Data-Led]
  - **Leadership Commitment**: [Evidence from survey and dimension analysis]
  - **Employee Engagement**: [Data awareness and adoption indicators]
  - **Cross-Functional Collaboration**: [Maturity of data collaboration]

- **Change Management Capability**: [Assessment]
  - **Organizational Readiness**: [Capacity for data transformation]
  - **Change History**: [Track record of successful data initiatives]
  - **Resistance Indicators**: [Identified barriers to advancement]

- **Skills & Competencies**: [Maturity assessment]
  - **Data Literacy**: [Enterprise-wide data skills assessment]
  - **Specialist Capabilities**: [Availability of data professionals]
  - **Training & Development**: [Investment in capability building]

#### Enterprise Maturity Gap Analysis

**Critical Cross-Dimension Gaps** (Top 10 by business impact):

| Rank | Gap Category | Description | Affected Dimensions | Current State | Target State | Business Impact | Remediation Complexity | Priority |
|------|--------------|-------------|---------------------|---------------|--------------|-----------------|----------------------|----------|
| 1 | [Gap Name] | [Detailed description] | [List dimensions] | [Current capability] | [Required capability] | [Specific business impact] | High/Medium/Low | Critical |
| 2 | [Gap Name] | [Detailed description] | [List dimensions] | [Current] | [Target] | [Impact] | [Complexity] | [Priority] |

**Detailed Gap Analysis** (Top 5):

1. **[Gap Name]**: [Category - Process/Governance/Technology/People/Culture]
   - **Description**: [Comprehensive gap description]
   - **Root Cause Analysis**: [Why this gap exists - organizational, technical, cultural factors]
   - **Affected Dimensions**: [List dimensions with severity impact per dimension]
   - **Current Capability**: [What exists today - cite survey evidence]
   - **Framework Requirement**: [What DAMA-DMBOK/Gartner/CMMI/ISO standards prescribe]
   - **Business Consequences**:
     - Revenue Impact: [Quantify or describe]
     - Risk Exposure: [Regulatory, operational, reputational]
     - Efficiency Loss: [Productivity, cost impact]
     - Strategic Limitation: [Business capability constraints]
   - **Interdependencies**: [What else must be addressed to close this gap]
   - **Remediation Approach**: [High-level strategy to address]
   - **Success Indicators**: [How to measure gap closure]

[Continue pattern for gaps 2-5]

#### Enterprise Maturity Advancement Strategy

**Strategic Vision**: [2-3 sentence vision for target maturity state]

**Maturity Progression Roadmap** (Aligned with framework progression paths):

##### Phase 1: Foundation & Stabilization (0-6 months)
**Objective**: Advance from [Current Enterprise Level] to [Next Level] by addressing critical foundations

**Strategic Priorities**:

1. **[Cross-Cutting Initiative 1]** - Priority: CRITICAL
   - **Description**: [Detailed description of initiative]
   - **Affected Dimensions**: [List with specific impact per dimension]
   - **Framework Alignment**:
     - **DAMA-DMBOK**: [Specific knowledge areas/principles]
     - **Gartner EIM**: [Stage advancement requirements]
     - **CMMI/DMM**: [Process areas and practices]
   - **Key Deliverables**:
     1. [Deliverable with success criteria]
     2. [Deliverable with success criteria]
     3. [Deliverable with success criteria]
   - **Resource Requirements**:
     - **Leadership**: [C-level sponsor, steering committee]
     - **People**: [Roles, FTE count, skills needed]
     - **Technology**: [Tools, platforms, infrastructure]
     - **Budget**: [Estimated investment with breakdown]
   - **Dependencies & Prerequisites**: [What must be in place]
   - **Risk & Mitigation**:
     - Risk 1: [Risk description] → [Mitigation strategy]
     - Risk 2: [Risk description] → [Mitigation strategy]
   - **Success Metrics**:
     | Metric | Baseline | 3-Month Target | 6-Month Target | Measurement |
     |--------|----------|----------------|----------------|-------------|
     | [Metric 1] | [Current] | [Target] | [Target] | [Method] |
   - **Expected Outcomes**: [Tangible improvements with business value]

2. **[Cross-Cutting Initiative 2]** - Priority: HIGH
   [Same detailed structure]

3. **[Cross-Cutting Initiative 3]** - Priority: HIGH
   [Same detailed structure]

##### Phase 2: Capability Building & Integration (6-12 months)
**Objective**: Advance to [Target Level] through capability enhancement and integration

**Strategic Priorities**:

1. **[Cross-Cutting Initiative 1]** - Priority: HIGH
   [Same detailed structure as Phase 1]

2. **[Cross-Cutting Initiative 2]** - Priority: MEDIUM
   [Same detailed structure]

3. **[Cross-Cutting Initiative 3]** - Priority: MEDIUM
   [Same detailed structure]

##### Phase 3: Optimization & Excellence (12-24 months)
**Objective**: Achieve [Excellence Level] through optimization and innovation

**Strategic Priorities**:

1. **[Cross-Cutting Initiative 1]** - Priority: MEDIUM
   [Same detailed structure]

2. **[Cross-Cutting Initiative 2]** - Priority: MEDIUM
   [Same detailed structure]

#### Enterprise Maturity KPIs & Progress Tracking

**Balanced Scorecard for Maturity Progression**:

##### Strategic KPIs (Enterprise Level)

| KPI Category | Metric | Current Baseline | 6M Target | 12M Target | 24M Target | Measurement Method | Owner | Framework Ref |
|--------------|--------|------------------|-----------|------------|------------|-------------------|-------|---------------|
| **Overall Maturity** | Enterprise Maturity Score | [X.X/5] | [X.X/5] | [X.X/5] | [X.X/5] | Framework assessment | CDO | All frameworks |
| **Survey Performance** | Avg Survey Score (All Dimensions) | [X.X/10] | [X.X/10] | [X.X/10] | [X.X/10] | Survey analytics | CDO | Performance indicator |
| **Survey Performance** | % Dimensions with Avg ≥ 8 | [X%] | [X%] | [X%] | [X%] | Survey analytics | CDO | Excellence threshold |
| **Survey Performance** | % Questions with Avg < 5 | [X%] | [X%] | [X%] | [X%] | Survey analytics | CDO | Critical gaps |
| **Process Maturity** | % Processes Automated | [X%] | [X%] | [X%] | [X%] | Process inventory | COO | CMMI/DMM |
| **Governance** | Policy Coverage % | [X%] | [X%] | [X%] | [X%] | Policy audit | Chief Counsel | DAMA-DMBOK |
| **Governance** | Policy Compliance Rate | [X%] | [X%] | [X%] | [X%] | Compliance audit | CAO | DAMA-DMBOK |
| **Data Quality** | Enterprise Data Quality Score | [X.X/10] | [X.X/10] | [X.X/10] | [X.X/10] | Quality framework | Data Quality Lead | ISO 8000 |
| **Risk & Compliance** | Regulatory Compliance % | [X%] | [X%] | [X%] | [X%] | Audit findings | CCO | Regulatory |
| **Risk & Compliance** | Critical Issues Open > 30 days | [Count] | [Target] | [Target] | [Target] | Issue tracking | CDO | Risk management |
| **Technology** | Modern Tool Coverage % | [X%] | [X%] | [X%] | [X%] | Technology assessment | CTO | Gartner EIM |
| **Skills** | CDMP/DAMA Certified Staff | [Count] | [Target] | [Target] | [Target] | HR records | CHRO | DAMA |
| **Culture** | Data Literacy Score | [X/10] | [X/10] | [X/10] | [X/10] | Culture survey | CDO | Org maturity |
| **Business Value** | Data-Driven Decision % | [X%] | [X%] | [X%] | [X%] | Business survey | CEO | Value realization |

##### Operational KPIs (Dimension Level)

Track progress for each dimension using metrics defined in dimensional maturity analyses.

##### Leading Indicators (Early Warning Signals)

- [Indicator 1]: [Description, target trend, alert threshold]
- [Indicator 2]: [Description, target trend, alert threshold]
- [Indicator 3]: [Description, target trend, alert threshold]
- [Indicator 4]: [Description, target trend, alert threshold]
- [Indicator 5]: [Description, target trend, alert threshold]

##### Lagging Indicators (Outcome Measures)

- [Indicator 1]: [Description, target outcome, measurement frequency]
- [Indicator 2]: [Description, target outcome, measurement frequency]
- [Indicator 3]: [Description, target outcome, measurement frequency]

**Progress Review Cadence**:
- **Monthly**: Tactical KPI review, initiative progress check
- **Quarterly**: Strategic KPI review, maturity re-assessment
- **Annual**: Comprehensive maturity audit, roadmap adjustment

#### Cross-Dimension Maturity Insights

**Maturity Pattern Analysis**:

1. **Dimensional Clustering**: [Identify dimensions at similar maturity levels]
   - **High Maturity Cluster**: [Dimensions, common characteristics, success factors]
   - **Medium Maturity Cluster**: [Dimensions, common characteristics, improvement areas]
   - **Low Maturity Cluster**: [Dimensions, common characteristics, critical needs]

2. **Interdependency Analysis**: [How maturity in one dimension affects others]
   - **Enabler Dimensions**: [Dimensions whose improvement unlocks others]
   - **Constraint Dimensions**: [Dimensions currently limiting overall advancement]
   - **Synergy Opportunities**: [Where joint improvements create multiplicative value]

3. **Maturity Imbalances**: [Identify harmful gaps between dimensions]
   - **Risk Imbalances**: [e.g., High data usage but low governance]
   - **Efficiency Imbalances**: [e.g., Good processes but poor tools]
   - **Strategic Imbalances**: [Misalignment with business strategy]

**Root Cause Analysis** (Why maturity is at current level):

- **Historical Factors**: [Organizational history, past decisions]
- **Cultural Factors**: [Data culture, leadership support]
- **Structural Factors**: [Org structure, funding, governance]
- **Technical Factors**: [Legacy systems, technical debt]
- **External Factors**: [Industry, regulatory environment, market pressures]

#### Industry Benchmarking & Best Practices

**Peer Comparison** (Based on framework research):

- **Industry Positioning**: Organizations in [Industry] at [Similar Maturity Level] typically:
  - [Characteristic 1 with framework reference]
  - [Characteristic 2 with framework reference]
  - [Characteristic 3 with framework reference]

- **Competitive Intelligence**: [How maturity compares to competitors/peers]
  - **Leaders**: [What industry leaders demonstrate]
  - **Fast Followers**: [Typical characteristics at next maturity level]
  - **Laggards**: [Characteristics to avoid]

**Best-in-Class Capabilities** (From framework definitions):

1. **[Capability Area]**: [What optimized organizations do]
   - Framework reference: [DAMA/Gartner/CMMI]
   - Gap to best-in-class: [Assessment]
   - Path to excellence: [High-level approach]

[Continue for 3-5 key capability areas]

#### Critical Success Factors for Enterprise Maturity

Based on framework research and consulting best practices:

1. **[Success Factor 1]**: [Factor name and description]
   - **Why Critical**: [Importance to maturity advancement]
   - **Current State**: [Assessment]
   - **How to Achieve**: [Specific actions]
   - **Framework Reference**: [Supporting evidence from frameworks]
   - **Examples**: [Real-world examples or case studies]

[Continue for 5-7 critical success factors]

#### Maturity-Related Enterprise Risks

**Strategic Risks of Remaining at Current Maturity**:

| Risk | Likelihood | Impact | Timeline | Business Consequence | Affected Dimensions | Mitigation Strategy | Investment Required |
|------|-----------|--------|----------|---------------------|---------------------|-------------------|-------------------|
| [Risk 1] | High/Med/Low | Critical/High/Med | [When risk materializes] | [Specific consequence] | [Dimensions] | [Strategy] | [Est. investment] |

**Detailed Risk Analysis** (Top 5 strategic risks):

1. **[Risk Name]**: [Category - Strategic/Operational/Regulatory/Reputational]
   - **Description**: [Comprehensive risk description]
   - **Likelihood**: [High/Medium/Low with justification]
   - **Impact**: [Critical/High/Medium with quantification if possible]
   - **Affected Dimensions**: [List with severity per dimension]
   - **Business Consequences**:
     - Financial: [Revenue loss, cost increase, fines]
     - Operational: [Service disruptions, inefficiencies]
     - Regulatory: [Compliance violations, penalties]
     - Reputational: [Brand damage, customer trust]
     - Strategic: [Market position, competitive disadvantage]
   - **Triggering Conditions**: [What would cause this risk to materialize]
   - **Early Warning Indicators**: [How to detect risk escalation]
   - **Mitigation Strategy**: [Approach to reduce/eliminate risk]
   - **Contingency Plan**: [Response if risk materializes]
   - **Investment Required**: [Cost of mitigation vs. cost of risk]

[Continue for risks 2-5]

#### Change Management & Organizational Readiness

**Readiness Assessment**:

- **Leadership Alignment**: [Assessment of C-suite commitment]
  - Current state: [Evidence from survey and organizational indicators]
  - Required state: [What's needed for success]
  - Gap closure plan: [How to build alignment]

- **Organizational Capacity**: [Ability to execute transformation]
  - Change fatigue level: [Assessment]
  - Resource availability: [People, budget, time]
  - Competing priorities: [Constraints and conflicts]

- **Stakeholder Analysis**:
  | Stakeholder Group | Influence | Support Level | Key Concerns | Engagement Strategy |
  |-------------------|-----------|---------------|--------------|-------------------|
  | [Group] | High/Med/Low | Champion/Supportive/Neutral/Resistant | [Concerns] | [Strategy] |

**Change Management Strategy**:

- **Communication Plan**: [How to build awareness and support]
- **Training & Enablement**: [Capability building approach]
- **Incentive Alignment**: [How to drive desired behaviors]
- **Quick Wins**: [Early successes to build momentum]
- **Risk Mitigation**: [Addressing resistance and barriers]

#### Framework-Specific Strategic Recommendations

**DAMA-DMBOK Maturity Path**:
- **Current Assessment**: [Overall DAMA-DMBOK maturity level with justification]
- **Knowledge Area Priorities**: [Which DMBOK knowledge areas to focus on]
- **Recommended Practices**: [Specific DMBOK practices to implement]
- **Progression Strategy**: [How to advance through DMBOK maturity levels]

**Gartner EIM Advancement**:
- **Current Stage**: [Gartner EIM stage with characteristics]
- **Next Stage Requirements**: [What's needed to advance]
- **Strategic Imperatives**: [Aligned with Gartner recommendations]
- **Common Pitfalls**: [What to avoid based on Gartner research]

**CMMI/DMM Implementation**:
- **Process Area Assessment**: [Current maturity by process area]
- **Capability Building**: [Which CMMI practices to implement]
- **Institutionalization**: [How to embed practices]
- **Continuous Improvement**: [Path to higher maturity levels]

**ISO Standards Compliance**:
- **Relevant Standards**: [List applicable ISO standards]
- **Current Compliance**: [Assessment against standards]
- **Certification Roadmap**: [Path to certification if desired]
- **Business Value**: [Why compliance matters]

#### Executive Summary: Enterprise Maturity Analysis

**Maturity Verdict** (2-3 sentences):
[Overall assessment of enterprise data maturity, current position, and trajectory]

**Key Findings** (Top 5):
1. **[Finding 1]**: [Description with framework validation and business impact]
2. **[Finding 2]**: [Description with framework validation and business impact]
3. **[Finding 3]**: [Description with framework validation and business impact]
4. **[Finding 4]**: [Description with framework validation and business impact]
5. **[Finding 5]**: [Description with framework validation and business impact]

**Strategic Imperatives** (Top 3 actions to advance enterprise maturity):
1. **[Imperative 1]**: [Why critical, expected impact, framework alignment, investment required]
2. **[Imperative 2]**: [Why critical, expected impact, framework alignment, investment required]
3. **[Imperative 3]**: [Why critical, expected impact, framework alignment, investment required]

**Maturity Progression Forecast** (If roadmap executed successfully):

- **6 Months**:
  - Target Maturity: [X.X/5] - [Level Name]
  - Key Achievements: [3-5 achievements]
  - Dimensions Advanced: [List dimensions expected to improve]
  - Business Value: [Quantified or described benefits]

- **12 Months**:
  - Target Maturity: [X.X/5] - [Level Name]
  - Key Achievements: [3-5 achievements]
  - Enterprise Transformation: [Major changes realized]
  - Business Value: [Quantified or described benefits]

- **24 Months**:
  - Target Maturity: [X.X/5] - [Level Name]
  - Key Achievements: [3-5 achievements]
  - Competitive Position: [Strategic advantage gained]
  - Business Value: [Comprehensive value realization]

**Investment & Value Summary**:

| Timeframe | Est. Investment | Expected Value | ROI | Risk Reduction | Capability Gain |
|-----------|----------------|----------------|-----|----------------|-----------------|
| 0-6 months | $[Amount] | $[Value] | [X]x | [Description] | [Capabilities] |
| 6-12 months | $[Amount] | $[Value] | [X]x | [Description] | [Capabilities] |
| 12-24 months | $[Amount] | $[Value] | [X]x | [Description] | [Capabilities] |
| **Total** | **$[Total]** | **$[Total Value]** | **[X]x** | **[Total Risk Reduction]** | **[Complete Transformation]** |

**Final Recommendation** (2-3 sentences):
[Clear recommendation on whether to proceed, pace of execution, and critical considerations]

---
"""

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

### 7. Enterprise Data Maturity Analysis
**CRITICAL**: Leverage the RAG-provided industry frameworks and best practices to conduct a comprehensive, enterprise-wide maturity assessment. This section must synthesize maturity assessments from individual dimension reports and validate against DAMA-DMBOK, Gartner EIM, CMMI/DMM, and other relevant frameworks from the knowledge base.
""" + ENTERPRISE_MATURITY_ANALYSIS + """
"""

OVERALL_SUMMARY_SYSTEM_PROMPT = OVERALL_SUMMARY_PROMPT_ADD_ON + """You are a **senior data management consultant** tasked with synthesizing insights across multiple data management dimensions. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format.

**CRITICALLY IMPORTANT TABLE FORMAT RULES:**
1. Use ONLY standard markdown table syntax with pipes (|) and dashes (-)
2. NEVER use ASCII box-drawing characters like +-----------+ or +-----+-----+
3. NEVER use ASCII art or box art for tables
4. Use this format ONLY: | Column | Column |\n|--------|--------|\n| Data | Data |
5. All tables must be properly aligned, scannable, and visually appealing for human readers

The analysis is based on survey responses with scores on a 1-10 scale."""


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

    prompt += "\n\nGenerate a professionally crafted, consultative, executive-ready report with the following sections.\n"
    prompt += "\n**IMPORTANT TABLE FORMAT:** Use ONLY standard markdown table syntax (| and -). DO NOT use ASCII box-drawing characters (+-----------+) or box art.\n\n"
    prompt += OVERALL_SUMMARY_SECTIONS
    return prompt


def get_overall_summary_single_prompt(all_summaries_text: str) -> str:
    """Generate prompt for single-pass overall summary"""
    prompt = "Analyze the following dimension summaries and provide an overall organizational data governance assessment:\n\n"
    prompt += all_summaries_text
    prompt += "\n\nGenerate a professionally crafted, consultative, executive-ready report with the following sections. **USE MARKDOWN TABLES EXTENSIVELY** for all data and comparisons.\n"
    prompt += "\n**IMPORTANT TABLE FORMAT:** Use ONLY standard markdown table syntax (| and -). DO NOT use ASCII box-drawing characters (+-----------+) or box art.\n\n"
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
- **Extensive use of well-formatted MARKDOWN tables** (using | and - ONLY) for all data
- DO NOT use ASCII box-drawing characters (+-----------+)
- Proper table alignment and spacing
- Visual clarity for human readers"""
    return prompt


CONSOLIDATION_SYSTEM_PROMPT = """You are a senior data governance consultant writing a professional executive report. Write in a formal, report-style format suitable for C-level executives. Use third-person perspective. Do NOT use first person (I, we) or ask questions. Do NOT include interactive elements or conversational language.

**CRITICALLY IMPORTANT TABLE FORMAT RULES:**
1. Use ONLY standard markdown table syntax with pipes (|) and dashes (-)
2. NEVER use ASCII box-drawing characters like +-----------+ or +-----+-----+
3. NEVER use ASCII art or box art for tables
4. Use this format ONLY: | Column | Column |\n|--------|--------|\n| Data | Data |

Use well-formatted markdown tables extensively for all data, comparisons, and structured information. Tables must be properly aligned and visually clear for human readers."""
