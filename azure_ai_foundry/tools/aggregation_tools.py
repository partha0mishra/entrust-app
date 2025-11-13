"""
Aggregation Tools
Aggregates insights from multiple dimension reports for overall synthesis
"""

from typing import List, Dict
import statistics


def aggregate_dimension_reports(dimension_reports: List[Dict]) -> Dict:
    """
    Aggregate insights from dimension reports for overall synthesis

    Args:
        dimension_reports: List of dimension report dictionaries

    Returns:
        Dictionary with aggregated insights

    Example:
        >>> reports = [
        ...     {"dimension": "Privacy", "maturity_level": 3, "avg_score": 7.2},
        ...     {"dimension": "Security", "maturity_level": 4, "avg_score": 8.1}
        ... ]
        >>> agg = aggregate_dimension_reports(reports)
        >>> print(agg['avg_maturity'])
        3.5
    """
    if not dimension_reports:
        return {
            "avg_maturity": 0.0,
            "dimension_comparison": [],
            "cross_cutting_themes": [],
            "overall_strengths": [],
            "overall_weaknesses": [],
            "strategic_priorities": []
        }

    # Extract maturity levels and scores
    maturity_levels = []
    scores = []
    dimension_comparison = []

    for report in dimension_reports:
        dimension = report.get("dimension", "Unknown")
        maturity = report.get("metadata", {}).get("maturity_level")
        avg_score = report.get("overall_metrics", {}).get("avg_score")

        if maturity is not None:
            maturity_levels.append(maturity)

        if avg_score is not None:
            scores.append(avg_score)

        dimension_comparison.append({
            "dimension": dimension,
            "maturity_level": maturity,
            "avg_score": avg_score
        })

    # Calculate averages
    avg_maturity = round(statistics.mean(maturity_levels), 1) if maturity_levels else 0.0
    avg_score = round(statistics.mean(scores), 2) if scores else 0.0

    # Identify strengths (high maturity/scores)
    overall_strengths = []
    overall_weaknesses = []

    for comp in dimension_comparison:
        if comp["maturity_level"] and comp["maturity_level"] >= 4:
            overall_strengths.append({
                "dimension": comp["dimension"],
                "maturity_level": comp["maturity_level"],
                "reason": "High maturity level achieved"
            })
        elif comp["maturity_level"] and comp["maturity_level"] <= 2:
            overall_weaknesses.append({
                "dimension": comp["dimension"],
                "maturity_level": comp["maturity_level"],
                "reason": "Low maturity level, requires significant improvement"
            })

        if comp["avg_score"] and comp["avg_score"] < 6.0:
            if comp["dimension"] not in [w["dimension"] for w in overall_weaknesses]:
                overall_weaknesses.append({
                    "dimension": comp["dimension"],
                    "avg_score": comp["avg_score"],
                    "reason": "Below average performance"
                })

    # Identify cross-cutting themes
    # (In real implementation, this would use NLP to identify common themes across reports)
    cross_cutting_themes = _identify_cross_cutting_themes(dimension_reports)

    # Determine strategic priorities
    strategic_priorities = _determine_strategic_priorities(
        overall_weaknesses,
        dimension_comparison
    )

    return {
        "avg_maturity": avg_maturity,
        "avg_score": avg_score,
        "dimension_comparison": dimension_comparison,
        "cross_cutting_themes": cross_cutting_themes,
        "overall_strengths": overall_strengths,
        "overall_weaknesses": overall_weaknesses,
        "strategic_priorities": strategic_priorities,
        "maturity_distribution": {
            "level_1": sum(1 for m in maturity_levels if m == 1),
            "level_2": sum(1 for m in maturity_levels if m == 2),
            "level_3": sum(1 for m in maturity_levels if m == 3),
            "level_4": sum(1 for m in maturity_levels if m == 4),
            "level_5": sum(1 for m in maturity_levels if m == 5)
        }
    }


def _identify_cross_cutting_themes(dimension_reports: List[Dict]) -> List[Dict]:
    """
    Identify common themes across dimension reports

    This is a simplified implementation. In production, would use NLP
    to analyze report content and extract common themes.
    """
    themes = []

    # Check for common patterns
    low_maturity_count = sum(
        1 for r in dimension_reports
        if r.get("metadata", {}).get("maturity_level", 5) <= 2
    )

    if low_maturity_count >= len(dimension_reports) / 2:
        themes.append({
            "theme": "Organization-wide maturity challenges",
            "description": "Multiple dimensions show low maturity, indicating systemic gaps",
            "affected_dimensions": [
                r["dimension"] for r in dimension_reports
                if r.get("metadata", {}).get("maturity_level", 5) <= 2
            ]
        })

    # Check for policy/documentation themes
    policy_related = ["Privacy", "Compliance", "Governance", "Ethics"]
    policy_dims = [
        r for r in dimension_reports
        if any(p in r.get("dimension", "") for p in policy_related)
    ]

    if len(policy_dims) >= 2:
        avg_policy_score = statistics.mean([
            r.get("overall_metrics", {}).get("avg_score", 0)
            for r in policy_dims
        ])

        if avg_policy_score < 6.5:
            themes.append({
                "theme": "Policy and governance framework needs strengthening",
                "description": "Policy-related dimensions show room for improvement",
                "affected_dimensions": [r["dimension"] for r in policy_dims]
            })

    return themes


def _determine_strategic_priorities(
    weaknesses: List[Dict],
    dimension_comparison: List[Dict]
) -> List[Dict]:
    """
    Determine strategic priorities based on weaknesses and impact
    """
    priorities = []

    # Sort weaknesses by maturity/score
    sorted_weaknesses = sorted(
        weaknesses,
        key=lambda w: (
            w.get("maturity_level", 5),
            w.get("avg_score", 10)
        )
    )

    # Top 3 priorities
    for i, weakness in enumerate(sorted_weaknesses[:3]):
        priority_level = ["Critical", "High", "Medium"][i] if i < 3 else "Low"

        priorities.append({
            "priority": i + 1,
            "priority_level": priority_level,
            "dimension": weakness["dimension"],
            "current_state": {
                "maturity_level": weakness.get("maturity_level"),
                "avg_score": weakness.get("avg_score")
            },
            "rationale": weakness.get("reason", "Improvement needed"),
            "recommended_actions": [
                "Conduct detailed assessment",
                "Develop improvement roadmap",
                "Allocate resources and ownership"
            ]
        })

    return priorities


# Tool definitions for Azure AI Foundry
TOOL_DEFINITIONS = {
    "aggregate_dimension_reports": {
        "function": aggregate_dimension_reports,
        "description": "Aggregate insights from dimension reports",
        "parameters": {
            "type": "object",
            "properties": {
                "dimension_reports": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of dimension report dictionaries"
                }
            },
            "required": ["dimension_reports"]
        }
    }
}


if __name__ == "__main__":
    # Test aggregation
    print("Testing Aggregation Tools...")

    test_reports = [
        {
            "dimension": "Data Privacy & Compliance",
            "metadata": {"maturity_level": 3},
            "overall_metrics": {"avg_score": 7.2}
        },
        {
            "dimension": "Data Security & Access",
            "metadata": {"maturity_level": 4},
            "overall_metrics": {"avg_score": 8.1}
        },
        {
            "dimension": "Data Quality",
            "metadata": {"maturity_level": 2},
            "overall_metrics": {"avg_score": 5.8}
        }
    ]

    agg = aggregate_dimension_reports(test_reports)
    print(f"Average Maturity: {agg['avg_maturity']}")
    print(f"Average Score: {agg['avg_score']}")
    print(f"Strengths: {len(agg['overall_strengths'])}")
    print(f"Weaknesses: {len(agg['overall_weaknesses'])}")
    print(f"Strategic Priorities: {len(agg['strategic_priorities'])}")
