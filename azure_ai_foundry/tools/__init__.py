"""
Custom tools for Azure AI Foundry agents
"""

from .rag_tools import query_rag_standards, get_dimension_standards
from .stats_tools import (
    compute_survey_statistics,
    compute_maturity_score,
    identify_risk_areas,
    calculate_score_distribution
)
from .graph_tools import (
    generate_score_distribution_chart,
    generate_dimension_comparison_radar,
    generate_word_cloud,
    generate_category_heatmap
)
from .pdf_tools import convert_markdown_to_pdf
from .storage_tools import save_reports_to_disk
from .data_loader import load_survey_from_db
from .aggregation_tools import aggregate_dimension_reports

__all__ = [
    # RAG tools
    "query_rag_standards",
    "get_dimension_standards",

    # Stats tools
    "compute_survey_statistics",
    "compute_maturity_score",
    "identify_risk_areas",
    "calculate_score_distribution",

    # Graph tools
    "generate_score_distribution_chart",
    "generate_dimension_comparison_radar",
    "generate_word_cloud",
    "generate_category_heatmap",

    # PDF tools
    "convert_markdown_to_pdf",

    # Storage tools
    "save_reports_to_disk",

    # Data loader
    "load_survey_from_db",

    # Aggregation tools
    "aggregate_dimension_reports"
]
