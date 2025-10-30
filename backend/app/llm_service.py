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
                json_schema_prompt_add_on = """

---
**JSON Output Requirement**
In addition to the markdown report, you MUST provide a valid JSON object that conforms to the following schema.
The JSON output should be a single, separate block of code. Do not add any text before or after the JSON block.

```json
{
  "type": "object",
  "properties": {
    "report_metadata": {
      "type": "object",
      "properties": {
        "dimension": { "type": "string" },
        "report_date": { "type": "string", "format": "date" },
        "generated_with_ai": { "type": "boolean", "const": true },
        "ai_model": { "type": "string" },
        "survey_responses": { "type": "integer" },
        "total_questions": { "type": "integer" },
        "version": { "type": "string", "const": "v4-deep-drill" }
      },
      "required": ["dimension", "report_date", "survey_responses", "total_questions"]
    },

    "current_state": {
      "type": "object",
      "properties": {
        "overall_mean_score": { "type": "number", "minimum": 1, "maximum": 10 },
        "median_score": { "type": "number", "minimum": 1, "maximum": 10 },
        "pct_scores_7_plus": { "type": "number", "minimum": 0, "maximum": 100 },
        "pct_scores_3_minus": { "type": "number", "minimum": 0, "maximum": 100 },
        "maturity_level": { 
          "type": "string", 
          "enum": ["Critical", "Low", "Medium", "High", "Excellent"] 
        },
        "executive_summary": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 3,
          "maxItems": 6,
          "description": "Bullet points. Each must cite a score or % and a framework."
        }
      },
      "required": ["overall_mean_score", "maturity_level", "executive_summary"]
    },

    "analysis_by_category": {
      "type": "array",
      "description": "Deep analysis per Category (e.g., Accuracy, Completeness, Timeliness).",
      "items": {
        "type": "object",
        "properties": {
          "category": { "type": "string" },
          "avg_score": { "type": "number", "minimum": 1, "maximum": 10 },
          "pct_high": { "type": "number", "minimum": 0, "maximum": 100 },
          "pct_low": { "type": "number", "minimum": 0, "maximum": 100 },
          "questions_in_category": { "type": "array", "items": { "type": "string" } },
          "comment_analysis": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "q_num": { "type": "string" },
                "comment": { "type": "string" },
                "sentiment": { "type": "string", "enum": ["Positive", "Neutral", "Negative"] },
                "theme": { "type": "string" }
              },
              "required": ["q_num", "comment", "theme"]
            }
          },
          "best_practices": {
            "type": "array",
            "items": { "type": "string" },
            "minItems": 3,
            "maxItems": 6,
            "description": "Cite DAMA, ISO 8000, GDPR, etc."
          },
          "observations": {
            "type": "array",
            "items": { "type": "string" },
            "minItems": 3,
            "maxItems": 6
          },
          "areas_for_improvement": {
            "type": "array",
            "items": { "type": "string" },
            "minItems": 3,
            "maxItems": 6
          },
          "action_items": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "action": { "type": "string" },
                "priority": { "type": "string", "enum": ["High", "Medium", "Low"] },
                "owner": { "type": "string" },
                "timeline": { "type": "string" },
                "tool_example": { "type": "string" },
                "framework_ref": { "type": "string" }
              },
              "required": ["action", "priority", "tool_example", "framework_ref"]
            },
            "minItems": 3,
            "maxItems": 8
          }
        },
        "required": [
          "category", "avg_score", "pct_high", "pct_low",
          "best_practices", "observations", "areas_for_improvement", "action_items"
        ]
      }
    },

    "analysis_by_process": {
      "type": "array",
      "description": "Deep analysis per Process (e.g., Data Ingestion, Cleansing, Monitoring).",
      "items": {
        "type": "object",
        "properties": {
          "process": { "type": "string" },
          "avg_score": { "type": "number", "minimum": 1, "maximum": 10 },
          "questions_in_process": { "type": "array", "items": { "type": "string" } },
          "comment_analysis": { "type": "array", "items": { "$ref": "#/properties/analysis_by_category/items/properties/comment_analysis/items" } },
          "best_practices": { "type": "array", "items": { "type": "string" }, "minItems": 3 },
          "observations": { "type": "array", "items": { "type": "string" }, "minItems": 3 },
          "areas_for_improvement": { "type": "array", "items": { "type": "string" }, "minItems": 3 },
          "action_items": { "$ref": "#/properties/analysis_by_category/items/properties/action_items" }
        },
        "required": [
          "process", "avg_score",
          "best_practices", "observations", "areas_for_improvement", "action_items"
        ]
      }
    },

    "analysis_by_lifecycle_stage": {
      "type": "array",
      "description": "Deep analysis per Lifecycle Stage (e.g., Creation, Usage, Archival).",
      "items": {
        "type": "object",
        "properties": {
          "stage": { "type": "string" },
          "avg_score": { "type": "number", "minimum": 1, "maximum": 10 },
          "questions_in_stage": { "type": "array", "items": { "type": "string" } },
          "comment_analysis": { "type": "array", "items": { "$ref": "#/properties/analysis_by_category/items/properties/comment_analysis/items" } },
          "best_practices": { "type": "array", "items": { "type": "string" }, "minItems": 3 },
          "observations": { "type": "array", "items": { "type": "string" }, "minItems": 3 },
          "areas_for_improvement": { "type": "array", "items": { "type": "string" }, "minItems": 3 },
          "action_items": { "$ref": "#/properties/analysis_by_category/items/properties/action_items" }
        },
        "required": [
          "stage", "avg_score",
          "best_practices", "observations", "areas_for_improvement", "action_items"
        ]
      }
    },

    "priority_actions": {
      "type": "array",
      "description": "Top 10 cross-cutting initiatives. Ranked by Risk × Impact.",
      "items": {
        "type": "object",
        "properties": {
          "rank": { "type": "integer", "minimum": 1, "maximum": 10 },
          "initiative": { "type": "string" },
          "risk_severity": { "type": "string", "enum": ["High", "Medium", "Low"] },
          "business_impact": { "type": "string", "enum": ["High", "Medium", "Low"] },
          "rice_score": { "type": "integer", "minimum": 1, "maximum": 9 },
          "linked_questions": { "type": "array", "items": { "type": "string" } },
          "actionable_step": { "type": "string" }
        },
        "required": ["rank", "initiative", "risk_severity", "business_impact", "rice_score"]
      },
      "minItems": 5,
      "maxItems": 10
    },

    "actionable_improvement_suggestions": {
      "type": "array",
      "description": "One concrete, tool-enabled fix per major gap. From SHIP report.",
      "items": {
        "type": "object",
        "properties": {
          "gap": { "type": "string" },
          "recommendation": { "type": "string" },
          "tool_example": { "type": "string" },
          "owner_role": { "type": "string" },
          "timeline": { "type": "string", "enum": ["Immediate", "Q1", "Q2", "Q3", "Q4", "Long-term"] },
          "framework_reference": { "type": "string" },
          "expected_roi": { "type": "string" }
        },
        "required": ["recommendation", "tool_example", "framework_reference"]
      },
      "minItems": 5
    },

    "strategic_observations": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 4,
      "maxItems": 8,
      "description": "Link survey findings to DAMA, GDPR, ISO 8000, NIST, etc."
    },

    "question_level_analysis": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "q_num": { "type": "string", "pattern": "^Q[0-9]+$" },
          "question_text": { "type": "string" },
          "category": { "type": "string" },
          "process": { "type": "string" },
          "lifecycle_stage": { "type": "string" },
          "responses": { "type": "integer" },
          "min_score": { "type": "number" },
          "max_score": { "type": "number" },
          "avg_score": { "type": "number", "minimum": 1, "maximum": 10 },
          "comments": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["q_num", "question_text", "avg_score", "category"]
      }
    },

    "risk_spotlight": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "risk": { "type": "string" },
          "severity": { "type": "string", "enum": ["Critical", "High", "Medium", "Low"] },
          "regulatory_risk": { "type": "string" },
          "mitigation_urgency": { "type": "string", "enum": ["Immediate", "Short-term", "Long-term"] },
          "linked_questions": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["risk", "severity", "mitigation_urgency"]
      }
    },

    "self_score": {
      "type": "object",
      "properties": {
        "clarity": { "type": "integer", "minimum": 1, "maximum": 10 },
        "actionability": { "type": "integer", "minimum": 1, "maximum": 10 },
        "evidence_based": { "type": "integer", "minimum": 1, "maximum": 10 },
        "framework_alignment": { "type": "integer", "minimum": 1, "maximum": 10 },
        "depth_of_analysis": { "type": "integer", "minimum": 1, "maximum": 10 },
        "average": { "type": "number" },
        "revision_needed": { "type": "boolean" },
        "revision_notes": { "type": "string" }
      },
      "required": ["clarity", "actionability", "evidence_based", "framework_alignment", "depth_of_analysis", "revision_needed"]
    }
  },
  "required": [
    "report_metadata",
    "current_state",
    "analysis_by_category",
    "analysis_by_process",
    "analysis_by_lifecycle_stage",
    "priority_actions",
    "actionable_improvement_suggestions",
    "strategic_observations",
    "question_level_analysis",
    "risk_spotlight",
    "self_score"
  ]
}
```
"""
                system_prompt = prompt_add_on + "You are a data governance expert writing a professional report analyzing survey responses with scores on a 1-10 scale. Write in a formal, report-style format suitable for executive review. Use third-person perspective. DO NOT use first person (I, we) or ask questions. DO NOT include interactive elements like 'Let me analyze' or 'Would you like'. Provide clear, actionable insights in markdown format with proper headers, bullet points, and line breaks."
                user_prompt_template = """
Provide a concise summary of the current state and actionable suggestions for improvement.
"""

                if dimension == "Data Privacy & Compliance":
                    system_prompt = prompt_add_on + "You are a **senior data management consultant** specializing in Data Privacy & Compliance. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."
                    user_prompt_template = """
Generate a report with the following sections based on the provided survey data. Use clear headings, tables, and bullet points for optimal readability.

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

--- Analysis for every category

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

--- Analysis for every category

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

--- Analysis for every category

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

---
"""
                elif dimension == "Data Value & Lifecycle Management":
                    system_prompt = prompt_add_on + "You are a **senior data management consultant** specializing in Data Value & Lifecycle Management. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."
                    user_prompt_template = """
Generate a report with the following sections based on the provided survey data. Use clear headings, tables, and bullet points for optimal readability.

# Data Value & Lifecycle Management – Survey Analysis Report

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
- Link survey findings to industry frameworks (e.g., DAMA-DMBOK, data lifecycle models)

### 6. Prioritized Action Plan
- Create a table with columns: Priority, Action Item, Owner, Timeline, Expected Outcome
- Provide at least one 'High' priority action.

### 7. Risk Spotlight
- Identify critical risks (e.g., data underutilization, poor retention)
- Assign a mitigation urgency: Immediate / Short-term / Long-term

--- Analysis for every category

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

---
"""
                elif dimension == "Data Governance & Management":
                    system_prompt = prompt_add_on + "You are a **senior data management consultant** specializing in Data Governance & Management. Your output must be a professionally crafted, consultative, executive-ready report in PDF-friendly Markdown format. Analyze the provided survey responses which include Question, Score (on a 1-10 scale), Comment, Category, Process, and Lifecycle Stage."
                    user_prompt_template = """
Generate a report with the following sections based on the provided survey data. Use clear headings, tables, and bullet points for optimal readability.

# Data Governance & Management – Survey Analysis Report

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
- Link survey findings to industry frameworks (e.g., DAMA-DMBOK, COBIT)

### 6. Prioritized Action Plan
- Create a table with columns: Priority, Action Item, Owner, Timeline, Expected Outcome
- Provide at least one 'High' priority action.

### 7. Risk Spotlight
- Identify critical risks (e.g., inconsistent policies, lack of accountability)
- Assign a mitigation urgency: Immediate / Short-term / Long-term

--- Analysis for every category

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

--- Analysis for every category

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

--- Analysis for every category

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
**Output ONLY the Markdown report** as requested below.

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
**Output ONLY the Markdown report** as requested below.

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