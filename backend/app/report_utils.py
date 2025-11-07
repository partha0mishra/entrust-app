import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
from .storage_service import StorageService

logger = logging.getLogger(__name__)

# Base path for reports - mounted at /app/entrust in Docker
REPORTS_BASE_PATH = "/app/entrust"

# Dimension mapping with underscores to avoid spaces
DIMENSION_MAP = {
    "Privacy & Compliance": "privacy_compliance",
    "Ethics & Bias": "ethics_bias",
    "Lineage & Traceability": "lineage_traceability",
    "Value & Lifecycle": "value_lifecycle",
    "Governance & Management": "governance_management",
    "Security & Access": "security_access",
    "Metadata & Documentation": "metadata_documentation",
    "Quality": "quality",
    "Overall": "overall"
}


def get_dimension_filename(dimension: str) -> str:
    """Convert dimension name to filename-safe format with underscores"""
    import re

    # Strict validation to prevent path traversal
    if not dimension or len(dimension) > 100:
        raise ValueError(f"Invalid dimension name length: {dimension}")

    # Only allow alphanumeric, spaces, hyphens, underscores, and ampersands
    if not re.match(r'^[a-zA-Z0-9_\-\s&]+$', dimension):
        raise ValueError(f"Invalid dimension name characters: {dimension}")

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
    Get the full paths for markdown, JSON, and HTML reports

    Args:
        customer_code: Customer code
        dimension: Dimension name

    Returns:
        Dict with 'markdown', 'json', and 'html' paths
    """
    import re

    # Validate customer_code to prevent path traversal
    if not customer_code or len(customer_code) > 50:
        raise ValueError(f"Invalid customer code length: {customer_code}")

    if not re.match(r'^[A-Z0-9_\-]+$', customer_code):
        raise ValueError(f"Invalid customer code characters: {customer_code}")

    dimension_filename = get_dimension_filename(dimension)
    date_str = datetime.now().strftime("%Y%m%d")

    markdown_dir = os.path.join(REPORTS_BASE_PATH, "reports", customer_code)
    json_dir = os.path.join(REPORTS_BASE_PATH, "report_json", customer_code)
    html_dir = os.path.join(REPORTS_BASE_PATH, "reports_html", customer_code)

    markdown_path = os.path.join(markdown_dir, f"{dimension_filename}_report_{date_str}.md")
    json_path = os.path.join(json_dir, f"{dimension_filename}_report_{date_str}.json")
    html_path = os.path.join(html_dir, f"{dimension_filename}_report_{date_str}.html")

    return {
        "markdown": markdown_path,
        "json": json_path,
        "html": html_path,
        "markdown_dir": markdown_dir,
        "json_dir": json_dir,
        "html_dir": html_dir
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


def create_html_report(
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
    overall_summary: Optional[str] = None,
    category_llm_analyses: Optional[Dict] = None,
    process_llm_analyses: Optional[Dict] = None,
    lifecycle_llm_analyses: Optional[Dict] = None
) -> str:
    """
    Create an HTML report with embedded CSS styled like the on-screen display

    Returns:
        HTML content as string
    """
    import html
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def markdown_to_html(md_text):
        """Simple markdown to HTML converter for analysis text"""
        if not md_text:
            return ""

        # Escape HTML
        text = html.escape(md_text)

        # Convert markdown formatting
        import re
        # Headers
        text = re.sub(r'^### (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)

        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

        # Lists
        lines = text.split('\n')
        in_list = False
        result_lines = []
        for line in lines:
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                result_lines.append(f'<li>{line.strip()[2:]}</li>')
            elif line.strip().startswith(tuple(f'{i}.' for i in range(10))):
                if not in_list:
                    result_lines.append('<ol>')
                    in_list = True
                # Remove number and dot
                content = re.sub(r'^\d+\.\s*', '', line.strip())
                result_lines.append(f'<li>{content}</li>')
            else:
                if in_list:
                    # Check if previous list was ordered or unordered
                    if '<ol>' in result_lines[-10:]:
                        result_lines.append('</ol>')
                    else:
                        result_lines.append('</ul>')
                    in_list = False
                if line.strip():
                    result_lines.append(f'<p>{line}</p>')
                else:
                    result_lines.append('<br>')

        if in_list:
            if '<ol>' in result_lines[-20:]:
                result_lines.append('</ol>')
            else:
                result_lines.append('</ul>')

        return '\n'.join(result_lines)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dimension} Report - {customer_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f3f4f6;
            padding: 2rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 2rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .header {{
            border-bottom: 3px solid #10b981;
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}

        .header h1 {{
            font-size: 2rem;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }}

        .header .meta {{
            color: #6b7280;
            font-size: 0.95rem;
        }}

        .section {{
            margin-bottom: 2rem;
        }}

        .section h2 {{
            font-size: 1.5rem;
            color: #1f2937;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e5e7eb;
        }}

        .section h3 {{
            font-size: 1.25rem;
            color: #374151;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }}

        .section h4 {{
            font-size: 1.1rem;
            color: #4b5563;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .metric-card {{
            background: #f9fafb;
            padding: 1.25rem;
            border-radius: 0.5rem;
            border: 1px solid #e5e7eb;
        }}

        .metric-card .value {{
            font-size: 1.75rem;
            font-weight: bold;
            color: #10b981;
            margin-bottom: 0.25rem;
        }}

        .metric-card .label {{
            font-size: 0.875rem;
            color: #6b7280;
        }}

        .analysis-box {{
            background: linear-gradient(to right, #f0fdf4, #ecfdf5);
            border: 2px solid #86efac;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .analysis-box.summary {{
            background: linear-gradient(to right, #faf5ff, #f3e8ff);
            border-color: #d8b4fe;
        }}

        .analysis-box h3 {{
            color: #065f46;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
        }}

        .analysis-box.summary h3 {{
            color: #6b21a8;
        }}

        .analysis-box .icon {{
            font-size: 1.5rem;
            margin-right: 0.5rem;
        }}

        .facet-analysis {{
            background: #fefce8;
            border: 2px solid #fde047;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .facet-analysis h4 {{
            color: #854d0e;
            margin-bottom: 0.75rem;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: white;
        }}

        table thead {{
            background: #f3f4f6;
        }}

        table th {{
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #d1d5db;
        }}

        table td {{
            padding: 0.75rem;
            border-bottom: 1px solid #e5e7eb;
        }}

        table tbody tr:hover {{
            background: #f9fafb;
        }}

        .score {{
            font-weight: 600;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
        }}

        .score.high {{
            background: #d1fae5;
            color: #065f46;
        }}

        .score.medium {{
            background: #fef3c7;
            color: #92400e;
        }}

        .score.low {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .comment-analysis {{
            background: #eff6ff;
            border: 2px solid #93c5fd;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .comment-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }}

        .comment-stat {{
            background: white;
            padding: 0.75rem;
            border-radius: 0.375rem;
            text-align: center;
        }}

        .comment-stat .value {{
            font-size: 1.25rem;
            font-weight: bold;
            color: #1e40af;
        }}

        .comment-stat .label {{
            font-size: 0.8rem;
            color: #6b7280;
        }}

        .footer {{
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 0.875rem;
        }}

        p {{
            margin-bottom: 0.75rem;
            line-height: 1.7;
        }}

        ul, ol {{
            margin-left: 1.5rem;
            margin-bottom: 0.75rem;
        }}

        li {{
            margin-bottom: 0.5rem;
        }}

        strong {{
            font-weight: 600;
            color: #1f2937;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{html.escape(dimension)} Report</h1>
            <div class="meta">
                <strong>Customer:</strong> {html.escape(customer_name)} ({html.escape(customer_code)})<br>
                <strong>Date:</strong> {date_str}<br>
                <strong>Dimension:</strong> {html.escape(dimension)}
            </div>
        </div>
"""

    # Add overall metrics for dimension reports
    if overall_metrics:
        html_content += f"""
        <div class="section">
            <h2>Overview</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value">{overall_metrics.get('avg_score', 'N/A')}</div>
                    <div class="label">Average Score</div>
                </div>
                <div class="metric-card">
                    <div class="value">{overall_metrics.get('response_rate', 'N/A')}</div>
                    <div class="label">Response Rate</div>
                </div>
                <div class="metric-card">
                    <div class="value">{overall_metrics.get('total_responses', 0)}</div>
                    <div class="label">Total Responses</div>
                </div>
                <div class="metric-card">
                    <div class="value">{overall_metrics.get('total_respondents', 0)}/{overall_metrics.get('total_users', 0)}</div>
                    <div class="label">Respondents</div>
                </div>
            </div>
        </div>
"""

    # Add overall summary for Overall reports
    if overall_summary:
        html_content += f"""
        <div class="section">
            <div class="analysis-box summary">
                <h3><span class="icon">🤖</span>Executive Summary</h3>
                <div class="content">
                    {markdown_to_html(overall_summary)}
                </div>
            </div>
        </div>
"""

    # Add dimension-level analysis
    if dimension_analysis:
        html_content += f"""
        <div class="section">
            <div class="analysis-box">
                <h3><span class="icon">📊</span>Strategic Analysis & Recommendations</h3>
                <div class="content">
                    {markdown_to_html(dimension_analysis)}
                </div>
            </div>
        </div>
"""

    # Add dimension summaries for Overall reports
    if dimension_summaries:
        html_content += """
        <div class="section">
            <h2>Dimension Analysis</h2>
"""
        for dim, summary in dimension_summaries.items():
            html_content += f"""
            <div class="analysis-box">
                <h3>{html.escape(dim)}</h3>
                <div class="content">
                    {markdown_to_html(summary)}
                </div>
            </div>
"""
        html_content += """
        </div>
"""

    # Add category analysis
    if category_analysis and len(category_analysis) > 0:
        html_content += """
        <div class="section">
            <h2>Category Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Avg Score</th>
                        <th>% High (8-10)</th>
                        <th>% Medium (5-7)</th>
                        <th>% Low (1-4)</th>
                        <th>Responses</th>
                    </tr>
                </thead>
                <tbody>
"""
        for cat_name, cat_data in category_analysis.items():
            avg_score = cat_data.get('avg_score', 'N/A')
            avg_score_str = f"{avg_score:.2f}" if isinstance(avg_score, (int, float)) and avg_score is not None else 'N/A'

            score_class = 'medium'
            if isinstance(avg_score, (int, float)):
                if avg_score >= 8.0:
                    score_class = 'high'
                elif avg_score < 5.0:
                    score_class = 'low'

            score_dist = cat_data.get('score_distribution', {})
            pct_high = score_dist.get('pct_high', 0)
            pct_medium = score_dist.get('pct_medium', 0)
            pct_low = score_dist.get('pct_low', 0)
            count = cat_data.get('count', 0)

            html_content += f"""
                    <tr>
                        <td><strong>{html.escape(cat_name)}</strong></td>
                        <td><span class="score {score_class}">{avg_score_str}</span></td>
                        <td>{pct_high}%</td>
                        <td>{pct_medium}%</td>
                        <td>{pct_low}%</td>
                        <td>{count}</td>
                    </tr>
"""

        html_content += """
                </tbody>
            </table>
"""

        # Add category LLM analyses
        if category_llm_analyses:
            for cat_name, analysis in category_llm_analyses.items():
                if analysis:
                    html_content += f"""
            <div class="facet-analysis">
                <h4>{html.escape(cat_name)} - Detailed Insights</h4>
                <div class="content">
                    {markdown_to_html(analysis)}
                </div>
            </div>
"""

        html_content += """
        </div>
"""

    # Add process analysis
    if process_analysis and len(process_analysis) > 0:
        html_content += """
        <div class="section">
            <h2>Process Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Process</th>
                        <th>Avg Score</th>
                        <th>% High (8-10)</th>
                        <th>% Medium (5-7)</th>
                        <th>% Low (1-4)</th>
                        <th>Responses</th>
                    </tr>
                </thead>
                <tbody>
"""
        for proc_name, proc_data in process_analysis.items():
            avg_score = proc_data.get('avg_score', 'N/A')
            avg_score_str = f"{avg_score:.2f}" if isinstance(avg_score, (int, float)) and avg_score is not None else 'N/A'

            score_class = 'medium'
            if isinstance(avg_score, (int, float)):
                if avg_score >= 8.0:
                    score_class = 'high'
                elif avg_score < 5.0:
                    score_class = 'low'

            score_dist = proc_data.get('score_distribution', {})
            pct_high = score_dist.get('pct_high', 0)
            pct_medium = score_dist.get('pct_medium', 0)
            pct_low = score_dist.get('pct_low', 0)
            count = proc_data.get('count', 0)

            html_content += f"""
                    <tr>
                        <td><strong>{html.escape(proc_name)}</strong></td>
                        <td><span class="score {score_class}">{avg_score_str}</span></td>
                        <td>{pct_high}%</td>
                        <td>{pct_medium}%</td>
                        <td>{pct_low}%</td>
                        <td>{count}</td>
                    </tr>
"""

        html_content += """
                </tbody>
            </table>
"""

        # Add process LLM analyses
        if process_llm_analyses:
            for proc_name, analysis in process_llm_analyses.items():
                if analysis:
                    html_content += f"""
            <div class="facet-analysis">
                <h4>{html.escape(proc_name)} - Detailed Insights</h4>
                <div class="content">
                    {markdown_to_html(analysis)}
                </div>
            </div>
"""

        html_content += """
        </div>
"""

    # Add lifecycle analysis
    if lifecycle_analysis and len(lifecycle_analysis) > 0:
        html_content += """
        <div class="section">
            <h2>Lifecycle Stage Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Lifecycle Stage</th>
                        <th>Avg Score</th>
                        <th>% High (8-10)</th>
                        <th>% Medium (5-7)</th>
                        <th>% Low (1-4)</th>
                        <th>Responses</th>
                    </tr>
                </thead>
                <tbody>
"""
        for lc_name, lc_data in lifecycle_analysis.items():
            avg_score = lc_data.get('avg_score', 'N/A')
            avg_score_str = f"{avg_score:.2f}" if isinstance(avg_score, (int, float)) and avg_score is not None else 'N/A'

            score_class = 'medium'
            if isinstance(avg_score, (int, float)):
                if avg_score >= 8.0:
                    score_class = 'high'
                elif avg_score < 5.0:
                    score_class = 'low'

            score_dist = lc_data.get('score_distribution', {})
            pct_high = score_dist.get('pct_high', 0)
            pct_medium = score_dist.get('pct_medium', 0)
            pct_low = score_dist.get('pct_low', 0)
            count = lc_data.get('count', 0)

            html_content += f"""
                    <tr>
                        <td><strong>{html.escape(lc_name)}</strong></td>
                        <td><span class="score {score_class}">{avg_score_str}</span></td>
                        <td>{pct_high}%</td>
                        <td>{pct_medium}%</td>
                        <td>{pct_low}%</td>
                        <td>{count}</td>
                    </tr>
"""

        html_content += """
                </tbody>
            </table>
"""

        # Add lifecycle LLM analyses
        if lifecycle_llm_analyses:
            for lc_name, analysis in lifecycle_llm_analyses.items():
                if analysis:
                    html_content += f"""
            <div class="facet-analysis">
                <h4>{html.escape(lc_name)} - Detailed Insights</h4>
                <div class="content">
                    {markdown_to_html(analysis)}
                </div>
            </div>
"""

        html_content += """
        </div>
"""

    # Add comment insights
    if comment_insights and comment_insights.get('total_comments', 0) > 0:
        html_content += f"""
        <div class="section">
            <div class="comment-analysis">
                <h2>Comment Analysis</h2>
                <div class="comment-stats">
                    <div class="comment-stat">
                        <div class="value">{comment_insights.get('total_comments', 0)}</div>
                        <div class="label">Total Comments</div>
                    </div>
                    <div class="comment-stat">
                        <div class="value">{comment_insights.get('positive_count', 0)}</div>
                        <div class="label">Positive</div>
                    </div>
                    <div class="comment-stat">
                        <div class="value">{comment_insights.get('negative_count', 0)}</div>
                        <div class="label">Negative</div>
                    </div>
                    <div class="comment-stat">
                        <div class="value">{comment_insights.get('neutral_count', 0)}</div>
                        <div class="label">Neutral</div>
                    </div>
                    <div class="comment-stat">
                        <div class="value">{int(comment_insights.get('avg_comment_length', 0))}</div>
                        <div class="label">Avg Length</div>
                    </div>
                </div>
"""

        if comment_insights.get('llm_analysis'):
            html_content += f"""
                <div style="margin-top: 1rem; background: white; padding: 1rem; border-radius: 0.375rem;">
                    <h4 style="color: #1e40af; margin-bottom: 0.5rem;">Sentiment & Themes Analysis</h4>
                    {markdown_to_html(comment_insights['llm_analysis'])}
                </div>
"""

        html_content += """
            </div>
        </div>
"""

    # Add questions table
    if questions and len(questions) > 0:
        html_content += """
        <div class="section">
            <h2>Question-Level Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>Q#</th>
                        <th>Question</th>
                        <th>Category</th>
                        <th>Process</th>
                        <th>Lifecycle</th>
                        <th>Avg Score</th>
                    </tr>
                </thead>
                <tbody>
"""
        for q in questions:
            q_id = q.get('question_id', '-')
            q_text = html.escape(q.get('question', 'N/A'))
            category = html.escape(q.get('category', '-'))
            process = html.escape(q.get('process', '-'))
            lifecycle = html.escape(q.get('lifecycle_stage', '-'))
            avg_score = q.get('avg_score')
            avg_score_str = f"{avg_score:.2f}" if avg_score is not None else '-'

            score_class = 'medium'
            if avg_score is not None:
                if avg_score >= 8.0:
                    score_class = 'high'
                elif avg_score < 5.0:
                    score_class = 'low'

            html_content += f"""
                    <tr>
                        <td>{q_id}</td>
                        <td>{q_text}</td>
                        <td>{category}</td>
                        <td>{process}</td>
                        <td>{lifecycle}</td>
                        <td><span class="score {score_class}">{avg_score_str}</span></td>
                    </tr>
"""

        html_content += """
                </tbody>
            </table>
        </div>
"""

    # Footer
    html_content += f"""
        <div class="footer">
            <p>Report generated on {time_str}</p>
            <p>This report was automatically generated by the Entrust Data Trust Assessment platform.</p>
        </div>
    </div>
</body>
</html>
"""

    return html_content


def save_reports(
    customer_code: str,
    customer_name: str,
    dimension: str,
    report_data: Dict,
    rag_context: Optional[str] = None,
    customer=None
) -> Dict[str, Optional[str]]:
    """
    Save reports in markdown, JSON, and HTML formats using customer storage configuration

    Args:
        customer_code: Customer code
        customer_name: Customer name
        dimension: Dimension name
        report_data: Complete report data dictionary
        rag_context: Optional RAG context that was retrieved
        customer: Customer model instance (for storage configuration)

    Returns:
        Dict with 'markdown_path', 'json_path', and 'html_path' (None if path doesn't exist or save failed)
    """
    result = {
        "markdown_path": None,
        "json_path": None,
        "html_path": None,
        "error": None,
        "storage_type": "LOCAL"  # Default
    }

    try:
        # Initialize storage service with customer configuration
        storage_service = StorageService(customer)
        result["storage_type"] = storage_service.storage_type

        # For cloud storage, check if local path exists for fallback
        if storage_service.storage_type != "LOCAL" and storage_service.fallback_enabled:
            if not check_reports_path_exists():
                logger.warning(f"Local fallback path {REPORTS_BASE_PATH} does not exist. Cloud-only mode.")

        paths = get_report_paths(customer_code, dimension)

        # Create directories if using local storage or fallback
        if storage_service.storage_type == "LOCAL" or storage_service.fallback_enabled:
            if check_reports_path_exists():
                os.makedirs(paths['markdown_dir'], exist_ok=True)
                os.makedirs(paths['json_dir'], exist_ok=True)
                os.makedirs(paths['html_dir'], exist_ok=True)

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
        success, error = storage_service.save_file(paths['markdown'], markdown_content, 'text/markdown')
        if success:
            result['markdown_path'] = paths['markdown']
            logger.info(f"Saved markdown report: {paths['markdown']}")
        else:
            logger.error(f"Failed to save markdown report: {error}")

        # Create HTML report
        html_content = create_html_report(
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
            overall_summary=report_data.get('overall_summary'),
            category_llm_analyses=report_data.get('category_llm_analyses'),
            process_llm_analyses=report_data.get('process_llm_analyses'),
            lifecycle_llm_analyses=report_data.get('lifecycle_llm_analyses')
        )

        # Save HTML
        success, error = storage_service.save_file(paths['html'], html_content, 'text/html')
        if success:
            result['html_path'] = paths['html']
            logger.info(f"Saved HTML report: {paths['html']}")
        else:
            logger.error(f"Failed to save HTML report: {error}")

        # Create JSON report with full context
        json_data = {
            "customer_code": customer_code,
            "customer_name": customer_name,
            "dimension": dimension,
            "generated_at": datetime.now().isoformat(),
            "report_data": report_data,
            "rag_context": rag_context
        }

        # Save JSON
        json_content = json.dumps(json_data, indent=2, ensure_ascii=False)
        success, error = storage_service.save_file(paths['json'], json_content, 'application/json')
        if success:
            result['json_path'] = paths['json']
            logger.info(f"Saved JSON report: {paths['json']}")
        else:
            logger.error(f"Failed to save JSON report: {error}")

        # Report summary
        if result['markdown_path'] or result['json_path'] or result['html_path']:
            logger.info(f"Report saved successfully to {result['storage_type']} storage")
        else:
            result["error"] = "Failed to save any report files"

    except Exception as e:
        logger.error(f"Error saving reports: {str(e)}")
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


def check_report_exists_for_today(customer_code: str, dimension: str) -> Dict[str, bool]:
    """
    Check if reports exist for today for a given dimension

    Args:
        customer_code: Customer code
        dimension: Dimension name

    Returns:
        Dict with boolean flags for markdown, json, and html existence
    """
    if not check_reports_path_exists():
        return {
            "markdown_exists": False,
            "json_exists": False,
            "html_exists": False
        }

    try:
        paths = get_report_paths(customer_code, dimension)

        return {
            "markdown_exists": os.path.exists(paths['markdown']),
            "json_exists": os.path.exists(paths['json']),
            "html_exists": os.path.exists(paths['html']),
            "html_path": paths['html'] if os.path.exists(paths['html']) else None
        }

    except Exception as e:
        logger.error(f"Error checking report existence: {str(e)}")
        return {
            "markdown_exists": False,
            "json_exists": False,
            "html_exists": False
        }
