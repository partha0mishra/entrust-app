"""
RAG (Retrieval-Augmented Generation) Tools
Integrates with ChromaDB knowledge base for standards retrieval
"""

import sys
import os
from typing import Optional

# Add backend to path to access existing RAG service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

try:
    from app.rag import get_dimension_context, get_rag_service, retrieve_context
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    import logging
    logging.warning("Backend RAG service not available. Install dependencies or check path.")


def query_rag_standards(dimension: str, query: str, top_k: int = 5) -> str:
    """
    Query ChromaDB knowledge base for relevant standards and best practices

    This tool is used by the Maturity Assessor Agent to retrieve industry
    standards context (GDPR, DAMA-DMBOK, NIST, ISO 8000) for grounding
    maturity assessments.

    Args:
        dimension: Data dimension name (e.g., "Data Privacy & Compliance")
        query: Search query describing what standards info is needed
        top_k: Number of top results to retrieve (default: 5)

    Returns:
        Formatted string with relevant standards context

    Example:
        >>> context = query_rag_standards(
        ...     dimension="Data Privacy & Compliance",
        ...     query="GDPR requirements for data privacy policies",
        ...     top_k=5
        ... )
        >>> print(context)
        **Relevant Standards and Best Practices:**

        1. [GDPR_Article_5.txt]
        Article 5 of GDPR outlines principles for processing personal data...
    """
    if not RAG_AVAILABLE:
        return "RAG service not available. Standards context cannot be retrieved."

    try:
        # Use existing RAG service from backend
        context = retrieve_context(query=query, dimension=dimension, top_k=top_k)

        if not context:
            return f"No standards context found for dimension '{dimension}' and query '{query}'"

        return context

    except Exception as e:
        import logging
        logging.error(f"Error querying RAG: {e}")
        return f"Error retrieving standards context: {str(e)}"


def get_dimension_standards(dimension: str, survey_summary: Optional[str] = None, top_k: int = 5) -> str:
    """
    Get comprehensive standards context for a specific dimension

    This is a convenience wrapper around query_rag_standards that constructs
    an appropriate query for comprehensive dimension standards.

    Args:
        dimension: Data dimension name
        survey_summary: Optional summary of survey data for context-aware retrieval
        top_k: Number of results to retrieve

    Returns:
        Formatted standards context string

    Example:
        >>> context = get_dimension_standards(
        ...     dimension="Data Security & Access",
        ...     survey_summary="Average score: 6.5/10, weak areas: encryption, access controls"
        ... )
    """
    if not RAG_AVAILABLE:
        return "RAG service not available. Standards context cannot be retrieved."

    try:
        # Use existing get_dimension_context from backend
        context = get_dimension_context(
            dimension=dimension,
            survey_summary=survey_summary,
            top_k=top_k
        )

        if not context:
            return f"No standards context found for dimension '{dimension}'"

        return context

    except Exception as e:
        import logging
        logging.error(f"Error getting dimension standards: {e}")
        return f"Error retrieving dimension standards: {str(e)}"


def get_rag_statistics() -> dict:
    """
    Get statistics about the RAG knowledge base

    Returns:
        Dictionary with RAG stats (enabled, total_documents, by_dimension, etc.)
    """
    if not RAG_AVAILABLE:
        return {"enabled": False, "error": "RAG service not available"}

    try:
        service = get_rag_service()
        return service.get_stats()
    except Exception as e:
        return {"enabled": False, "error": str(e)}


# For Azure AI Foundry tool registration
# These will be wrapped with @tool decorator when deploying to Foundry

TOOL_DEFINITIONS = {
    "query_rag_standards": {
        "function": query_rag_standards,
        "description": "Query knowledge base for industry standards and best practices",
        "parameters": {
            "type": "object",
            "properties": {
                "dimension": {
                    "type": "string",
                    "description": "Data dimension name (e.g., 'Data Privacy & Compliance')"
                },
                "query": {
                    "type": "string",
                    "description": "Search query for standards information"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to retrieve",
                    "default": 5
                }
            },
            "required": ["dimension", "query"]
        }
    },
    "get_dimension_standards": {
        "function": get_dimension_standards,
        "description": "Get comprehensive standards context for a dimension",
        "parameters": {
            "type": "object",
            "properties": {
                "dimension": {
                    "type": "string",
                    "description": "Data dimension name"
                },
                "survey_summary": {
                    "type": "string",
                    "description": "Optional survey summary for context-aware retrieval"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to retrieve",
                    "default": 5
                }
            },
            "required": ["dimension"]
        }
    }
}


if __name__ == "__main__":
    # Test the RAG tools
    print("Testing RAG Tools...")
    print("=" * 60)

    # Test query_rag_standards
    result = query_rag_standards(
        dimension="Data Privacy & Compliance",
        query="GDPR requirements and best practices",
        top_k=3
    )
    print("Query Result:")
    print(result[:500] + "..." if len(result) > 500 else result)
    print("\n" + "=" * 60)

    # Test get_dimension_standards
    result = get_dimension_standards(
        dimension="Data Security & Access",
        survey_summary="Average score: 6.5/10"
    )
    print("\nDimension Standards Result:")
    print(result[:500] + "..." if len(result) > 500 else result)
    print("\n" + "=" * 60)

    # Test stats
    stats = get_rag_statistics()
    print("\nRAG Statistics:")
    print(stats)
