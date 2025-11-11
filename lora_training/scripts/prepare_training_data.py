"""
Extract and prepare training data from JSON reports
Creates instruction-following datasets for fine-tuning
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import sys
from datetime import datetime

# Add configs to path
sys.path.append(str(Path(__file__).parent.parent))
from configs.training_config import DIMENSIONS, REPORTS_BASE_PATH, DATA_OUTPUT_PATH


def extract_training_examples(report_data: Dict, dimension: str, rag_context: str = None) -> List[Dict]:
    """
    Extract training examples from a report
    Creates instruction-response pairs suitable for fine-tuning

    Args:
        report_data: Report data dictionary
        dimension: Dimension name
        rag_context: RAG context (industry standards, best practices) to include in training
    """
    examples = []

    # Extract dimension analysis
    if report_data.get("dimension_llm_analysis"):
        examples.append({
            "instruction": f"Analyze the {dimension} dimension based on the following survey data and provide a comprehensive assessment.",
            "input": create_input_context(report_data, rag_context),
            "output": report_data["dimension_llm_analysis"]
        })

    # Extract category analyses
    if report_data.get("category_llm_analyses"):
        for category, analysis in report_data["category_llm_analyses"].items():
            examples.append({
                "instruction": f"Provide detailed analysis for the '{category}' category within {dimension}.",
                "input": create_category_context(report_data, category, rag_context),
                "output": analysis
            })

    # Extract process analyses
    if report_data.get("process_llm_analyses"):
        for process, analysis in report_data["process_llm_analyses"].items():
            examples.append({
                "instruction": f"Analyze the '{process}' process for {dimension}.",
                "input": create_process_context(report_data, process, rag_context),
                "output": analysis
            })

    # Extract lifecycle analyses
    if report_data.get("lifecycle_llm_analyses"):
        for lifecycle, analysis in report_data["lifecycle_llm_analyses"].items():
            examples.append({
                "instruction": f"Evaluate the '{lifecycle}' lifecycle stage for {dimension}.",
                "input": create_lifecycle_context(report_data, lifecycle, rag_context),
                "output": analysis
            })

    # Extract comment analysis
    if report_data.get("comment_insights", {}).get("llm_analysis"):
        examples.append({
            "instruction": f"Analyze survey comments for {dimension} and provide insights.",
            "input": create_comment_context(report_data, rag_context),
            "output": report_data["comment_insights"]["llm_analysis"]
        })

    return examples


def create_input_context(report_data: Dict, rag_context: str = None) -> str:
    """Create structured input context from report data including RAG knowledge"""
    metrics = report_data.get("overall_metrics", {})

    context = f"""Survey Metrics:
- Average Score: {metrics.get('avg_score', 'N/A')}/10
- Response Rate: {metrics.get('response_rate', 'N/A')}
- Total Responses: {metrics.get('total_responses', 'N/A')}
- Score Range: {metrics.get('min_score', 'N/A')} - {metrics.get('max_score', 'N/A')}

"""

    # Add category breakdown
    if report_data.get("category_analysis"):
        context += "Category Performance:\n"
        for cat_name, cat_data in report_data["category_analysis"].items():
            context += f"- {cat_name}: {cat_data.get('avg_score', 'N/A')}/10\n"
        context += "\n"

    # Add process breakdown
    if report_data.get("process_analysis"):
        context += "Process Performance:\n"
        for proc_name, proc_data in report_data["process_analysis"].items():
            context += f"- {proc_name}: {proc_data.get('avg_score', 'N/A')}/10\n"
        context += "\n"

    # Add lifecycle breakdown
    if report_data.get("lifecycle_analysis"):
        context += "Lifecycle Stage Performance:\n"
        for lc_name, lc_data in report_data["lifecycle_analysis"].items():
            context += f"- {lc_name}: {lc_data.get('avg_score', 'N/A')}/10\n"
        context += "\n"

    # Add RAG context (industry standards & best practices)
    if rag_context:
        context += f"{rag_context}\n"

    return context.strip()


def create_category_context(report_data: Dict, category: str, rag_context: str = None) -> str:
    """Create context for category-specific analysis"""
    cat_data = report_data.get("category_analysis", {}).get(category, {})

    context = f"""Category: {category}
Average Score: {cat_data.get('avg_score', 'N/A')}/10
Score Range: {cat_data.get('min_score', 'N/A')} - {cat_data.get('max_score', 'N/A')}
High Scores (8-10): {cat_data.get('score_distribution', {}).get('high', 'N/A')}%
Medium Scores (5-7): {cat_data.get('score_distribution', {}).get('medium', 'N/A')}%
Low Scores (1-4): {cat_data.get('score_distribution', {}).get('low', 'N/A')}%

"""

    # Add RAG context
    if rag_context:
        context += f"{rag_context}\n"

    return context.strip()


def create_process_context(report_data: Dict, process: str, rag_context: str = None) -> str:
    """Create context for process-specific analysis"""
    proc_data = report_data.get("process_analysis", {}).get(process, {})

    context = f"""Process: {process}
Average Score: {proc_data.get('avg_score', 'N/A')}/10
Score Range: {proc_data.get('min_score', 'N/A')} - {proc_data.get('max_score', 'N/A')}

"""

    # Add RAG context
    if rag_context:
        context += f"{rag_context}\n"

    return context.strip()


def create_lifecycle_context(report_data: Dict, lifecycle: str, rag_context: str = None) -> str:
    """Create context for lifecycle-specific analysis"""
    lc_data = report_data.get("lifecycle_analysis", {}).get(lifecycle, {})

    context = f"""Lifecycle Stage: {lifecycle}
Average Score: {lc_data.get('avg_score', 'N/A')}/10
Score Range: {lc_data.get('min_score', 'N/A')} - {lc_data.get('max_score', 'N/A')}

"""

    # Add RAG context
    if rag_context:
        context += f"{rag_context}\n"

    return context.strip()


def create_comment_context(report_data: Dict, rag_context: str = None) -> str:
    """Create context for comment analysis"""
    comment_insights = report_data.get("comment_insights", {})

    context = f"""Comment Statistics:
Total Comments: {comment_insights.get('total_comments', 'N/A')}
Average Sentiment: {comment_insights.get('avg_sentiment', 'N/A')}

Top Themes:
"""

    for theme in comment_insights.get("top_themes", [])[:5]:
        context += f"- {theme}\n"

    # Add RAG context
    if rag_context:
        context += f"\n{rag_context}\n"

    return context.strip()


def prepare_dimension_dataset(dimension_key: str, dimension_name: str):
    """Prepare training dataset for a specific dimension"""
    print(f"\n{'='*60}")
    print(f"Preparing dataset for: {dimension_name}")
    print(f"{'='*60}")

    training_examples = []
    reports_path = Path(REPORTS_BASE_PATH)

    # Find all report files for this dimension
    report_files = list(reports_path.glob(f"*/{dimension_key}_report_*.json"))

    print(f"Found {len(report_files)} report files")

    for report_file in report_files:
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                report_data = data.get("report_data", data)

                # Extract RAG context (industry standards & best practices)
                rag_context = data.get("rag_context")

                # Extract training examples with RAG context
                examples = extract_training_examples(report_data, dimension_name, rag_context)
                training_examples.extend(examples)

                rag_note = " (with RAG context)" if rag_context else ""
                print(f"✓ Processed {report_file.name}: {len(examples)} examples{rag_note}")
        except Exception as e:
            print(f"✗ Error processing {report_file.name}: {e}")

    # Save dataset
    if training_examples:
        output_dir = Path(__file__).parent.parent / "data" / dimension_key
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "training_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_examples, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved {len(training_examples)} training examples to {output_file}")

        # Create train/val split
        from sklearn.model_selection import train_test_split

        train_data, val_data = train_test_split(
            training_examples,
            test_size=0.1,
            random_state=42
        )

        # Save splits
        with open(output_dir / "train.json", 'w', encoding='utf-8') as f:
            json.dump(train_data, f, indent=2, ensure_ascii=False)

        with open(output_dir / "val.json", 'w', encoding='utf-8') as f:
            json.dump(val_data, f, indent=2, ensure_ascii=False)

        print(f"  - Training set: {len(train_data)} examples")
        print(f"  - Validation set: {len(val_data)} examples")

        return len(training_examples)
    else:
        print(f"✗ No training examples found for {dimension_name}")
        return 0


def main():
    """Prepare datasets for all dimensions"""
    print("="*80)
    print("PREPARING TRAINING DATA FROM REPORTS")
    print("="*80)
    print(f"Reports path: {REPORTS_BASE_PATH}")
    print(f"Output path: {Path(__file__).parent.parent / 'data'}")
    print()

    total_examples = 0
    successful_dims = []

    for dim_key, dim_name in DIMENSIONS.items():
        examples_count = prepare_dimension_dataset(dim_key, dim_name)
        total_examples += examples_count

        if examples_count > 0:
            successful_dims.append(dim_key)

    print(f"\n{'='*80}")
    print(f"DATA PREPARATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total dimensions processed: {len(successful_dims)}/{len(DIMENSIONS)}")
    print(f"Total training examples: {total_examples}")
    print(f"Successful dimensions: {', '.join(successful_dims)}")
    print()


if __name__ == "__main__":
    main()
