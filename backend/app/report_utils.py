import os
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
from decimal import Decimal

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime, Decimal, and other non-serializable types"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

# Base path for reports - mounted at /app/entrust in Docker
REPORTS_BASE_PATH = "/app/entrust"

# Dimension mapping with underscores to avoid spaces
# Supports both with and without "Data" prefix
DIMENSION_MAP = {
    # With "Data" prefix (as stored in database)
    "Data Privacy & Compliance": "privacy_compliance",
    "Data Ethics & Bias": "ethics_bias",
    "Data Lineage & Traceability": "lineage_traceability",
    "Data Value & Lifecycle Management": "value_lifecycle",
    "Data Governance & Management": "governance_management",
    "Data Security & Access": "security_access",
    "Metadata & Documentation": "metadata_documentation",
    "Data Quality": "quality",

    # Without "Data" prefix (for backwards compatibility)
    "Privacy & Compliance": "privacy_compliance",
    "Ethics & Bias": "ethics_bias",
    "Lineage & Traceability": "lineage_traceability",
    "Value & Lifecycle": "value_lifecycle",
    "Governance & Management": "governance_management",
    "Security & Access": "security_access",
    "Quality": "quality",

    # Overall (no Data prefix)
    "Overall": "overall"
}


def get_dimension_filename(dimension: str) -> str:
    """Convert dimension name to filename-safe format with underscores"""
    # If dimension is already in the mapped format, use it
    if dimension.lower() in [v.lower() for v in DIMENSION_MAP.values()]:
        return dimension.lower()

    # Otherwise, look it up in the mapping
    return DIMENSION_MAP.get(dimension, dimension.lower().replace(" ", "_").replace("&", ""))


def check_reports_path_exists() -> bool:
    """Check if the reports base path exists"""
    return os.path.exists(REPORTS_BASE_PATH) and os.path.isdir(REPORTS_BASE_PATH)


def get_report_paths(customer_code: str, dimension: str) -> Dict[str, str]:
    """
    Get the full paths for markdown and JSON reports

    Args:
        customer_code: Customer code
        dimension: Dimension name

    Returns:
        Dict with 'markdown' and 'json' paths
    """
    dimension_filename = get_dimension_filename(dimension)
    date_str = datetime.now().strftime("%Y%m%d")

    markdown_dir = os.path.join(REPORTS_BASE_PATH, "reports", customer_code)
    json_dir = os.path.join(REPORTS_BASE_PATH, "report_json", customer_code)

    markdown_path = os.path.join(markdown_dir, f"{dimension_filename}_report_{date_str}.md")
    json_path = os.path.join(json_dir, f"{dimension_filename}_report_{date_str}.json")

    return {
        "markdown": markdown_path,
        "json": json_path,
        "markdown_dir": markdown_dir,
        "json_dir": json_dir
    }


def create_markdown_report(
    dimension: str,
    customer_code: str,
    customer_name: str,
    overall_metrics: Optional[Dict],
    questions: List[Dict],
    dimension_analysis: Optional[str] = None,
    category_analysis: Optional[Dict] = None,
    process_analysis: Optional[Dict] = None,
    lifecycle_analysis: Optional[Dict] = None,
    comment_insights: Optional[Dict] = None,
    dimension_summaries: Optional[Dict] = None,
    overall_summary: Optional[str] = None
) -> str:
    """
    Create a markdown report with questions table and scores

    Returns:
        Markdown content as string
    """
    date_str = datetime.now().strftime("%Y-%m-%d")

    markdown = f"""# {dimension} Report

**Customer:** {customer_name} ({customer_code})
**Date:** {date_str}
**Dimension:** {dimension}

---

"""

    # Add overall metrics for dimension reports
    if overall_metrics:
        markdown += f"""## Overview

- **Average Score:** {overall_metrics.get('avg_score', 'N/A')}
- **Response Rate:** {overall_metrics.get('response_rate', 'N/A')}
- **Total Responses:** {overall_metrics.get('total_responses', 0)}
- **Total Respondents:** {overall_metrics.get('total_respondents', 0)}/{overall_metrics.get('total_users', 0)}

---

"""

    # Add overall summary for Overall reports
    if overall_summary:
        markdown += f"""## Executive Summary

{overall_summary}

---

"""

    # Add dimension-level analysis
    if dimension_analysis:
        markdown += f"""## Strategic Analysis & Recommendations

{dimension_analysis}

---

"""

    # Add dimension summaries for Overall reports
    if dimension_summaries:
        markdown += """## Dimension Analysis

"""
        for dim, summary in dimension_summaries.items():
            markdown += f"""### {dim}

{summary}

---

"""

    # Add category analysis
    if category_analysis and len(category_analysis) > 0:
        markdown += """## Category Analysis

| Category | Avg Score | % High (8-10) | % Medium (5-7) | % Low (1-4) | Response Count |
|----------|-----------|---------------|----------------|-------------|----------------|
"""
        for cat_name, cat_data in category_analysis.items():
            avg_score = cat_data.get('avg_score', 'N/A')
            avg_score_str = f"{avg_score:.2f}" if isinstance(avg_score, (int, float)) and avg_score is not None else 'N/A'

            score_dist = cat_data.get('score_distribution', {})
            pct_high = score_dist.get('pct_high', 0)
            pct_medium = score_dist.get('pct_medium', 0)
            pct_low = score_dist.get('pct_low', 0)

            pct_high_str = f"{pct_high}%" if pct_high > 0 else "0%"
            pct_medium_str = f"{pct_medium}%" if pct_medium > 0 else "0%"
            pct_low_str = f"{pct_low}%" if pct_low > 0 else "0%"

            count = cat_data.get('count', 0)

            markdown += f"| {cat_name} | {avg_score_str} | {pct_high_str} | {pct_medium_str} | {pct_low_str} | {count} |\n"

        markdown += "\n---\n\n"

    # Add process analysis
    if process_analysis and len(process_analysis) > 0:
        markdown += """## Process Analysis

| Process | Avg Score | % High (8-10) | % Medium (5-7) | % Low (1-4) | Response Count |
|---------|-----------|---------------|----------------|-------------|----------------|
"""
        for proc_name, proc_data in process_analysis.items():
            avg_score = proc_data.get('avg_score', 'N/A')
            avg_score_str = f"{avg_score:.2f}" if isinstance(avg_score, (int, float)) and avg_score is not None else 'N/A'

            score_dist = proc_data.get('score_distribution', {})
            pct_high = score_dist.get('pct_high', 0)
            pct_medium = score_dist.get('pct_medium', 0)
            pct_low = score_dist.get('pct_low', 0)

            pct_high_str = f"{pct_high}%" if pct_high > 0 else "0%"
            pct_medium_str = f"{pct_medium}%" if pct_medium > 0 else "0%"
            pct_low_str = f"{pct_low}%" if pct_low > 0 else "0%"

            count = proc_data.get('count', 0)

            markdown += f"| {proc_name} | {avg_score_str} | {pct_high_str} | {pct_medium_str} | {pct_low_str} | {count} |\n"

        markdown += "\n---\n\n"

    # Add lifecycle analysis
    if lifecycle_analysis and len(lifecycle_analysis) > 0:
        markdown += """## Lifecycle Stage Analysis

| Lifecycle Stage | Avg Score | % High (8-10) | % Medium (5-7) | % Low (1-4) | Response Count |
|----------------|-----------|---------------|----------------|-------------|----------------|
"""
        for lc_name, lc_data in lifecycle_analysis.items():
            avg_score = lc_data.get('avg_score', 'N/A')
            avg_score_str = f"{avg_score:.2f}" if isinstance(avg_score, (int, float)) and avg_score is not None else 'N/A'

            score_dist = lc_data.get('score_distribution', {})
            pct_high = score_dist.get('pct_high', 0)
            pct_medium = score_dist.get('pct_medium', 0)
            pct_low = score_dist.get('pct_low', 0)

            pct_high_str = f"{pct_high}%" if pct_high > 0 else "0%"
            pct_medium_str = f"{pct_medium}%" if pct_medium > 0 else "0%"
            pct_low_str = f"{pct_low}%" if pct_low > 0 else "0%"

            count = lc_data.get('count', 0)

            markdown += f"| {lc_name} | {avg_score_str} | {pct_high_str} | {pct_medium_str} | {pct_low_str} | {count} |\n"

        markdown += "\n---\n\n"

    # Add comment insights
    if comment_insights and comment_insights.get('total_comments', 0) > 0:
        markdown += f"""## Comment Analysis

- **Total Comments:** {comment_insights.get('total_comments', 0)}
- **Positive Comments:** {comment_insights.get('positive_count', 0)}
- **Negative Comments:** {comment_insights.get('negative_count', 0)}
- **Neutral Comments:** {comment_insights.get('neutral_count', 0)}
- **Average Comment Length:** {comment_insights.get('avg_comment_length', 0)} characters

"""

        if comment_insights.get('llm_analysis'):
            markdown += f"""### Sentiment & Themes Analysis

{comment_insights['llm_analysis']}

"""

        markdown += "---\n\n"

    # Add questions table
    if questions and len(questions) > 0:
        markdown += """## Question-Level Details

| Q# | Question | Category | Process | Lifecycle | Avg Score |
|----|----------|----------|---------|-----------|-----------|
"""
        for q in questions:
            q_id = q.get('question_id', '-')
            q_text = q.get('question', 'N/A')
            category = q.get('category', '-')
            process = q.get('process', '-')
            lifecycle = q.get('lifecycle_stage', '-')
            avg_score = q.get('avg_score')
            avg_score_str = f"{avg_score:.2f}" if avg_score is not None else '-'

            # Escape pipe characters in the question text
            q_text = q_text.replace('|', '\\|')

            markdown += f"| {q_id} | {q_text} | {category} | {process} | {lifecycle} | {avg_score_str} |\n"

        markdown += "\n---\n\n"

    markdown += f"""
*Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    return markdown


def save_reports(
    customer_code: str,
    customer_name: str,
    dimension: str,
    report_data: Dict,
    rag_context: Optional[str] = None
) -> Dict[str, Optional[str]]:
    """
    Save reports in both markdown and JSON formats

    Args:
        customer_code: Customer code
        customer_name: Customer name
        dimension: Dimension name
        report_data: Complete report data dictionary
        rag_context: Optional RAG context that was retrieved

    Returns:
        Dict with 'markdown_path' and 'json_path' (None if path doesn't exist or save failed)
    """
    result = {
        "markdown_path": None,
        "json_path": None,
        "error": None
    }

    # Check if base path exists
    if not check_reports_path_exists():
        logger.warning(f"Reports base path {REPORTS_BASE_PATH} does not exist. Skipping report save.")
        result["error"] = f"Reports path {REPORTS_BASE_PATH} not accessible"
        return result

    try:
        paths = get_report_paths(customer_code, dimension)

        # Create directories if they don't exist
        os.makedirs(paths['markdown_dir'], exist_ok=True)
        os.makedirs(paths['json_dir'], exist_ok=True)

        # Create markdown report
        markdown_content = create_markdown_report(
            dimension=dimension,
            customer_code=customer_code,
            customer_name=customer_name,
            overall_metrics=report_data.get('overall_metrics'),
            questions=report_data.get('questions', []) or report_data.get('overall_stats', {}).get('dimensions', []),
            dimension_analysis=report_data.get('dimension_llm_analysis'),
            category_analysis=report_data.get('category_analysis'),
            process_analysis=report_data.get('process_analysis'),
            lifecycle_analysis=report_data.get('lifecycle_analysis'),
            comment_insights=report_data.get('comment_insights'),
            dimension_summaries=report_data.get('dimension_summaries'),
            overall_summary=report_data.get('overall_summary')
        )

        # Save markdown
        with open(paths['markdown'], 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        result['markdown_path'] = paths['markdown']
        logger.info(f"Saved markdown report to {paths['markdown']}")

        # Create JSON report with full context
        json_data = {
            "customer_code": customer_code,
            "customer_name": customer_name,
            "dimension": dimension,
            "generated_at": datetime.now().isoformat(),
            "report_data": report_data,
            "rag_context": rag_context
        }

        # Save JSON with custom encoder to handle datetime and other types
        with open(paths['json'], 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
        result['json_path'] = paths['json']
        logger.info(f"Saved JSON report to {paths['json']}")

    except Exception as e:
        logger.error(f"Error saving reports: {str(e)}\n{traceback.format_exc()}")
        result["error"] = str(e)

    return result


def get_cached_report(customer_code: str, dimension: str, survey_updated_at: datetime) -> Optional[Dict]:
    """
    Get cached report if it exists and is newer than the survey update time

    Args:
        customer_code: Customer code
        dimension: Dimension name
        survey_updated_at: When the survey was last updated

    Returns:
        Cached report data or None if not available/stale
    """
    if not check_reports_path_exists():
        return None

    try:
        paths = get_report_paths(customer_code, dimension)
        json_path = paths['json']

        # Check if JSON report exists
        if not os.path.exists(json_path):
            logger.info(f"No cached report found at {json_path}")
            return None

        # Check file modification time
        file_mtime = datetime.fromtimestamp(os.path.getmtime(json_path))

        # If survey was updated after report was generated, cache is stale
        if survey_updated_at and file_mtime < survey_updated_at:
            logger.info(f"Cached report is stale (report: {file_mtime}, survey: {survey_updated_at})")
            return None

        # Load and return cached report
        with open(json_path, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)

        logger.info(f"Using cached report from {json_path}")
        return cached_data.get('report_data')

    except Exception as e:
        logger.error(f"Error loading cached report: {str(e)}")
        return None
