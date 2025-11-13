"""
PDF Conversion Tools
Converts markdown reports to professional PDF documents
"""

import os
from typing import Dict, Optional


def convert_markdown_to_pdf(
    markdown: str,
    title: str,
    metadata: Dict,
    output_path: Optional[str] = None
) -> bytes:
    """
    Convert markdown report to styled PDF

    Args:
        markdown: Markdown content
        title: Report title
        metadata: Report metadata (customer, dimension, date)
        output_path: Optional path to save PDF file

    Returns:
        PDF binary data

    Example:
        >>> pdf_bytes = convert_markdown_to_pdf(
        ...     markdown="# Report\n\nContent here...",
        ...     title="Data Privacy Report",
        ...     metadata={"customer": "Acme", "date": "2025-11-13"}
        ... )
    """
    try:
        from weasyprint import HTML, CSS
        from markdown import markdown as md_to_html

        # Convert markdown to HTML
        html_content = md_to_html(
            markdown,
            extensions=['extra', 'codehilite', 'tables', 'toc']
        )

        # Build complete HTML with styling
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                @page {{
                    size: A4;
                    margin: 2.5cm;
                    @top-left {{
                        content: "{metadata.get('customer_name', '')} - {metadata.get('dimension', '')}";
                        font-size: 9pt;
                        color: #666;
                    }}
                    @bottom-center {{
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 9pt;
                        color: #666;
                    }}
                    @bottom-right {{
                        content: "{metadata.get('date', '')}";
                        font-size: 9pt;
                        color: #666;
                    }}
                }}
                body {{
                    font-family: 'Helvetica', 'Arial', sans-serif;
                    font-size: 11pt;
                    line-height: 1.6;
                    color: #333;
                }}
                h1 {{
                    color: #003366;
                    font-size: 24pt;
                    margin-top: 0;
                    border-bottom: 2px solid #0066CC;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #0066CC;
                    font-size: 18pt;
                    margin-top: 30px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 5px;
                }}
                h3 {{
                    color: #0066CC;
                    font-size: 14pt;
                    margin-top: 20px;
                }}
                h4 {{
                    color: #333;
                    font-size: 12pt;
                    margin-top: 15px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background-color: #0066CC;
                    color: white;
                    padding: 10px;
                    text-align: left;
                    font-weight: bold;
                }}
                td {{
                    padding: 8px;
                    border: 1px solid #ddd;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                code {{
                    background-color: #f5f5f5;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }}
                pre {{
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                blockquote {{
                    border-left: 4px solid #0066CC;
                    padding-left: 15px;
                    margin-left: 0;
                    color: #666;
                    font-style: italic;
                }}
                ul, ol {{
                    margin: 10px 0;
                    padding-left: 30px;
                }}
                li {{
                    margin: 5px 0;
                }}
                .page-break {{
                    page-break-before: always;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
            </style>
        </head>
        <body>
            <div class="cover-page">
                <h1>{title}</h1>
                <p style="font-size: 16pt; color: #666;">
                    {metadata.get('customer_name', '')}
                </p>
                <p style="font-size: 12pt; color: #999;">
                    Generated: {metadata.get('date', '')}
                </p>
            </div>
            <div class="page-break"></div>
            {html_content}
        </body>
        </html>
        """

        # Convert HTML to PDF
        html_obj = HTML(string=full_html)
        pdf_bytes = html_obj.write_pdf()

        # Optionally save to file
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return pdf_bytes

    except ImportError as e:
        raise ImportError(f"PDF conversion requires weasyprint and markdown: {e}")
    except Exception as e:
        raise Exception(f"Error converting markdown to PDF: {e}")


# Tool definition for Azure AI Foundry
TOOL_DEFINITIONS = {
    "convert_markdown_to_pdf": {
        "function": convert_markdown_to_pdf,
        "description": "Convert markdown report to professional PDF",
        "parameters": {
            "type": "object",
            "properties": {
                "markdown": {
                    "type": "string",
                    "description": "Markdown content"
                },
                "title": {
                    "type": "string",
                    "description": "Report title"
                },
                "metadata": {
                    "type": "object",
                    "description": "Report metadata (customer, dimension, date)"
                },
                "output_path": {
                    "type": "string",
                    "description": "Optional file path to save PDF"
                }
            },
            "required": ["markdown", "title", "metadata"]
        }
    }
}


if __name__ == "__main__":
    # Test PDF conversion
    print("Testing PDF Conversion...")
    test_markdown = """
# Sample Report

## Executive Summary

This is a test report.

### Key Findings
- Finding 1
- Finding 2

| Dimension | Score |
|-----------|-------|
| Privacy   | 7.5   |
| Security  | 8.1   |
"""

    try:
        pdf = convert_markdown_to_pdf(
            markdown=test_markdown,
            title="Test Report",
            metadata={
                "customer_name": "Test Corp",
                "dimension": "Test Dimension",
                "date": "2025-11-13"
            }
        )
        print(f"PDF Generated: {len(pdf)} bytes")
    except Exception as e:
        print(f"Error: {e}")
