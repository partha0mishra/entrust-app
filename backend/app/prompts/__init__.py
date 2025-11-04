"""
Prompts module for LLM service
Centralizes all prompts used across the application
"""

from .base_prompts import (
    PROMPT_ADD_ON,
    OVERALL_SUMMARY_PROMPT_ADD_ON,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_USER_PROMPT_TEMPLATE
)

from .dimension_prompts import DIMENSION_PROMPTS

from .analysis_prompts import (
    get_deep_dimension_analysis_prompt,
    get_facet_analysis_prompt,
    get_comment_analysis_prompt,
    DEEP_DIMENSION_ANALYSIS_SYSTEM_PROMPT,
    FACET_ANALYSIS_SYSTEM_PROMPT,
    COMMENT_ANALYSIS_SYSTEM_PROMPT
)

from .overall_summary_prompts import (
    get_overall_summary_chunked_prompt,
    get_overall_summary_consolidation_prompt,
    get_overall_summary_single_prompt,
    OVERALL_SUMMARY_SYSTEM_PROMPT,
    CONSOLIDATION_SYSTEM_PROMPT
)

__all__ = [
    # Base prompts
    'PROMPT_ADD_ON',
    'OVERALL_SUMMARY_PROMPT_ADD_ON',
    'DEFAULT_SYSTEM_PROMPT',
    'DEFAULT_USER_PROMPT_TEMPLATE',

    # Dimension prompts
    'DIMENSION_PROMPTS',

    # Analysis prompts
    'get_deep_dimension_analysis_prompt',
    'get_facet_analysis_prompt',
    'get_comment_analysis_prompt',
    'DEEP_DIMENSION_ANALYSIS_SYSTEM_PROMPT',
    'FACET_ANALYSIS_SYSTEM_PROMPT',
    'COMMENT_ANALYSIS_SYSTEM_PROMPT',

    # Overall summary prompts
    'get_overall_summary_chunked_prompt',
    'get_overall_summary_consolidation_prompt',
    'get_overall_summary_single_prompt',
    'OVERALL_SUMMARY_SYSTEM_PROMPT',
    'CONSOLIDATION_SYSTEM_PROMPT',
]
