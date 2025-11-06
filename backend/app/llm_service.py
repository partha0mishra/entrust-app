import httpx
from typing import List, Dict, Optional
import json
from .llm_providers import get_llm_provider
import re
from .prompts import (
    PROMPT_ADD_ON,
    OVERALL_SUMMARY_PROMPT_ADD_ON,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_USER_PROMPT_TEMPLATE,
    DIMENSION_PROMPTS,
    get_deep_dimension_analysis_prompt,
    get_facet_analysis_prompt,
    get_comment_analysis_prompt,
    DEEP_DIMENSION_ANALYSIS_SYSTEM_PROMPT,
    FACET_ANALYSIS_SYSTEM_PROMPT,
    COMMENT_ANALYSIS_SYSTEM_PROMPT,
    get_overall_summary_chunked_prompt,
    get_overall_summary_consolidation_prompt,
    get_overall_summary_single_prompt,
    OVERALL_SUMMARY_SYSTEM_PROMPT,
    CONSOLIDATION_SYSTEM_PROMPT
)

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
        max_tokens: Optional[int] = None
    ) -> str:
        """Helper method to call LLM API using provider
        
        If max_tokens is not provided, automatically determines based on provider:
        - For GPT-5 (Azure OpenAI): 30000 (configured limit)
        - For AWS Bedrock with thinking mode: 15000 (to accommodate budget_tokens)
        - For AWS Bedrock without thinking mode: 8000 (faster responses)
        - For Azure OpenAI (other models): 8000 (standard)
        - For others: 8000 (default)
        """
        if max_tokens is None:
            # Auto-detect appropriate max_tokens based on provider
            # Check if this is GPT-5 model
            is_gpt5 = hasattr(provider, 'deployment_name') and provider.deployment_name and provider.deployment_name.startswith('gpt-5')
            
            if is_gpt5:
                max_tokens = 30000  # GPT-5 configured to 30k output tokens
            elif hasattr(provider, 'thinking_mode') and provider.thinking_mode == "enabled":
                max_tokens = 15000  # For thinking mode, need at least 1.5x budget_tokens
            else:
                max_tokens = 8000  # For non-thinking mode, use reasonable default
        
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
                # Get dimension-specific prompts or use defaults
                if dimension in DIMENSION_PROMPTS:
                    system_prompt = DIMENSION_PROMPTS[dimension]["system"]
                    user_prompt_template = DIMENSION_PROMPTS[dimension]["user"]
                else:
                    system_prompt = PROMPT_ADD_ON + DEFAULT_SYSTEM_PROMPT
                    user_prompt_template = DEFAULT_USER_PROMPT_TEMPLATE

                # Build the chunk prompt
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

                chunk_summary = await LLMService._call_llm(
                    provider, messages  # Auto-determines max_tokens based on thinking mode
                )

                chunk_summaries.append({
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "content": chunk_summary,
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

                final_summary = await LLMService._call_llm(
                    provider, messages  # Auto-determines max_tokens based on thinking mode
                )
            
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
    async def generate_deep_dimension_analysis(
        config,
        dimension: str,
        overall_metrics: Dict,
        questions_data: List[Dict],
        category_analysis: Dict,
        process_analysis: Dict,
        lifecycle_analysis: Dict
    ) -> Dict:
        """
        Generate comprehensive dimension analysis including all facets
        """
        try:
            provider = get_llm_provider(config)

            # Format category breakdown
            category_text = "\n".join([
                f"- {name}: Avg Score {data['avg_score']}/10 ({data['count']} responses)"
                for name, data in category_analysis.items()
                if data['avg_score'] is not None
            ]) if category_analysis else "No category data available"

            # Format process breakdown
            process_text = "\n".join([
                f"- {name}: Avg Score {data['avg_score']}/10 ({data['count']} responses)"
                for name, data in process_analysis.items()
                if data['avg_score'] is not None
            ]) if process_analysis else "No process data available"

            # Format lifecycle breakdown
            lifecycle_text = "\n".join([
                f"- {name}: Avg Score {data['avg_score']}/10 ({data['count']} responses)"
                for name, data in lifecycle_analysis.items()
                if data['avg_score'] is not None
            ]) if lifecycle_analysis else "No lifecycle stage data available"

            # Get the prompt from the prompts module
            prompt = get_deep_dimension_analysis_prompt(
                dimension,
                overall_metrics,
                category_text,
                process_text,
                lifecycle_text
            )

            messages = [
                {
                    "role": "system",
                    "content": DEEP_DIMENSION_ANALYSIS_SYSTEM_PROMPT
                },
                {"role": "user", "content": prompt}
            ]

            content = await LLMService._call_llm(provider, messages)  # Auto-determines max_tokens based on thinking mode

            return {
                "success": True,
                "content": content
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }

    @staticmethod
    async def analyze_facet(
        config,
        facet_type: str,
        facet_name: str,
        facet_data: Dict
    ) -> Dict:
        """
        Analyze specific facet (category/process/lifecycle stage)
        """
        try:
            provider = get_llm_provider(config)

            # Format questions
            questions_text = "\n".join([
                f"- {q['text']} (ID: {q['question_id']})"
                for q in facet_data.get('questions', [])
            ])

            # Format sample comments (limit to 10)
            comments = facet_data.get('comments', [])[:10]
            comments_text = "\n".join([f"- \"{comment}\"" for comment in comments]) if comments else "No comments available"

            # Get the prompt from the prompts module
            prompt = get_facet_analysis_prompt(
                facet_type,
                facet_name,
                facet_data,
                questions_text,
                comments_text
            )

            messages = [
                {
                    "role": "system",
                    "content": FACET_ANALYSIS_SYSTEM_PROMPT
                },
                {"role": "user", "content": prompt}
            ]

            content = await LLMService._call_llm(provider, messages)  # Auto-determines max_tokens based on thinking mode

            return {
                "success": True,
                "content": content
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }

    @staticmethod
    async def analyze_comments_sentiment(
        config,
        comments: List[str]
    ) -> Dict:
        """
        LLM-based sentiment and thematic analysis of comments
        """
        try:
            provider = get_llm_provider(config)

            # Limit comments to avoid token overflow
            sample_size = min(len(comments), 50)
            sampled_comments = comments[:sample_size]
            comments_text = "\n".join([f"{i+1}. \"{comment}\"" for i, comment in enumerate(sampled_comments)])

            # Get the prompt from the prompts module
            prompt = get_comment_analysis_prompt(
                len(comments),
                sample_size,
                comments_text
            )

            messages = [
                {
                    "role": "system",
                    "content": COMMENT_ANALYSIS_SYSTEM_PROMPT
                },
                {"role": "user", "content": prompt}
            ]

            content = await LLMService._call_llm(provider, messages)  # Auto-determines max_tokens based on thinking mode

            return {
                "success": True,
                "content": content
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
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
                
                # Process each chunk using proper prompt function
                chunk_summaries = []
                for i, chunk in enumerate(chunks):
                    # Build chunk data text
                    chunk_data = ""
                    for dimension, summary in chunk.items():
                        chunk_data += f"## {dimension}\n{summary}\n\n"
                    
                    # Use proper prompt function
                    chunk_prompt = get_overall_summary_chunked_prompt(i, len(chunks), chunk_data)
                    
                    messages = [
                        {"role": "system", "content": CONSOLIDATION_SYSTEM_PROMPT},
                        {"role": "user", "content": chunk_prompt}
                    ]

                    chunk_summary = await LLMService._call_llm(
                        provider, messages, max_tokens=20000
                    )
                    chunk_summaries.append(chunk_summary)
                
                # Final consolidation using proper prompt function
                final_prompt = get_overall_summary_consolidation_prompt(chunk_summaries)
                
                messages = [
                    {"role": "system", "content": OVERALL_SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": final_prompt}
                ]

                final_summary = await LLMService._call_llm(
                    provider, messages  # Auto-determines max_tokens based on thinking mode
                )

                return {
                    "success": True,
                    "markdown_content": final_summary,
                    "json_content": None,
                    "chunks_processed": len(chunks)
                }

            else:
                # Single call for smaller content using proper prompt function
                prompt = get_overall_summary_single_prompt(all_summaries_text)

                messages = [
                    {"role": "system", "content": OVERALL_SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]

                summary = await LLMService._call_llm(
                    provider, messages  # Auto-determines max_tokens based on thinking mode
                )

                return {
                    "success": True,
                    "markdown_content": summary,
                    "json_content": None,
                    "chunks_processed": 1
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "markdown_content": None
            }