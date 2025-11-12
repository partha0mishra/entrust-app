"""
Survey Parser Agent

Analyzes JSON survey data to compute statistics and extract key themes from comments.
Uses Chain-of-Thought reasoning to break down the analysis into clear steps.
"""

import json
from typing import Dict, List, Any
from collections import defaultdict, Counter
import statistics
from .base import AgentBase, AgentResult, SurveyStats
import time


class SurveyParserAgent(AgentBase):
    """
    Parses and analyzes survey data to compute comprehensive statistics

    Capabilities:
    - Compute overall metrics (avg score, response rate, distribution)
    - Break down statistics by category, process, and lifecycle stage
    - Extract comment themes using LLM
    - Generate score distributions
    """

    def __init__(self, llm_provider=None):
        super().__init__("SurveyParserAgent", llm_provider)

    async def execute(
        self,
        dimension: str,
        questions_data: List[Dict[str, Any]]
    ) -> AgentResult:
        """
        Parse survey data and compute statistics

        Args:
            dimension: Dimension name
            questions_data: List of question dicts with scores, comments, categories, etc.

        Returns:
            AgentResult with computed statistics
        """
        start_time = time.time()
        self.log_execution("START", f"Parsing survey data for {dimension}")

        try:
            # Step 1: Compute overall statistics
            self.log_execution("STEP_1", "Computing overall statistics")
            overall_stats = self._compute_overall_stats(questions_data)

            # Step 2: Compute statistics by category
            self.log_execution("STEP_2", "Computing category statistics")
            category_stats = self._compute_facet_stats(questions_data, "category")

            # Step 3: Compute statistics by process
            self.log_execution("STEP_3", "Computing process statistics")
            process_stats = self._compute_facet_stats(questions_data, "process")

            # Step 4: Compute statistics by lifecycle stage
            self.log_execution("STEP_4", "Computing lifecycle statistics")
            lifecycle_stats = self._compute_facet_stats(questions_data, "lifecycle_stage")

            # Step 5: Extract comment themes (if LLM available)
            self.log_execution("STEP_5", "Extracting comment themes")
            comment_themes = await self._extract_comment_themes(questions_data)

            # Step 6: Compute score distribution
            self.log_execution("STEP_6", "Computing score distribution")
            score_distribution = self._compute_score_distribution(questions_data)

            # Build output
            stats = SurveyStats(
                overall=overall_stats,
                by_category=category_stats,
                by_process=process_stats,
                by_lifecycle=lifecycle_stats,
                comment_themes=comment_themes,
                score_distribution=score_distribution
            )

            execution_time = time.time() - start_time
            self.log_execution("COMPLETE", f"Parsed survey data in {execution_time:.2f}s")

            return AgentResult(
                success=True,
                agent_name=self.agent_name,
                output=stats.model_dump(),
                execution_time_seconds=execution_time
            )

        except Exception as e:
            self.logger.error(f"Error in SurveyParserAgent: {e}", exc_info=True)
            return AgentResult(
                success=False,
                agent_name=self.agent_name,
                output={},
                error=str(e),
                execution_time_seconds=time.time() - start_time
            )

    def _compute_overall_stats(self, questions_data: List[Dict]) -> Dict[str, Any]:
        """Compute overall statistics across all questions"""
        scores = []
        total_responses = 0
        comments_count = 0

        for q in questions_data:
            avg_score = q.get('avg_score')
            if avg_score is not None and avg_score != 'N/A':
                try:
                    scores.append(float(avg_score))
                except (ValueError, TypeError):
                    pass

            # Count responses
            count = q.get('count', 0)
            total_responses += count

            # Count comments
            comments = q.get('comments', [])
            if comments:
                comments_count += len(comments)

        # Compute statistics
        avg_score = statistics.mean(scores) if scores else 0
        median_score = statistics.median(scores) if scores else 0
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 0

        # Response rate (assuming 100% if not provided)
        response_rate = 100.0  # This should come from survey data

        return {
            "avg_score": round(avg_score, 2),
            "median_score": round(median_score, 2),
            "min_score": min_score,
            "max_score": max_score,
            "total_questions": len(questions_data),
            "total_responses": total_responses,
            "total_comments": comments_count,
            "response_rate": response_rate
        }

    def _compute_facet_stats(
        self,
        questions_data: List[Dict],
        facet_field: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compute statistics grouped by a facet (category, process, or lifecycle_stage)

        Args:
            questions_data: Survey data
            facet_field: Field name ('category', 'process', 'lifecycle_stage')

        Returns:
            Dictionary with stats for each facet value
        """
        facet_data = defaultdict(lambda: {
            "scores": [],
            "count": 0,
            "questions": [],
            "comments": []
        })

        for q in questions_data:
            facet_value = q.get(facet_field, "Unknown")
            if not facet_value or facet_value == "":
                facet_value = "Unknown"

            avg_score = q.get('avg_score')
            if avg_score is not None and avg_score != 'N/A':
                try:
                    facet_data[facet_value]["scores"].append(float(avg_score))
                except (ValueError, TypeError):
                    pass

            facet_data[facet_value]["count"] += q.get('count', 0)
            facet_data[facet_value]["questions"].append({
                "question_id": q.get('question_id'),
                "text": q.get('text', q.get('question', ''))
            })

            comments = q.get('comments', [])
            if comments:
                facet_data[facet_value]["comments"].extend(comments)

        # Compute statistics for each facet
        result = {}
        for facet_value, data in facet_data.items():
            scores = data["scores"]
            avg_score = statistics.mean(scores) if scores else 0

            # Score distribution
            high = sum(1 for s in scores if s >= 8)
            medium = sum(1 for s in scores if 5 <= s < 8)
            low = sum(1 for s in scores if s < 5)
            total = len(scores) if scores else 1

            result[facet_value] = {
                "avg_score": round(avg_score, 2),
                "count": data["count"],
                "question_count": len(data["questions"]),
                "questions": data["questions"],
                "comments": data["comments"],
                "score_distribution": {
                    "high": high,
                    "medium": medium,
                    "low": low,
                    "pct_high": round((high / total) * 100, 1),
                    "pct_medium": round((medium / total) * 100, 1),
                    "pct_low": round((low / total) * 100, 1)
                }
            }

        return result

    def _compute_score_distribution(self, questions_data: List[Dict]) -> Dict[str, int]:
        """Compute distribution of scores"""
        distribution = {
            "1-4 (Low)": 0,
            "5-7 (Medium)": 0,
            "8-10 (High)": 0
        }

        for q in questions_data:
            avg_score = q.get('avg_score')
            if avg_score is not None and avg_score != 'N/A':
                try:
                    score = float(avg_score)
                    if score < 5:
                        distribution["1-4 (Low)"] += 1
                    elif score < 8:
                        distribution["5-7 (Medium)"] += 1
                    else:
                        distribution["8-10 (High)"] += 1
                except (ValueError, TypeError):
                    pass

        return distribution

    async def _extract_comment_themes(self, questions_data: List[Dict]) -> List[str]:
        """
        Extract top themes from comments using LLM (if available)
        Falls back to simple keyword extraction if no LLM
        """
        # Collect all comments
        all_comments = []
        for q in questions_data:
            comments = q.get('comments', [])
            if comments:
                all_comments.extend(comments)

        if not all_comments:
            return []

        # If LLM is available, use it for theme extraction
        if self.llm_provider:
            try:
                return await self._llm_extract_themes(all_comments)
            except Exception as e:
                self.logger.warning(f"LLM theme extraction failed: {e}, using fallback")

        # Fallback: Simple keyword extraction
        return self._simple_theme_extraction(all_comments)

    async def _llm_extract_themes(self, comments: List[str]) -> List[str]:
        """Use LLM to extract top 5 themes from comments"""
        system_prompt = self.get_system_prompt()
        user_prompt = self.get_user_prompt(comments=comments)

        response = await self.call_llm(system_prompt, user_prompt, max_tokens=500)

        # Parse themes from response (expected as numbered list or JSON)
        themes = []
        for line in response.split('\n'):
            line = line.strip()
            # Extract lines that start with numbers or bullets
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering and bullets
                theme = line.lstrip('0123456789.-•) ').strip()
                if theme and len(theme) > 5:  # Valid theme
                    themes.append(theme)

        return themes[:5]  # Top 5

    def _simple_theme_extraction(self, comments: List[str]) -> List[str]:
        """Simple keyword-based theme extraction (fallback)"""
        # Extract common keywords
        words = []
        for comment in comments:
            words.extend(comment.lower().split())

        # Filter stop words (simplified)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'to', 'of', 'in', 'on', 'at', 'for', 'with', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'over', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'that', 'this', 'these', 'those'}
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]

        # Get top 5 most common
        word_counts = Counter(filtered_words)
        return [word for word, count in word_counts.most_common(5)]

    def get_system_prompt(self) -> str:
        """System prompt for comment theme extraction"""
        return """You are a data analyst specializing in extracting key themes from survey comments.
Your task is to analyze comments and identify the top 5 recurring themes or topics.
Output ONLY a numbered list of themes, one per line.
Be concise and specific."""

    def get_user_prompt(self, comments: List[str]) -> str:
        """User prompt for theme extraction"""
        # Limit to 50 comments to avoid token overflow
        sample_comments = comments[:50]
        comments_text = "\n".join([f"{i+1}. {comment}" for i, comment in enumerate(sample_comments)])

        return f"""Analyze the following survey comments and extract the top 5 themes:

{comments_text}

Output ONLY a numbered list of the top 5 themes:
1. [Theme 1]
2. [Theme 2]
3. [Theme 3]
4. [Theme 4]
5. [Theme 5]"""
