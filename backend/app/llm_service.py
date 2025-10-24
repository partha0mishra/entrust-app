import httpx
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class LLMService:
    @staticmethod
    async def test_llm_connection(
        api_url: str, 
        api_key: Optional[str] = None,
        model_name: Optional[str] = "default"  # NEW PARAMETER
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
            "model": model_name or "default",  # USE MODEL NAME
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
        model_name: Optional[str] = "default"  # NEW PARAMETER
    ) -> str:
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        prompt = f"""Analyze the following survey responses for the {dimension} dimension and provide a summary and suggestions:

Questions and Responses:
"""
        for q in questions_data:
            prompt += f"\nQuestion: {q['text']}\n"
            prompt += f"Average Score: {q.get('avg_score', 'N/A')}\n"
            prompt += f"Comments: {q.get('comments', [])}\n"
        
        prompt += "\n\nProvide a concise summary of the current state and actionable suggestions for improvement."
        
        payload = {
            "model": model_name or "default",  # USE MODEL NAME
            "messages": [
                {"role": "system", "content": "You are a data governance expert analyzing survey responses."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 5000
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
        except Exception as e:
            raise Exception(f"LLM API Error: {str(e)}")
    
    @staticmethod
    async def generate_overall_summary(
        api_url: str,
        api_key: Optional[str],
        dimension_summaries: Dict[str, str],
        model_name: Optional[str] = "default"  # NEW PARAMETER
    ) -> str:
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        prompt = "Analyze the following dimension summaries and provide an overall organizational data governance assessment:\n\n"
        for dimension, summary in dimension_summaries.items():
            prompt += f"{dimension}:\n{summary}\n\n"
        
        prompt += "\nProvide an executive summary with key insights and strategic recommendations."
        
        payload = {
            "model": model_name or "default",  # USE MODEL NAME
            "messages": [
                {"role": "system", "content": "You are a senior data governance consultant providing executive-level insights."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 5000
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
        except Exception as e:
            raise Exception(f"LLM API Error: {str(e)}")