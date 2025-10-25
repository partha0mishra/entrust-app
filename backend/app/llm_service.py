import httpx
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Professional prompts for each dimension
DIMENSION_PROMPTS = {
    "Data Privacy & Compliance": """You are an expert in Data Privacy & Compliance. You have been provided with survey data containing questions related to Data Privacy & Compliance, each with a score from 1 to 10 and optional respondent comments. Analyze the provided survey data (questions, scores, and comments) to generate a comprehensive report. Your response should include:
1. **Summary**: A concise overview of the survey results, including average scores, score distribution (e.g., percentage of scores above 7), and prevalent themes in comments.
2. **Key Observations**: Identify patterns, strengths, and weaknesses in the responses. Highlight specific questions with notably high or low scores and recurring themes in comments (e.g., concerns about GDPR compliance, data breach protocols).
3. **Action Items**: Provide 3-5 specific, actionable recommendations to improve data privacy and compliance, such as policy updates, training programs, or audits, based on the survey insights.
4. **Potential Risks**: Highlight any privacy or compliance risks indicated by low scores or critical comments (e.g., lack of consent mechanisms, outdated privacy policies).
Structure your response with clear headings for each section and use bullet points for clarity. If the survey data is incomplete or unclear, note this and make reasonable assumptions while prioritizing privacy and compliance best practices (e.g., GDPR, CCPA, ISO 27701). Provide examples where relevant to illustrate your points.""",

    "Data Ethics & Bias": """You are an expert in Data Ethics & Bias. You have survey data with questions on Data Ethics & Bias, each with a score from 1 to 10 and optional comments. Analyze the data to produce a detailed report with the following sections:
1. **Summary**: Summarize the survey results, including average scores, score distribution, and key themes from comments (e.g., concerns about algorithmic bias, fairness in data use).
2. **Key Observations**: Identify trends, such as questions with consistently low scores (e.g., bias detection processes) or recurring comment themes (e.g., lack of transparency in AI models).
3. **Action Items**: Recommend 3-5 specific actions to address ethical concerns and reduce bias, such as implementing bias audits, enhancing transparency, or training on ethical data use.
4. **Ethical Risks**: Highlight potential ethical risks, such as biased decision-making or lack of stakeholder inclusion, based on the survey data.
Use clear headings and bullet points. Focus on ethical principles (e.g., fairness, accountability, transparency) and reference frameworks like AI Ethics Guidelines or IEEE Ethically Aligned Design where relevant. If data is ambiguous, note assumptions and prioritize ethical best practices.""",

    "Data Lineage & Traceability": """You are an expert in Data Lineage & Traceability. You have survey data with questions on Data Lineage & Traceability, each scored from 1 to 10 with optional comments. Analyze the data and generate a report with:
1. **Summary**: Provide an overview of the survey results, including average scores, score distribution, and common themes in comments (e.g., challenges in tracking data origins).
2. **Key Observations**: Highlight patterns, such as high-scoring areas (e.g., metadata tracking) or low-scoring areas (e.g., lack of lineage tools), and recurring comment themes.
3. **Action Items**: Suggest 3-5 actionable steps to improve data lineage and traceability, such as adopting lineage tracking tools, standardizing documentation, or automating provenance tracking.
4. **Traceability Gaps**: Identify risks or gaps in traceability (e.g., incomplete audit trails, unclear data transformations) based on low scores or critical comments.
Structure your response with headings and bullet points. Reference best practices (e.g., DAMA-DMBOK, data provenance standards) and provide examples to clarify recommendations. Note any assumptions if the data is incomplete.""",

    "Data Value & Lifecycle Management": """You are an expert in Data Value & Lifecycle Management. You have survey data with questions on Data Value & Lifecycle Management, each with a score from 1 to 10 and optional comments. Analyze the data to produce a report with:
1. **Summary**: Summarize the survey results, including average scores, score distribution, and key comment themes (e.g., issues with data retention policies, maximizing data value).
2. **Key Observations**: Identify strengths (e.g., effective data monetization) and weaknesses (e.g., unclear lifecycle stages) based on scores and comments.
3. **Action Items**: Recommend 3-5 specific actions to enhance data value and lifecycle management, such as defining clear lifecycle stages, optimizing data storage, or improving ROI tracking.
4. **Value Risks**: Highlight risks to data value, such as underutilization or poor lifecycle management, based on survey insights.
Use clear headings and bullet points. Reference frameworks like DAMA-DMBOK or data lifecycle models (e.g., creation, storage, usage, archival, deletion). Provide examples and note assumptions if data is incomplete.""",

    "Data Governance & Management": """You are an expert in Data Governance & Management. You have survey data with questions on Data Governance & Management, each scored from 1 to 10 with optional comments. Analyze the data and generate a report with:
1. **Summary**: Provide an overview of the survey results, including average scores, score distribution, and prevalent comment themes (e.g., lack of governance policies, role clarity).
2. **Key Observations**: Highlight patterns, such as high-scoring areas (e.g., clear ownership) or low-scoring areas (e.g., weak policy enforcement), and recurring comment themes.
3. **Action Items**: Suggest 3-5 actionable recommendations to strengthen governance and management, such as establishing a governance framework, clarifying roles, or implementing oversight tools.
4. **Governance Risks**: Identify risks, such as inconsistent policies or lack of accountability, based on low scores or critical comments.
Structure your response with headings and bullet points. Reference frameworks like DAMA-DMBOK or COBIT and provide examples. Note assumptions if the data is ambiguous.""",

    "Data Security & Access": """You are an expert in Data Security & Access. You have survey data with questions on Data Security & Access, each with a score from 1 to 10 and optional comments. Analyze the data to produce a report with:
1. **Summary**: Summarize the survey results, including average scores, score distribution, and key themes in comments (e.g., concerns about access controls, encryption).
2. **Key Observations**: Identify trends, such as strengths (e.g., robust authentication) or weaknesses (e.g., outdated security protocols), and recurring comment themes.
3. **Action Items**: Recommend 3-5 specific actions to improve data security and access, such as implementing multi-factor authentication, updating encryption standards, or conducting security audits.
4. **Security Risks**: Highlight potential security risks, such as unauthorized access or data breaches, based on low scores or critical comments.
Use clear headings and bullet points. Reference standards like ISO 27001 or NIST Cybersecurity Framework and provide examples. Note assumptions if the data is incomplete.""",

    "Metadata & Documentation": """You are an expert in Metadata & Documentation. You have survey data with questions on Metadata & Documentation, each scored from 1 to 10 with optional comments. Analyze the data and generate a report with:
1. **Summary**: Provide an overview of the survey results, including average scores, score distribution, and common comment themes (e.g., incomplete metadata, lack of documentation standards).
2. **Key Observations**: Highlight patterns, such as high-scoring areas (e.g., metadata availability) or low-scoring areas (e.g., outdated documentation), and recurring comment themes.
3. **Action Items**: Suggest 3-5 actionable steps to improve metadata and documentation, such as adopting metadata standards (e.g., Dublin Core), automating documentation, or training staff.
4. **Documentation Gaps**: Identify risks, such as poor data discoverability or compliance issues, based on low scores or critical comments.
Structure your response with headings and bullet points. Reference best practices (e.g., DAMA-DMBOK, metadata schemas) and provide examples. Note assumptions if data is incomplete.""",

    "Data Quality": """You are an expert in Data Quality. You have survey data with questions on Data Quality, each with a score from 1 to 10 and optional comments. Analyze the data to produce a report with:
1. **Summary**: Summarize the survey results, including average scores, score distribution, and key themes in comments (e.g., issues with accuracy, completeness).
2. **Key Observations**: Identify trends, such as high-scoring areas (e.g., data validation processes) or low-scoring areas (e.g., inconsistent data), and recurring comment themes.
3. **Action Items**: Recommend 3-5 specific actions to improve data quality, such as implementing data profiling tools, standardizing formats, or enhancing cleansing processes.
4. **Quality Risks**: Highlight risks, such as unreliable data impacting decision-making, based on low scores or critical comments.
Use clear headings and bullet points. Reference data quality dimensions (e.g., accuracy, completeness, consistency, timeliness) and frameworks like TDQM or ISO 8000. Provide examples and note assumptions if data is incomplete."""
}

OVERALL_REPORT_PROMPT = """You are an expert in data management, tasked with generating a holistic report by synthesizing insights from individual reports on eight dimensions: Data Privacy & Compliance, Data Ethics & Bias, Data Lineage & Traceability, Data Value & Lifecycle Management, Data Governance & Management, Data Security & Access, Metadata & Documentation, and Data Quality. Each dimension's report includes a summary, key observations, action items, and risks. Produce an overall report with:
1. **Executive Summary**: Provide a high-level overview of the findings across all dimensions, highlighting overall strengths, weaknesses, and common themes (e.g., recurring issues like lack of standardization or strong areas like security).
2. **Cross-Dimension Analysis**: Identify interconnections between dimensions (e.g., how poor metadata impacts data quality or how governance affects compliance) and highlight any conflicting or reinforcing trends.
3. **Prioritized Action Plan**: Recommend 5-7 high-priority actions to address critical issues across dimensions, prioritizing based on risk severity and feasibility. Include timelines or resource considerations where relevant.
4. **Strategic Risks**: Highlight overarching risks to the organization's data management strategy, such as systemic gaps or regulatory non-compliance, based on the individual reports.
5. **Recommendations for Continuous Improvement**: Suggest processes (e.g., regular audits, cross-functional governance teams) to sustain improvements across all dimensions.
Structure your response with clear headings and bullet points. Use a professional tone and provide examples to illustrate key points. If any dimension's report is incomplete or ambiguous, note assumptions and prioritize best practices (e.g., DAMA-DMBOK, ISO standards). Ensure the report is concise yet comprehensive, suitable for senior stakeholders."""


class LLMService:
    @staticmethod
    async def test_llm_connection(
        api_url: str, 
        api_key: Optional[str] = None,
        model_name: Optional[str] = "default"
    ) -> Dict:
        logger.info(f"========== LLMService.test_llm_connection called ==========")
        logger.info(f"Received api_url: '{api_url}' (type: {type(api_url)})")
        logger.info(f"Received model_name: '{model_name}'")
        logger.info(f"Received api_key: {'SET' if api_key else 'NOT SET'}")
        
        if not api_url:
            logger.error("API URL is None or empty!")
            return {"status": "Failed", "error": "API URL is required"}
        
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "model": model_name or "default",
            "messages": [
                {"role": "user", "content": "Hello, this is a test message."}
            ],
            "max_tokens": 5000
        }
        
        try:
            logger.info(f"Creating httpx client...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Sending POST to: {api_url} with model: {model_name}")
                response = await client.post(api_url, json=payload, headers=headers)
                logger.info(f"Response status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                logger.info(f"Success! Response: {result}")
                return {"status": "Success", "response": result}
        except httpx.InvalidURL as e:
            logger.error(f"Invalid URL error: {str(e)}")
            return {"status": "Failed", "error": f"Invalid URL: {str(e)}"}
        except httpx.TimeoutException as e:
            logger.error(f"Timeout: {str(e)}")
            return {"status": "Failed", "error": f"Timeout after 30s: {str(e)}"}
        except httpx.ConnectError as e:
            logger.error(f"Connection error: {str(e)}")
            return {"status": "Failed", "error": f"Connection failed: {str(e)}"}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {"status": "Failed", "error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}")
            return {"status": "Failed", "error": f"{type(e).__name__}: {str(e)}"}
    
    @staticmethod
    async def generate_dimension_summary(
        api_url: str,
        api_key: Optional[str],
        dimension: str,
        questions_data: List[Dict],
        model_name: Optional[str] = "default"
    ) -> str:
        """
        Generate a professional analysis report for a specific dimension using expert prompts.
        """
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # Get the professional prompt for this dimension
        system_prompt = DIMENSION_PROMPTS.get(
            dimension,
            "You are a data governance expert analyzing survey responses."
        )
        
        # Format the survey data in a clear structure
        survey_data = "Survey Data:\n\n"
        for idx, q in enumerate(questions_data, 1):
            survey_data += f"Question {idx}: {q['text']}\n"
            survey_data += f"  Average Score: {q.get('avg_score', 'N/A')}/10\n"
            
            # Add comments if available
            comments = q.get('comments', [])
            if comments:
                survey_data += f"  Comments ({len(comments)}):\n"
                for comment in comments[:5]:  # Limit to first 5 comments to avoid token limits
                    if comment:
                        survey_data += f"    - {comment}\n"
                if len(comments) > 5:
                    survey_data += f"    ... and {len(comments) - 5} more comments\n"
            else:
                survey_data += f"  Comments: None\n"
            survey_data += "\n"
        
        # Combine the professional prompt with the survey data
        user_message = f"{system_prompt}\n\n{survey_data}"
        
        payload = {
            "model": model_name or "default",
            "messages": [
                {"role": "system", "content": f"You are an expert in {dimension}."},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 5000,
            "temperature": 0.7
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout for longer responses
                response = await client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
                
                if not content or content == "No response":
                    logger.warning(f"Empty response from LLM for dimension: {dimension}")
                    return "No analysis available. Please check LLM configuration."
                
                return content
        except httpx.TimeoutException:
            raise Exception(f"LLM API Timeout: Request took longer than 120 seconds")
        except Exception as e:
            logger.error(f"LLM API Error for {dimension}: {str(e)}")
            raise Exception(f"LLM API Error: {str(e)}")
    
    @staticmethod
    async def generate_overall_summary(
        api_url: str,
        api_key: Optional[str],
        dimension_summaries: Dict[str, str],
        model_name: Optional[str] = "default"
    ) -> str:
        """
        Generate a comprehensive overall report by synthesizing all dimension reports.
        """
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # Format the dimension reports
        dimension_reports = "Individual Dimension Reports:\n\n"
        for dimension, summary in dimension_summaries.items():
            dimension_reports += f"=== {dimension} ===\n{summary}\n\n"
        
        # Combine the professional prompt with the dimension reports
        user_message = f"{OVERALL_REPORT_PROMPT}\n\n{dimension_reports}"
        
        payload = {
            "model": model_name or "default",
            "messages": [
                {"role": "system", "content": "You are a senior data governance consultant providing executive-level insights."},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 6000,  # Increased for comprehensive overall report
            "temperature": 0.7
        }
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:  # Increased timeout for comprehensive report
                response = await client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
                
                if not content or content == "No response":
                    logger.warning("Empty response from LLM for overall report")
                    return "No overall analysis available. Please check LLM configuration."
                
                return content
        except httpx.TimeoutException:
            raise Exception(f"LLM API Timeout: Request took longer than 180 seconds")
        except Exception as e:
            logger.error(f"LLM API Error for overall report: {str(e)}")
            raise Exception(f"LLM API Error: {str(e)}")