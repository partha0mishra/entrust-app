import httpx
from typing import List, Dict, Optional
import json
from .llm_providers import get_llm_provider
import re

class LLMService:
    # Approximate token estimation: ~4 characters per token
    CHARS_PER_TOKEN = 4
    MAX_TOKENS_PER_CHUNK = 5000
    MAX_CHARS_PER_CHUNK = MAX_TOKENS_PER_CHUNK * CHARS_PER_TOKEN  # ~20,000 chars
    LLM_TIMEOUT = 180.0  # 3 minutes
    
    @staticmethod
    async def test_llm_connection(config) -> Dict:
        """Test LLM connection using the appropriate provider"""
        try:
            provider = get_llm_provider(config)
            return await provider.test_connection()
        except Exception as e:
            return {"status": "Failed", "error": str(e)}
    
    @staticmethod
    def _chunk_questions(questions_data: List[Dict], max_chars: int) -> List[List[Dict]]:
        """
        Split questions into chunks based on character count estimation
        Each chunk will be within the token limit for LLM processing
        """
        chunks = []
        current_chunk = []
        current_size = 0
        
        for question in questions_data:
            # Estimate size of this question's data
            question_text = question.get('text', '')
            avg_score = str(question.get('avg_score', 'N/A'))
            comments = question.get('comments', [])
            comments_text = ' '.join(comments) if comments else ''
            
            question_size = len(question_text) + len(avg_score) + len(comments_text) + 100  # +100 for formatting
            
            # If adding this question exceeds limit, start new chunk
            if current_chunk and current_size + question_size > max_chars:
                chunks.append(current_chunk)
                current_chunk = []
                current_size = 0
            
            current_chunk.append(question)
            current_size += question_size
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    @staticmethod
    async def _call_llm(
        provider,
        messages: List[Dict],
        max_tokens: int = 500
    ) -> str:
        """Helper method to call LLM API using provider"""
        return await provider.call_llm(messages, max_tokens)
    
    @staticmethod
    def _parse_llm_output(response_text: str) -> (str, Optional[Dict]):
        """Parses LLM response to separate markdown and a JSON block."""
        json_content = None
        markdown_content = response_text

        # Regex to find a JSON block enclosed in ```json ... ```
        # It handles potential text before or after the JSON block.
        json_block_match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)

        if json_block_match:
            json_string = json_block_match.group(1)
            try:
                json_content = json.loads(json_string)
                # Remove the JSON block from the markdown content to avoid rendering it.
                markdown_content = response_text.replace(json_block_match.group(0), "").strip()
            except json.JSONDecodeError:
                # If JSON is invalid, treat it as part of the markdown and do nothing.
                pass
        return markdown_content, json_content
    @staticmethod
    async def generate_dimension_summary(
        config,
        dimension: str,
        questions_data: List[Dict]
    ) -> Dict:
        """
        Generate dimension summary with chunking support
        Returns both partial summaries and final consolidated summary
        """
        try:
            # Get the appropriate provider
            provider = get_llm_provider(config)

            # Split questions into chunks
            chunks = LLMService._chunk_questions(
                questions_data,
                LLMService.MAX_CHARS_PER_CHUNK
            )

            chunk_summaries = []

            # Process each chunk
            for i, chunk in enumerate(chunks):
                chunk_prompt = f"""Analyze the following survey responses for the {dimension} dimension (Part {i+1} of {len(chunks)}):

Questions and Responses:
"""

                prompt_add_on = """## PROMPT ADD-ON
You are a senior data governance consultant.
**DEEP DRILL-DOWN REQUIRED**:
**Step 1**: Compute stats (avg, % high/low) by Category, Process, Lifecycle Stage.
**Step 2**: Draft tables.
**Step 3**: Write observations with evidence.
**Step 4**: Prioritize actions (Risk × Impact).
**Step 5**: 
- For **every Category, Process, and Lifecycle Stage**, provide:
  - Full score breakdown
  - All comments (with sentiment/theme)
  - 3–6 **best practices** (cite DAMA, GDPR, ISO 8000, NIST)
  - 3–6 **observations**
  - 3–6 **areas for improvement**
  - 3–8 **action items** (priority, owner, tool, timeline, framework)
- **Do not summarize** — be exhaustive.
- **Cite Q# everywhere**.
- **Self-score depth ≥ 9** or revise.

---
"""                
                system_prompt = prompt_add_on + "You are a data governance expert writing a professional report analyzing survey responses with scores on a 1-10 scale. Write in a formal, report-style format suitable for executive review. Use third-person perspective. DO NOT use first person (I, we) or ask questions. DO NOT include interactive elements like 'Let me analyze' or 'Would you like'. Provide clear, actionable insights in markdown format with proper headers, bullet points, and line breaks."
                user_prompt_template = """
Provide a concise summary of the current state and actionable suggestions for improvement.
"""

                if dimension == "Data Privacy & Compliance":
                    system_prompt = prompt_add_on + "You are a **senior data management consultant** specializing in Data Privacy & Compliance. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."
                    user_prompt_template = """
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
                elif dimension == "Data Ethics & Bias":
                    system_prompt = prompt_add_on + "You are a **senior data management consultant** specializing in Data Ethics & Bias. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."
                    user_prompt_template = """
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
                elif dimension == "Data Lineage & Traceability":
                    system_prompt = prompt_add_on + "You are a **senior data management consultant** specializing in Data Lineage & Traceability. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."
                    user_prompt_template = """
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
                elif dimension == "Data Security & Access":
                    system_prompt = prompt_add_on + "You are a **senior data management consultant** specializing in Data Security & Access. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."
                    user_prompt_template = """
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
                elif dimension == "Metadata & Documentation":
                    system_prompt = prompt_add_on + "You are a **senior data management consultant** specializing in Metadata & Documentation. Your output must be a professionally crafted, consultative,executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."
                    user_prompt_template = """
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

                chunk_prompt = f"""Analyze the following survey responses for the {dimension} dimension (Part {i+1} of {len(chunks)}):

Questions and Responses:
"""
                for q in chunk:
                    chunk_prompt += f"\nQuestion: {q['text']}\n"
                    if q.get('guidance'):
                        chunk_prompt += f"Guidance: {q['guidance']}\n"
                    chunk_prompt += f"Category: {q.get('category', 'N/A')}\n"
                    chunk_prompt += f"Process: {q.get('process', 'N/A')}\n"
                    chunk_prompt += f"Lifecycle Stage: {q.get('lifecycle_stage', 'N/A')}\n"
                    chunk_prompt += f"Average Score: {q.get('avg_score', 'N/A')}\n"
                    
                    comments = q.get('comments', [])
                    if comments:
                        chunk_prompt += f"Sample Comments:\n"
                        # Limit comments to avoid too much data
                        for comment in comments[:5]:  # Max 5 comments per question
                            chunk_prompt += f"  - {comment}\n"
                chunk_prompt += user_prompt_template
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk_prompt}
                ]

                chunk_response = await LLMService._call_llm(
                    provider, messages, max_tokens=30000
                )
                                
                chunk_summaries.append({
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "content": chunk_response,
                    "json_content": None # Removed
                })
            
            # If multiple chunks, generate final consolidated summary
            final_summary = None
            final_json = None
            if len(chunks) > 1:
                consolidation_prompt = f"""You have analyzed {len(chunks)} parts of survey data for the {dimension} dimension. Here are the partial analyses:

"""
                for i, summary in enumerate(chunk_summaries):
                    consolidation_prompt += f"\n--- Part {i+1} Analysis ---\n{summary['content']}\n"
                
                if dimension in ["Data Privacy & Compliance", "Data Ethics & Bias", "Data Lineage & Traceability", "Data Value & Lifecycle Management", "Data Governance & Management", "Data Security & Access", "Metadata & Documentation"]:
                    consolidation_prompt += "\n\nConsolidate the analyses from all parts into a single, final report following the requested markdown structure. Ensure all sections are complete and well-structured based on the combined data from all parts."
                else:
                    consolidation_prompt += "\n\nProvide a comprehensive, consolidated summary that integrates insights from all parts. Include:\n1. **Current State**: Overall assessment\n2. **Key Findings**: Most important insights\n3. **Recommendations**: Actionable improvement suggestions\n\nUse markdown formatting with clear headers and bullet points."
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": consolidation_prompt}
                ]

                final_response = await LLMService._call_llm(
                    provider, messages, max_tokens=30000
                )
                final_summary, final_json = final_response, None
            
            single_chunk_summary = chunk_summaries[0] if chunk_summaries else {}

            return {
                "success": True,
                "chunk_summaries": chunk_summaries,
                "final_summary": final_summary or single_chunk_summary.get('content'),
                "final_json": final_json or single_chunk_summary.get('json_content'),
                "total_chunks": len(chunks)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chunk_summaries": [],
                "final_summary": None,
                "final_json": None
            }
    
    @staticmethod
    async def generate_overall_summary(
        config,
        dimension_summaries: Dict[str, str]
    ) -> Dict:
        """
        Generate overall summary from dimension summaries with chunking support
        """
        try:
            # Get the appropriate provider
            provider = get_llm_provider(config)

            # Prepare dimension summaries text
            all_summaries_text = ""
            for dimension, summary in dimension_summaries.items():
                all_summaries_text += f"\n## {dimension}\n{summary}\n"

            # Check if we need to chunk
            if len(all_summaries_text) > LLMService.MAX_CHARS_PER_CHUNK:
                # Split dimensions into chunks
                dimension_items = list(dimension_summaries.items())
                chunks = []
                current_chunk = {}
                current_size = 0
                
                for dimension, summary in dimension_items:
                    dim_size = len(dimension) + len(summary) + 50
                    
                    if current_chunk and current_size + dim_size > LLMService.MAX_CHARS_PER_CHUNK:
                        chunks.append(current_chunk)
                        current_chunk = {}
                        current_size = 0
                    
                    current_chunk[dimension] = summary
                    current_size += dim_size
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Process each chunk
                chunk_summaries = []
                for i, chunk in enumerate(chunks):
                    chunk_prompt = f"Analyze these data governance dimensions (Part {i+1} of {len(chunks)}):\n\n"
                    for dimension, summary in chunk.items():
                        chunk_prompt += f"## {dimension}\n{summary}\n\n"
                    
                    chunk_prompt += f"\n\nProvide a consolidated assessment focusing on cross-cutting themes and strategic insights from these dimensions."
                    
                    messages = [
                        {"role": "system", "content": "You are a senior data governance consultant writing a professional executive report. Write in a formal, report-style format suitable for C-level executives. Use third-person perspective. Do NOT use first person (I, we) or ask questions. Do NOT include interactive elements or conversational language. Use markdown formatting."},
                        {"role": "user", "content": chunk_prompt}
                    ]

                    chunk_response = await LLMService._call_llm(
                        provider, messages, max_tokens=30000
                    )
                    chunk_summaries.append(chunk_response)
                
                # Final consolidation
                final_prompt = "You have analyzed multiple groups of data governance dimensions. Here are the analyses:\n\n"
                for i, summary in enumerate(chunk_summaries):
                    final_prompt += f"\n--- Analysis Part {i+1} ---\n{summary}\n"
                
                prompt_add_on = """## PROMPT ADD-ON
You are a senior data governance consultant.
**Step 1**: Compute stats (avg, % high/low) by Category, Process, Lifecycle Stage.
**Step 2**: Draft tables.
**Step 3**: Write observations with evidence.
**Step 4**: Prioritize actions (Risk × Impact).
**Step 5**: Self-score (1–10). Revise if <8.
**Output ONLY the Markdown report**.

---
"""
                final_prompt += """

Generate a professionally crafted, consultative, executive-ready report with the following sections:

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
"""
                
                messages = [
                    {"role": "system", "content": prompt_add_on + "You are a **senior data management consultant** tasked with synthesizing insights across multiple data management dimensions. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. The analysis is based on survey responses with scores on a 1-10 scale."},
                    {"role": "user", "content": final_prompt}
                ]

                final_response = await LLMService._call_llm(
                    provider, messages, max_tokens=30000
                )
                final_summary, final_json = final_response, None
                
                return {
                    "success": True,
                    "markdown_content": final_summary,
                    "json_content": final_json,
                    "chunks_processed": len(chunks)
                }
            
            else:
                # Single call for smaller content
                prompt = "Analyze the following dimension summaries and provide an overall organizational data governance assessment:\n\n"
                prompt += all_summaries_text
                prompt_add_on = """## PROMPT ADD-ON
You are a senior data governance consultant.
**Step 1**: Compute stats (avg, % high/low) by Category, Process, Lifecycle Stage.
**Step 2**: Draft tables.
**Step 3**: Write observations with evidence.
**Step 4**: Prioritize actions (Risk × Impact).
**Step 5**: Self-score (1–10). Revise if <8.
**Output ONLY the Markdown report** .

---
"""
                prompt += """

Generate a professionally crafted, consultative, executive-ready report with the following sections:

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
"""
                
                messages = [
                    {"role": "system", "content": prompt_add_on + "You are a **senior data management consultant** tasked with synthesizing insights across multiple data management dimensions. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. The analysis is based on survey responses with scores on a 1-10 scale."},
                    {"role": "user", "content": prompt}
                ]

                response_text = await LLMService._call_llm(
                    provider, messages, max_tokens=30000
                )
                markdown_summary, json_summary = response_text, None
                
                return {
                    "success": True,
                    "markdown_content": markdown_summary,
                    "json_content": json_summary,
                    "chunks_processed": 1
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "markdown_content": None
            }