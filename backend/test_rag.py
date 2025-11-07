"""
Test script for RAG (Retrieval-Augmented Generation) integration
Validates knowledge base ingestion, retrieval, and context generation.
"""

import sys
import logging
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.rag import RAGService, initialize_rag, get_rag_stats, get_dimension_context, retrieve_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_rag_initialization():
    """Test RAG service initialization and knowledge base ingestion"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: RAG Initialization and Ingestion")
    logger.info("="*60)

    try:
        # Initialize RAG (should ingest knowledge base)
        result = initialize_rag(force_reingest=False)

        if result.get('success'):
            logger.info("✓ RAG initialization successful")
            if result.get('stats'):
                logger.info(f"  Files processed: {result['stats']['files_processed']}")
                logger.info(f"  Total chunks: {result['stats']['chunks_created']}")
            logger.info(f"  Total documents in collection: {result.get('total_documents', 0)}")
            return True
        else:
            logger.error(f"✗ RAG initialization failed: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"✗ Test failed with exception: {e}")
        return False


def test_rag_stats():
    """Test RAG statistics retrieval"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: RAG Statistics")
    logger.info("="*60)

    try:
        stats = get_rag_stats()

        if not stats.get('enabled'):
            logger.warning("⚠ RAG service not enabled")
            return False

        logger.info("✓ RAG statistics retrieved successfully")
        logger.info(f"  Total documents: {stats.get('total_documents', 0)}")
        logger.info(f"  Embedding model: {stats.get('embedding_model', 'N/A')}")

        logger.info("\n  Documents by dimension:")
        for dim, count in stats.get('by_dimension', {}).items():
            logger.info(f"    {dim}: {count} documents")

        return True

    except Exception as e:
        logger.error(f"✗ Test failed with exception: {e}")
        return False


def test_retrieval_basic():
    """Test basic context retrieval"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Basic Context Retrieval")
    logger.info("="*60)

    test_cases = [
        {
            "query": "What are GDPR requirements for data privacy?",
            "dimension": "Data Privacy & Compliance",
            "expected_keywords": ["gdpr", "privacy", "compliance", "regulation"]
        },
        {
            "query": "How to implement data quality controls?",
            "dimension": "Data Quality",
            "expected_keywords": ["quality", "accuracy", "completeness", "validation"]
        },
        {
            "query": "Data lineage best practices",
            "dimension": "Data Lineage & Traceability",
            "expected_keywords": ["lineage", "traceability", "metadata", "tracking"]
        }
    ]

    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n  Test Case {i}:")
        logger.info(f"    Query: {test_case['query']}")
        logger.info(f"    Dimension: {test_case['dimension']}")

        try:
            context = retrieve_context(
                query=test_case['query'],
                dimension=test_case['dimension'],
                top_k=3
            )

            if context:
                logger.info(f"    ✓ Context retrieved ({len(context)} chars)")
                logger.info(f"    Preview: {context[:200]}...")

                # Check for expected keywords (case-insensitive)
                context_lower = context.lower()
                found_keywords = [kw for kw in test_case['expected_keywords'] if kw in context_lower]

                if found_keywords:
                    logger.info(f"    ✓ Found relevant keywords: {', '.join(found_keywords)}")
                    passed += 1
                else:
                    logger.warning(f"    ⚠ No expected keywords found in context")
            else:
                logger.warning(f"    ⚠ No context retrieved (empty result)")

        except Exception as e:
            logger.error(f"    ✗ Retrieval failed: {e}")

    logger.info(f"\n  Passed: {passed}/{len(test_cases)} test cases")
    return passed == len(test_cases)


def test_dimension_context():
    """Test dimension-specific context retrieval with survey summary"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Dimension Context with Survey Summary")
    logger.info("="*60)

    test_cases = [
        {
            "dimension": "Data Privacy & Compliance",
            "survey_summary": "Average score: 6.5/10, Low scores in encryption and access controls"
        },
        {
            "dimension": "Data Security & Access",
            "survey_summary": "Average score: 4.2/10, Critical gaps in authentication and monitoring"
        }
    ]

    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n  Test Case {i}:")
        logger.info(f"    Dimension: {test_case['dimension']}")
        logger.info(f"    Survey Summary: {test_case['survey_summary']}")

        try:
            context = get_dimension_context(
                dimension=test_case['dimension'],
                survey_summary=test_case['survey_summary']
            )

            if context:
                logger.info(f"    ✓ Context retrieved ({len(context)} chars)")
                logger.info(f"    Preview: {context[:200]}...")
                passed += 1
            else:
                logger.warning(f"    ⚠ No context retrieved")

        except Exception as e:
            logger.error(f"    ✗ Retrieval failed: {e}")

    logger.info(f"\n  Passed: {passed}/{len(test_cases)} test cases")
    return passed == len(test_cases)


def test_empty_query():
    """Test edge case: empty query"""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Edge Case - Empty Query")
    logger.info("="*60)

    try:
        context = retrieve_context(query="", dimension="Data Quality")
        if context == "":
            logger.info("  ✓ Empty query handled correctly (returned empty string)")
            return True
        else:
            logger.warning(f"  ⚠ Unexpected result for empty query: {len(context)} chars")
            return False
    except Exception as e:
        logger.info(f"  ✓ Empty query raised exception as expected: {type(e).__name__}")
        return True


def test_invalid_dimension():
    """Test edge case: invalid dimension"""
    logger.info("\n" + "="*60)
    logger.info("TEST 6: Edge Case - Invalid Dimension")
    logger.info("="*60)

    try:
        context = retrieve_context(
            query="Test query",
            dimension="Invalid Dimension That Does Not Exist"
        )

        # Should return empty or handle gracefully
        if context == "":
            logger.info("  ✓ Invalid dimension handled correctly (returned empty)")
            return True
        else:
            logger.info(f"  ⚠ Returned some context despite invalid dimension: {len(context)} chars")
            return True  # Still acceptable if it returns generic context

    except Exception as e:
        logger.error(f"  ✗ Invalid dimension caused exception: {e}")
        return False


def test_maturity_context():
    """Test retrieval of maturity model context"""
    logger.info("\n" + "="*60)
    logger.info("TEST 7: Maturity Model Context Retrieval")
    logger.info("="*60)

    try:
        # Query for maturity-related content
        context = retrieve_context(
            query="DAMA-DMBOK maturity levels and progression",
            dimension="Organizational Maturity",
            top_k=3
        )

        if context:
            logger.info(f"  ✓ Maturity context retrieved ({len(context)} chars)")

            # Check for maturity-related keywords
            maturity_keywords = ['maturity', 'dama', 'level', 'initial', 'managed', 'optimized', 'gartner']
            found = [kw for kw in maturity_keywords if kw.lower() in context.lower()]

            if found:
                logger.info(f"  ✓ Found maturity keywords: {', '.join(found)}")
                return True
            else:
                logger.warning("  ⚠ No maturity keywords found")
                return False
        else:
            logger.warning("  ⚠ No maturity context retrieved")
            return False

    except Exception as e:
        logger.error(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all RAG tests"""
    logger.info("\n" + "="*80)
    logger.info("RAG INTEGRATION TEST SUITE")
    logger.info("="*80)

    tests = [
        ("RAG Initialization", test_rag_initialization),
        ("RAG Statistics", test_rag_stats),
        ("Basic Retrieval", test_retrieval_basic),
        ("Dimension Context", test_dimension_context),
        ("Empty Query Edge Case", test_empty_query),
        ("Invalid Dimension Edge Case", test_invalid_dimension),
        ("Maturity Context", test_maturity_context),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            logger.error(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"  {status}: {test_name}")

    logger.info(f"\n  Total: {passed_count}/{total_count} tests passed")
    logger.info("="*80)

    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
