"""
Graph Generation Tools
Creates visualizations (charts, graphs, word clouds) for reports
"""

import base64
import io
from typing import Dict, List
import json


def generate_score_distribution_chart(scores: List[float], title: str = "Score Distribution") -> str:
    """
    Generate histogram of score distribution

    Args:
        scores: List of scores (0-10)
        title: Chart title

    Returns:
        Base64-encoded PNG image data URL

    Example:
        >>> chart = generate_score_distribution_chart([7.5, 6.2, 8.9, 5.1])
        >>> # Returns: "data:image/png;base64,iVBORw0KGgoAAAANS..."
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend

        fig, ax = plt.subplots(figsize=(10, 6))

        # Create histogram
        ax.hist(scores, bins=10, range=(0, 10), edgecolor='black', color='#0066CC')
        ax.set_xlabel('Score', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        # Save to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    except ImportError:
        return "![Chart](Chart generation requires matplotlib)"
    except Exception as e:
        return f"![Chart](Error generating chart: {str(e)})"


def generate_dimension_comparison_radar(dimension_scores: Dict[str, float], title: str = "Dimension Comparison") -> str:
    """
    Generate radar chart comparing dimensions

    Args:
        dimension_scores: Dictionary mapping dimension names to scores
        title: Chart title

    Returns:
        Base64-encoded PNG image data URL

    Example:
        >>> scores = {
        ...     "Privacy": 7.5,
        ...     "Quality": 6.2,
        ...     "Security": 8.1
        ... }
        >>> chart = generate_dimension_comparison_radar(scores)
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        import numpy as np
        matplotlib.use('Agg')

        dimensions = list(dimension_scores.keys())
        scores = list(dimension_scores.values())

        # Number of dimensions
        num_vars = len(dimensions)

        # Compute angle for each axis
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        scores += scores[:1]  # Complete the circle
        angles += angles[:1]

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        ax.plot(angles, scores, 'o-', linewidth=2, color='#0066CC')
        ax.fill(angles, scores, alpha=0.25, color='#0066CC')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dimensions, fontsize=10)
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=8)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.grid(True)

        # Save to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    except ImportError:
        return "![Radar Chart](Chart generation requires matplotlib and numpy)"
    except Exception as e:
        return f"![Radar Chart](Error generating chart: {str(e)})"


def generate_word_cloud(comments: List[str], title: str = "Comment Word Cloud") -> str:
    """
    Generate word cloud from comments

    Args:
        comments: List of comment strings
        title: Chart title

    Returns:
        Base64-encoded PNG image data URL

    Example:
        >>> comments = ["Good privacy policies", "Need better security"]
        >>> cloud = generate_word_cloud(comments)
    """
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')

        if not comments:
            return "![Word Cloud](No comments available)"

        # Combine all comments
        text = " ".join(comments)

        # Generate word cloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='Blues',
            max_words=100,
            relative_scaling=0.5,
            min_font_size=10
        ).generate(text)

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)

        # Save to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    except ImportError:
        return "![Word Cloud](Word cloud generation requires wordcloud package)"
    except Exception as e:
        return f"![Word Cloud](Error generating word cloud: {str(e)})"


def generate_category_heatmap(category_scores: Dict[str, Dict[str, float]], title: str = "Category Heatmap") -> str:
    """
    Generate heatmap of scores by category and process

    Args:
        category_scores: Nested dict {category: {process: score}}
        title: Chart title

    Returns:
        Base64-encoded PNG image data URL

    Example:
        >>> scores = {
        ...     "Policy": {"Planning": 7.5, "Implementation": 6.2},
        ...     "Technical": {"Planning": 8.0, "Implementation": 7.1}
        ... }
        >>> heatmap = generate_category_heatmap(scores)
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        import numpy as np
        matplotlib.use('Agg')

        # Extract categories and processes
        categories = list(category_scores.keys())
        processes = list(set(proc for cat in category_scores.values() for proc in cat.keys()))
        processes.sort()

        # Build matrix
        matrix = []
        for category in categories:
            row = []
            for process in processes:
                score = category_scores.get(category, {}).get(process, 0)
                row.append(score)
            matrix.append(row)

        matrix = np.array(matrix)

        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, 8))
        im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=10)

        # Set ticks and labels
        ax.set_xticks(np.arange(len(processes)))
        ax.set_yticks(np.arange(len(categories)))
        ax.set_xticklabels(processes, rotation=45, ha='right', fontsize=9)
        ax.set_yticklabels(categories, fontsize=9)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Score', rotation=270, labelpad=20, fontsize=10)

        # Add text annotations
        for i in range(len(categories)):
            for j in range(len(processes)):
                text = ax.text(j, i, f'{matrix[i, j]:.1f}',
                             ha="center", va="center", color="black", fontsize=8)

        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)
        plt.tight_layout()

        # Save to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    except ImportError:
        return "![Heatmap](Heatmap generation requires matplotlib and numpy)"
    except Exception as e:
        return f"![Heatmap](Error generating heatmap: {str(e)})"


def generate_maturity_heatmap(dimension_maturity: Dict[str, int], title: str = "Maturity Level Heatmap") -> str:
    """
    Generate heatmap showing maturity levels across dimensions

    Args:
        dimension_maturity: Dictionary mapping dimensions to maturity levels (1-5)
        title: Chart title

    Returns:
        Base64-encoded PNG image data URL
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        import numpy as np
        matplotlib.use('Agg')

        dimensions = list(dimension_maturity.keys())
        maturity_levels = list(dimension_maturity.values())

        # Create horizontal bar chart with color coding
        fig, ax = plt.subplots(figsize=(10, 8))

        colors = ['#d32f2f', '#f57c00', '#fbc02d', '#7cb342', '#388e3c']  # Red to Green
        bar_colors = [colors[int(level) - 1] for level in maturity_levels]

        y_pos = np.arange(len(dimensions))
        ax.barh(y_pos, maturity_levels, color=bar_colors, edgecolor='black')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(dimensions, fontsize=10)
        ax.set_xlabel('Maturity Level', fontsize=12)
        ax.set_xlim(0, 5.5)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xticklabels(['1\nInitial', '2\nDeveloping', '3\nDefined', '4\nManaged', '5\nOptimizing'], fontsize=9)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()

        # Save to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    except ImportError:
        return "![Maturity Heatmap](Chart generation requires matplotlib and numpy)"
    except Exception as e:
        return f"![Maturity Heatmap](Error generating chart: {str(e)})"


# Tool definitions for Azure AI Foundry
TOOL_DEFINITIONS = {
    "generate_score_distribution_chart": {
        "function": generate_score_distribution_chart,
        "description": "Generate histogram of score distribution",
        "parameters": {
            "type": "object",
            "properties": {
                "scores": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of scores"
                },
                "title": {
                    "type": "string",
                    "description": "Chart title",
                    "default": "Score Distribution"
                }
            },
            "required": ["scores"]
        }
    },
    "generate_dimension_comparison_radar": {
        "function": generate_dimension_comparison_radar,
        "description": "Generate radar chart comparing dimensions",
        "parameters": {
            "type": "object",
            "properties": {
                "dimension_scores": {
                    "type": "object",
                    "description": "Dictionary mapping dimension names to scores"
                },
                "title": {
                    "type": "string",
                    "description": "Chart title",
                    "default": "Dimension Comparison"
                }
            },
            "required": ["dimension_scores"]
        }
    },
    "generate_word_cloud": {
        "function": generate_word_cloud,
        "description": "Generate word cloud from comments",
        "parameters": {
            "type": "object",
            "properties": {
                "comments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of comment strings"
                },
                "title": {
                    "type": "string",
                    "description": "Chart title",
                    "default": "Comment Word Cloud"
                }
            },
            "required": ["comments"]
        }
    },
    "generate_category_heatmap": {
        "function": generate_category_heatmap,
        "description": "Generate heatmap of category scores",
        "parameters": {
            "type": "object",
            "properties": {
                "category_scores": {
                    "type": "object",
                    "description": "Nested dict {category: {process: score}}"
                },
                "title": {
                    "type": "string",
                    "description": "Chart title",
                    "default": "Category Heatmap"
                }
            },
            "required": ["category_scores"]
        }
    }
}


if __name__ == "__main__":
    # Test the graph tools
    print("Testing Graph Tools...")
    print("=" * 60)

    # Test score distribution
    scores = [7.5, 6.2, 8.9, 5.1, 7.8, 6.5, 8.2, 7.1, 6.8, 7.9]
    chart = generate_score_distribution_chart(scores)
    print(f"Score Distribution Chart: {'Generated' if chart.startswith('data:image') else 'Failed'}")

    # Test radar chart
    dimension_scores = {
        "Privacy": 7.5,
        "Quality": 6.2,
        "Security": 8.1,
        "Governance": 7.0,
        "Lineage": 6.5
    }
    radar = generate_dimension_comparison_radar(dimension_scores)
    print(f"Radar Chart: {'Generated' if radar.startswith('data:image') else 'Failed'}")

    # Test word cloud
    comments = ["Good policies", "Need improvement", "Better security needed"]
    cloud = generate_word_cloud(comments)
    print(f"Word Cloud: {'Generated' if cloud.startswith('data:image') else 'Failed'}")
