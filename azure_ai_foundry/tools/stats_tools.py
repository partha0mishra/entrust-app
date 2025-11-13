"""
Statistical Analysis Tools
Provides functions for computing survey statistics and maturity scores
"""

from typing import Dict, List, Optional
import statistics


def compute_survey_statistics(survey_data: Dict) -> Dict:
    """
    Compute comprehensive statistics from survey data

    Args:
        survey_data: Survey data dictionary with questions, scores, comments

    Returns:
        Dictionary with computed statistics

    Example:
        >>> stats = compute_survey_statistics({
        ...     "questions": [
        ...         {"avg_score": 7.5, "count": 10},
        ...         {"avg_score": 6.2, "count": 10}
        ...     ]
        ... })
    """
    questions = survey_data.get("questions", [])

    if not questions:
        return {
            "overall_metrics": {
                "avg_score": None,
                "min_score": None,
                "max_score": None,
                "total_responses": 0
            },
            "score_distribution": {
                "high": {"count": 0, "percentage": 0.0},
                "medium": {"count": 0, "percentage": 0.0},
                "low": {"count": 0, "percentage": 0.0}
            }
        }

    # Extract all scores
    scores = []
    total_responses = 0
    for q in questions:
        if "avg_score" in q and q["avg_score"] is not None:
            scores.append(float(q["avg_score"]))
            total_responses += q.get("count", 1)

    if not scores:
        return {
            "overall_metrics": {
                "avg_score": None,
                "min_score": None,
                "max_score": None,
                "total_responses": 0
            },
            "score_distribution": {
                "high": {"count": 0, "percentage": 0.0},
                "medium": {"count": 0, "percentage": 0.0},
                "low": {"count": 0, "percentage": 0.0}
            }
        }

    # Compute overall metrics
    avg_score = round(statistics.mean(scores), 2)
    min_score = round(min(scores), 2)
    max_score = round(max(scores), 2)
    median_score = round(statistics.median(scores), 2)
    std_dev = round(statistics.stdev(scores), 2) if len(scores) > 1 else 0.0

    # Compute score distribution
    high_scores = [s for s in scores if s >= 8.0]
    medium_scores = [s for s in scores if 5.0 <= s < 8.0]
    low_scores = [s for s in scores if s < 5.0]

    total = len(scores)
    distribution = {
        "high": {
            "count": len(high_scores),
            "percentage": round((len(high_scores) / total * 100), 1)
        },
        "medium": {
            "count": len(medium_scores),
            "percentage": round((len(medium_scores) / total * 100), 1)
        },
        "low": {
            "count": len(low_scores),
            "percentage": round((len(low_scores) / total * 100), 1)
        }
    }

    return {
        "overall_metrics": {
            "avg_score": avg_score,
            "min_score": min_score,
            "max_score": max_score,
            "median_score": median_score,
            "std_dev": std_dev,
            "total_responses": total_responses,
            "total_questions": len(questions)
        },
        "score_distribution": distribution
    }


def compute_maturity_score(
    scores: List[float],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate weighted maturity score on 1-5 scale

    Args:
        scores: List of scores (typically 0-10 scale)
        weights: Optional weights for different score ranges

    Returns:
        Maturity level (1-5)

    Maturity Mapping:
        1 (Initial): avg < 3.0
        2 (Developing): 3.0 <= avg < 5.0
        3 (Defined): 5.0 <= avg < 7.0
        4 (Managed): 7.0 <= avg < 8.5
        5 (Optimizing): avg >= 8.5
    """
    if not scores:
        return 1.0  # Default to lowest maturity

    avg_score = statistics.mean(scores)

    # Map 0-10 score to 1-5 maturity level
    if avg_score < 3.0:
        return 1.0  # Initial
    elif avg_score < 5.0:
        return 2.0  # Developing
    elif avg_score < 7.0:
        return 3.0  # Defined
    elif avg_score < 8.5:
        return 4.0  # Managed
    else:
        return 5.0  # Optimizing


def identify_risk_areas(
    survey_data: Dict,
    threshold: float = 5.0
) -> List[Dict]:
    """
    Identify low-scoring areas requiring immediate attention

    Args:
        survey_data: Survey data with questions and scores
        threshold: Score threshold for risk (default: 5.0)

    Returns:
        List of risk area dictionaries

    Example:
        >>> risks = identify_risk_areas(survey_data, threshold=5.0)
        >>> for risk in risks:
        ...     print(f"{risk['area']}: {risk['avg_score']}")
    """
    questions = survey_data.get("questions", [])
    risk_areas = []

    for q in questions:
        avg_score = q.get("avg_score")
        if avg_score is not None and avg_score < threshold:
            risk_areas.append({
                "area": q.get("text", "Unknown"),
                "avg_score": round(avg_score, 2),
                "category": q.get("category", "N/A"),
                "process": q.get("process", "N/A"),
                "lifecycle_stage": q.get("lifecycle_stage", "N/A"),
                "severity": _calculate_severity(avg_score),
                "reason": _generate_risk_reason(avg_score, threshold)
            })

    # Sort by score (lowest first)
    risk_areas.sort(key=lambda x: x["avg_score"])

    return risk_areas


def calculate_score_distribution(scores: List[float]) -> Dict:
    """
    Calculate detailed score distribution statistics

    Args:
        scores: List of scores

    Returns:
        Dictionary with distribution statistics
    """
    if not scores:
        return {
            "mean": 0.0,
            "median": 0.0,
            "mode": 0.0,
            "std_dev": 0.0,
            "quartiles": {"q1": 0.0, "q2": 0.0, "q3": 0.0},
            "range": {"min": 0.0, "max": 0.0}
        }

    sorted_scores = sorted(scores)
    n = len(sorted_scores)

    return {
        "mean": round(statistics.mean(scores), 2),
        "median": round(statistics.median(scores), 2),
        "mode": round(statistics.mode(scores), 2) if len(set(scores)) < n else None,
        "std_dev": round(statistics.stdev(scores), 2) if n > 1 else 0.0,
        "quartiles": {
            "q1": round(statistics.quantiles(sorted_scores, n=4)[0], 2) if n >= 4 else sorted_scores[0],
            "q2": round(statistics.quantiles(sorted_scores, n=4)[1], 2) if n >= 4 else statistics.median(scores),
            "q3": round(statistics.quantiles(sorted_scores, n=4)[2], 2) if n >= 4 else sorted_scores[-1]
        },
        "range": {
            "min": round(min(scores), 2),
            "max": round(max(scores), 2)
        },
        "percentiles": {
            "p10": round(sorted_scores[max(0, int(n * 0.1))], 2),
            "p25": round(sorted_scores[max(0, int(n * 0.25))], 2),
            "p50": round(sorted_scores[max(0, int(n * 0.50))], 2),
            "p75": round(sorted_scores[max(0, int(n * 0.75))], 2),
            "p90": round(sorted_scores[max(0, int(n * 0.90))], 2)
        }
    }


def _calculate_severity(score: float) -> str:
    """Calculate risk severity based on score"""
    if score < 3.0:
        return "Critical"
    elif score < 5.0:
        return "High"
    elif score < 7.0:
        return "Medium"
    else:
        return "Low"


def _generate_risk_reason(score: float, threshold: float) -> str:
    """Generate human-readable reason for risk"""
    gap = threshold - score
    if gap >= 3.0:
        return f"Significantly below threshold (gap: {round(gap, 1)} points)"
    elif gap >= 2.0:
        return f"Moderately below threshold (gap: {round(gap, 1)} points)"
    else:
        return f"Slightly below threshold (gap: {round(gap, 1)} points)"


# Tool definitions for Azure AI Foundry
TOOL_DEFINITIONS = {
    "compute_survey_statistics": {
        "function": compute_survey_statistics,
        "description": "Compute comprehensive statistics from survey data",
        "parameters": {
            "type": "object",
            "properties": {
                "survey_data": {
                    "type": "object",
                    "description": "Survey data with questions and scores"
                }
            },
            "required": ["survey_data"]
        }
    },
    "compute_maturity_score": {
        "function": compute_maturity_score,
        "description": "Calculate maturity level (1-5) from scores",
        "parameters": {
            "type": "object",
            "properties": {
                "scores": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of scores"
                },
                "weights": {
                    "type": "object",
                    "description": "Optional weights dictionary"
                }
            },
            "required": ["scores"]
        }
    },
    "identify_risk_areas": {
        "function": identify_risk_areas,
        "description": "Identify low-scoring areas requiring attention",
        "parameters": {
            "type": "object",
            "properties": {
                "survey_data": {
                    "type": "object",
                    "description": "Survey data with questions"
                },
                "threshold": {
                    "type": "number",
                    "description": "Score threshold for risk",
                    "default": 5.0
                }
            },
            "required": ["survey_data"]
        }
    }
}


if __name__ == "__main__":
    # Test the stats tools
    print("Testing Stats Tools...")
    print("=" * 60)

    test_data = {
        "questions": [
            {"text": "Q1", "avg_score": 7.5, "count": 10},
            {"text": "Q2", "avg_score": 4.2, "count": 10},
            {"text": "Q3", "avg_score": 8.9, "count": 10},
            {"text": "Q4", "avg_score": 6.1, "count": 10}
        ]
    }

    # Test compute_survey_statistics
    stats = compute_survey_statistics(test_data)
    print("Survey Statistics:")
    print(f"  Average Score: {stats['overall_metrics']['avg_score']}")
    print(f"  Distribution: High={stats['score_distribution']['high']['percentage']}%, "
          f"Medium={stats['score_distribution']['medium']['percentage']}%, "
          f"Low={stats['score_distribution']['low']['percentage']}%")

    # Test compute_maturity_score
    scores = [7.5, 4.2, 8.9, 6.1]
    maturity = compute_maturity_score(scores)
    print(f"\nMaturity Level: {maturity}")

    # Test identify_risk_areas
    risks = identify_risk_areas(test_data, threshold=5.0)
    print(f"\nRisk Areas ({len(risks)}):")
    for risk in risks:
        print(f"  - {risk['area']}: {risk['avg_score']} ({risk['severity']})")
