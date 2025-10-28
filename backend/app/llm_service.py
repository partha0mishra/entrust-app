import httpx
from typing import List, Dict, Optional
import json
from .llm_providers import get_llm_provider

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
                for q in chunk:
                    chunk_prompt += f"\nQuestion: {q['text']}\n"
                    chunk_prompt += f"Average Score: {q.get('avg_score', 'N/A')}\n"
                    
                    comments = q.get('comments', [])
                    if comments:
                        chunk_prompt += f"Sample Comments:\n"
                        # Limit comments to avoid too much data
                        for comment in comments[:5]:  # Max 5 comments per question
                            chunk_prompt += f"  - {comment}\n"
                
                if len(chunks) > 1:
                    chunk_prompt += f"\n\nProvide a concise analysis of this subset of questions. This is part {i+1} of {len(chunks)} parts."
                else:
                    chunk_prompt += "\n\nProvide a concise summary of the current state and actionable suggestions for improvement."
                
                messages = [
                    {"role": "system", "content": "You are a data governance expert writing a professional report analyzing survey responses. Write in a formal, report-style format suitable for executive review. Use third-person perspective. DO NOT use first person (I, we) or ask questions. DO NOT include interactive elements like 'Let me analyze' or 'Would you like'. Provide clear, actionable insights in markdown format with proper headers, bullet points, and line breaks."},
                    {"role": "user", "content": chunk_prompt}
                ]

                chunk_summary = await LLMService._call_llm(
                    provider, messages, max_tokens=8196
                )
                
                chunk_summaries.append({
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "content": chunk_summary
                })
            
            # If multiple chunks, generate final consolidated summary
            final_summary = None
            if len(chunks) > 1:
                consolidation_prompt = f"""You have analyzed {len(chunks)} parts of survey data for the {dimension} dimension. Here are the partial analyses:

"""
                for i, summary in enumerate(chunk_summaries):
                    consolidation_prompt += f"\n--- Part {i+1} Analysis ---\n{summary['content']}\n"
                
                consolidation_prompt += f"\n\nProvide a comprehensive, consolidated summary that integrates insights from all parts. Include:\n"
                consolidation_prompt += "1. **Current State**: Overall assessment\n"
                consolidation_prompt += "2. **Key Findings**: Most important insights\n"
                consolidation_prompt += "3. **Recommendations**: Actionable improvement suggestions\n\n"
                consolidation_prompt += "Use markdown formatting with clear headers and bullet points."
                
                messages = [
                    {"role": "system", "content": "You are a data governance expert writing a professional executive report. Write in a formal, report-style format suitable for C-level executives and board members. Use third-person perspective. DO NOT use first person (I, we) or ask questions. DO NOT include interactive elements or conversational language. Use markdown formatting with proper line breaks and structure."},
                    {"role": "user", "content": consolidation_prompt}
                ]

                final_summary = await LLMService._call_llm(
                    provider, messages, max_tokens=8196
                )
            
            return {
                "success": True,
                "chunk_summaries": chunk_summaries,
                "final_summary": final_summary or chunk_summaries[0]['content'] if chunk_summaries else None,
                "total_chunks": len(chunks)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chunk_summaries": [],
                "final_summary": None
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

                    chunk_summary = await LLMService._call_llm(
                        provider, messages, max_tokens=8196
                    )
                    chunk_summaries.append(chunk_summary)
                
                # Final consolidation
                final_prompt = "You have analyzed multiple groups of data governance dimensions. Here are the analyses:\n\n"
                for i, summary in enumerate(chunk_summaries):
                    final_prompt += f"\n--- Analysis Part {i+1} ---\n{summary}\n"
                
                final_prompt += """\n\nProvide a comprehensive executive summary that includes:

1. **Executive Overview**: High-level organizational data governance maturity
2. **Strengths**: Key areas of excellence across dimensions
3. **Critical Gaps**: Most urgent areas needing attention
4. **Strategic Recommendations**: Prioritized action items
5. **Roadmap Considerations**: Suggested implementation approach

Use clear markdown formatting with headers, bullet points, and proper line breaks."""
                
                messages = [
                    {"role": "system", "content": "You are a Chief Data Officer writing a professional board-level strategic report. Write in a formal, report-style format suitable for board members and C-level executives. Use third-person perspective. Do NOT use first person (I, we) or ask questions. Do NOT include interactive elements or conversational language. Use markdown formatting."},
                    {"role": "user", "content": final_prompt}
                ]

                final_summary = await LLMService._call_llm(
                    provider, messages, max_tokens=8196
                )
                
                return {
                    "success": True,
                    "content": final_summary,
                    "chunks_processed": len(chunks)
                }
            
            else:
                # Single call for smaller content
                prompt = "Analyze the following dimension summaries and provide an overall organizational data governance assessment:\n\n"
                prompt += all_summaries_text
                prompt += """\n\nProvide an executive summary with:

1. **Executive Overview**: Overall maturity assessment
2. **Key Strengths**: Areas of excellence
3. **Critical Gaps**: Urgent improvement areas
4. **Strategic Recommendations**: Prioritized actions
5. **Implementation Approach**: Suggested roadmap

Use markdown formatting with clear headers and bullet points."""
                
                messages = [
                    {"role": "system", "content": "You are a senior data governance consultant writing a professional executive report. Write in a formal, report-style format suitable for C-level executives. Use third-person perspective. Do NOT use first person (I, we) or ask questions. Do NOT include interactive elements or conversational language. Use markdown formatting."},
                    {"role": "user", "content": prompt}
                ]

                summary = await LLMService._call_llm(
                    provider, messages, max_tokens=8196
                )
                
                return {
                    "success": True,
                    "content": summary,
                    "chunks_processed": 1
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }