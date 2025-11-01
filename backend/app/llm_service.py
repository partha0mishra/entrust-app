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
                    {"role": "system", "content": "You are a data governance expert writing a professional report analyzing survey responses. Write in a formal, report-style format suitable for executive review. Use third-person perspective. Do NOT use first person (I, we) or ask questions. Do NOT include interactive elements like 'Let me analyze' or 'Would you like'. Provide clear, actionable insights in markdown format with proper headers, bullet points, and line breaks."},
                    {"role": "user", "content": chunk_prompt}
                ]

                chunk_summary = await LLMService._call_llm(
                    provider, messages, max_tokens=800
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
                    {"role": "system", "content": "You are a data governance expert writing a professional executive report. Write in a formal, report-style format suitable for C-level executives and board members. Use third-person perspective. Do NOT use first person (I, we) or ask questions. Do NOT include interactive elements or conversational language. Use markdown formatting with proper line breaks and structure."},
                    {"role": "user", "content": consolidation_prompt}
                ]

                final_summary = await LLMService._call_llm(
                    provider, messages, max_tokens=1000
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

            prompt = f"""As a data governance expert, provide a comprehensive analysis of the {dimension} dimension.

METRICS:
- Average Score: {overall_metrics['avg_score']}/10
- Response Rate: {overall_metrics['response_rate']}
- Score Range: {overall_metrics['min_score']} - {overall_metrics['max_score']}
- Total Responses: {overall_metrics['total_responses']}

CATEGORY BREAKDOWN:
{category_text}

PROCESS BREAKDOWN:
{process_text}

LIFECYCLE STAGE BREAKDOWN:
{lifecycle_text}

Provide a comprehensive analysis with the following sections:

## Strategic Observations
- What do these scores indicate about organizational maturity in {dimension}?
- Which areas show strength vs weakness?
- Are there concerning patterns or trends?

## Category Analysis
- Compare category performance
- Identify highest/lowest performing categories
- Explain potential reasons for category performance differences

## Process Analysis
- Which processes need attention?
- Are processes balanced or showing uneven maturity?
- What process improvements should be prioritized?

## Lifecycle Analysis
- Which lifecycle stages are problematic?
- Is there evidence of progression issues?
- What lifecycle improvements are needed?

## Actionable Recommendations
Provide 5-7 specific, prioritized actions organized by timeframe:

**Quick Wins (< 3 months):**
- [specific actions that can be completed quickly]

**Medium-term Improvements (3-6 months):**
- [actions requiring more planning and resources]

**Strategic Initiatives (6-12 months):**
- [major transformational efforts]

Format your response in markdown with clear headers and bullet points. Be specific and actionable."""

            messages = [
                {
                    "role": "system",
                    "content": "You are a senior data governance expert writing a professional strategic report. Write in a formal, report-style format suitable for executive review. Use third-person perspective. Provide clear, actionable insights in markdown format with proper headers, bullet points, and line breaks."
                },
                {"role": "user", "content": prompt}
            ]

            content = await LLMService._call_llm(provider, messages, max_tokens=1500)

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

            prompt = f"""Analyze this {facet_type} facet of data governance:

{facet_type.upper()}: {facet_name}
Average Score: {facet_data['avg_score']}/10
Score Range: {facet_data['min_score']} - {facet_data['max_score']}
Total Responses: {facet_data['count']}
Respondents: {facet_data['respondents']}

Questions in this {facet_type}:
{questions_text}

Sample Comments:
{comments_text}

Provide analysis with these sections:

## Performance Assessment
- How is this {facet_type} performing relative to a 10-point scale?
- What does this score indicate about organizational capabilities?

## Root Cause Analysis
- Why might this {facet_type} be scoring at this level?
- What underlying factors could explain the performance?

## Specific Recommendations
- What 3-5 concrete actions should be taken to improve this {facet_type}?
- Prioritize recommendations by impact and feasibility

## Success Metrics
- What metrics should be tracked to measure improvement?
- What would "good" look like for this {facet_type} in 6-12 months?

Format in markdown with clear headers and bullet points."""

            messages = [
                {
                    "role": "system",
                    "content": "You are a data governance specialist writing a focused analysis report. Write in a professional, report-style format. Use third-person perspective. Provide specific, actionable insights."
                },
                {"role": "user", "content": prompt}
            ]

            content = await LLMService._call_llm(provider, messages, max_tokens=800)

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

            prompt = f"""Analyze these {len(comments)} survey comments (showing {sample_size} samples):

{comments_text}

Provide comprehensive comment analysis with these sections:

## Sentiment Analysis
Categorize the comments and provide percentages:
- Positive comments: X%
- Neutral comments: Y%
- Negative comments: Z%

Explain the overall sentiment trend.

## Key Themes
List the 5-7 most common themes across all comments. For each theme:
- Theme name
- Brief description
- Approximate frequency

## Top Concerns
What are respondents most worried about or frustrated with?
List 3-5 main concerns in order of frequency/severity.

## Positive Highlights
What are respondents happy about or praising?
List 3-5 positive aspects mentioned.

## Recommendations Based on Comments
What actions should be taken based on the feedback in these comments?
Provide 3-5 specific recommendations.

Format in markdown with clear headers and bullet points."""

            messages = [
                {
                    "role": "system",
                    "content": "You are a data analyst specializing in qualitative feedback analysis. Write a professional report suitable for management review. Use third-person perspective. Provide objective analysis with specific insights."
                },
                {"role": "user", "content": prompt}
            ]

            content = await LLMService._call_llm(provider, messages, max_tokens=1000)

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
                        provider, messages, max_tokens=800
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
                    provider, messages, max_tokens=1200
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
                    provider, messages, max_tokens=1200
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