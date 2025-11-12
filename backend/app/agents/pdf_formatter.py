"""
PDF Formatter Agent

Converts Markdown/JSON reports to professional PDFs with graphs, word clouds,
and consistent branding.
"""

import os
import time
from typing import Dict, Any, Optional
from pathlib import Path
from .base import AgentBase, AgentResult, PDFOutput
import logging

logger = logging.getLogger(__name__)


class PDFFormatterAgent(AgentBase):
    """
    Formats reports as professional PDFs

    Capabilities:
    - Convert Markdown to PDF
    - Embed graphs (category scores, maturity levels)
    - Embed word clouds from comment themes
    - Apply professional styling (headers, fonts, branding)
    - Support WeasyPrint or Pandoc for conversion

    Note: PDF generation is optional and may require additional dependencies.
    The agent will gracefully handle cases where PDF tools are unavailable.
    """

    def __init__(self, llm_provider=None):
        super().__init__("PDFFormatterAgent", llm_provider)
        self._check_pdf_tools()

    def _check_pdf_tools(self):
        """Check if PDF generation tools are available"""
        self.weasyprint_available = False
        self.pandoc_available = False

        try:
            import weasyprint
            self.weasyprint_available = True
            logger.info("WeasyPrint available for PDF generation")
        except ImportError:
            logger.warning("WeasyPrint not available. Install with: pip install weasyprint")

        try:
            import subprocess
            result = subprocess.run(['pandoc', '--version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                self.pandoc_available = True
                logger.info("Pandoc available for PDF generation")
        except:
            logger.warning("Pandoc not available")

    async def execute(
        self,
        dimension: str,
        markdown_content: str,
        report_data: Dict[str, Any],
        output_path: str,
        customer_name: str = "Organization"
    ) -> AgentResult:
        """
        Convert report to PDF

        Args:
            dimension: Dimension name
            markdown_content: Markdown content to convert
            report_data: Full report data (for visuals)
            output_path: Path to save PDF
            customer_name: Customer organization name

        Returns:
            AgentResult with PDF output info
        """
        start_time = time.time()
        self.log_execution("START", f"Formatting PDF for {dimension}")

        try:
            # Check if PDF tools available
            if not self.weasyprint_available and not self.pandoc_available:
                self.log_execution("SKIP", "No PDF tools available, skipping PDF generation")
                return AgentResult(
                    success=True,
                    agent_name=self.agent_name,
                    output=PDFOutput(
                        pdf_path="",
                        status="skipped",
                        error_details="PDF generation tools not available"
                    ).model_dump(),
                    execution_time_seconds=time.time() - start_time
                )

            # Step 1: Prepare HTML from Markdown (if using WeasyPrint)
            self.log_execution("STEP_1", "Converting Markdown to HTML")
            html_content = await self._markdown_to_html(
                dimension, markdown_content, report_data, customer_name
            )

            # Step 2: Generate graphs (if visual data available)
            self.log_execution("STEP_2", "Generating visualizations")
            graph_paths = await self._generate_graphs(
                report_data.get('visuals', {}),
                os.path.dirname(output_path)
            )

            # Step 3: Convert to PDF
            self.log_execution("STEP_3", "Converting to PDF")
            pdf_path = await self._generate_pdf(
                html_content, output_path, graph_paths
            )

            # Step 4: Get PDF stats
            pdf_stats = self._get_pdf_stats(pdf_path)

            execution_time = time.time() - start_time
            self.log_execution("COMPLETE", f"PDF generated in {execution_time:.2f}s")

            return AgentResult(
                success=True,
                agent_name=self.agent_name,
                output=PDFOutput(
                    pdf_path=pdf_path,
                    status="success",
                    **pdf_stats
                ).model_dump(),
                execution_time_seconds=execution_time
            )

        except Exception as e:
            self.logger.error(f"Error in PDFFormatterAgent: {e}", exc_info=True)
            return AgentResult(
                success=False,
                agent_name=self.agent_name,
                output=PDFOutput(
                    pdf_path="",
                    status="error",
                    error_details=str(e)
                ).model_dump(),
                error=str(e),
                execution_time_seconds=time.time() - start_time
            )

    async def _markdown_to_html(
        self,
        dimension: str,
        markdown_content: str,
        report_data: Dict,
        customer_name: str
    ) -> str:
        """Convert Markdown to HTML with styling"""
        try:
            import markdown
        except ImportError:
            logger.warning("Markdown library not available, using plain conversion")
            # Fallback: Simple HTML wrapper
            return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{dimension} Report - {customer_name}</title>
    <style>{self._get_pdf_css()}</style>
</head>
<body>
    <pre>{markdown_content}</pre>
</body>
</html>"""

        # Convert Markdown to HTML
        html_body = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'codehilite']
        )

        # Wrap in HTML document with styling
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{dimension} Report - {customer_name}</title>
    <style>{self._get_pdf_css()}</style>
</head>
<body>
    <div class="header">
        <h1>EnTrust Data Governance Report</h1>
        <h2>{dimension}</h2>
        <p><strong>{customer_name}</strong></p>
    </div>
    <div class="content">
        {html_body}
    </div>
    <div class="footer">
        <p>Generated by EnTrust Survey Analysis Platform</p>
    </div>
</body>
</html>"""
        return html

    def _get_pdf_css(self) -> str:
        """Get CSS styling for PDF"""
        return """
        @page {
            size: letter;
            margin: 1in;
            @top-center {
                content: "EnTrust Report";
                font-size: 10pt;
                color: #666;
            }
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
            }
        }

        body {
            font-family: 'Calibri', 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }

        .header {
            text-align: center;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 20px;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 24pt;
            color: #0066cc;
            margin-bottom: 10px;
        }

        .header h2 {
            font-size: 18pt;
            color: #333;
            margin-bottom: 10px;
        }

        h1 {
            font-size: 20pt;
            color: #0066cc;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 5px;
            margin-top: 30px;
        }

        h2 {
            font-size: 16pt;
            color: #0066cc;
            margin-top: 25px;
        }

        h3 {
            font-size: 14pt;
            color: #333;
            margin-top: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 10pt;
        }

        table thead {
            background-color: #0066cc;
            color: white;
        }

        table th, table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }

        table tbody tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        .footer {
            text-align: center;
            font-size: 9pt;
            color: #666;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }

        code {
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }

        pre {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            border-left: 3px solid #0066cc;
            overflow-x: auto;
        }
        """

    async def _generate_graphs(
        self,
        visuals: Dict[str, Any],
        output_dir: str
    ) -> Dict[str, str]:
        """Generate graph images from visual data"""
        graph_paths = {}

        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            import numpy as np

            # Category scores bar chart
            if 'category_scores' in visuals and visuals['category_scores']:
                fig, ax = plt.subplots(figsize=(10, 6))
                categories = list(visuals['category_scores'].keys())
                scores = list(visuals['category_scores'].values())

                ax.barh(categories, scores, color='#0066cc')
                ax.set_xlabel('Average Score')
                ax.set_title('Scores by Category')
                ax.set_xlim(0, 10)

                graph_path = os.path.join(output_dir, 'category_scores.png')
                plt.tight_layout()
                plt.savefig(graph_path, dpi=150, bbox_inches='tight')
                plt.close()
                graph_paths['category_scores'] = graph_path

            # Maturity by framework
            if 'maturity_by_framework' in visuals and visuals['maturity_by_framework']:
                fig, ax = plt.subplots(figsize=(10, 6))
                frameworks = list(visuals['maturity_by_framework'].keys())
                maturity_scores = list(visuals['maturity_by_framework'].values())

                ax.barh(frameworks, maturity_scores, color='#009900')
                ax.set_xlabel('Maturity Score')
                ax.set_title('Maturity by Framework')
                ax.set_xlim(0, 5)

                graph_path = os.path.join(output_dir, 'maturity_framework.png')
                plt.tight_layout()
                plt.savefig(graph_path, dpi=150, bbox_inches='tight')
                plt.close()
                graph_paths['maturity_framework'] = graph_path

        except ImportError:
            logger.warning("Matplotlib not available, skipping graph generation")
        except Exception as e:
            logger.error(f"Error generating graphs: {e}")

        return graph_paths

    async def _generate_pdf(
        self,
        html_content: str,
        output_path: str,
        graph_paths: Dict[str, str]
    ) -> str:
        """Generate PDF from HTML"""
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if self.weasyprint_available:
            return await self._weasyprint_generate(html_content, output_path)
        elif self.pandoc_available:
            return await self._pandoc_generate(html_content, output_path)
        else:
            raise RuntimeError("No PDF generation tool available")

    async def _weasyprint_generate(self, html_content: str, output_path: str) -> str:
        """Generate PDF using WeasyPrint"""
        try:
            from weasyprint import HTML, CSS
            HTML(string=html_content).write_pdf(output_path)
            return output_path
        except Exception as e:
            logger.error(f"WeasyPrint PDF generation failed: {e}")
            raise

    async def _pandoc_generate(self, html_content: str, output_path: str) -> str:
        """Generate PDF using Pandoc"""
        import subprocess
        import tempfile

        try:
            # Write HTML to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                html_path = f.name

            # Call pandoc
            subprocess.run([
                'pandoc',
                html_path,
                '-o', output_path,
                '--pdf-engine=wkhtmltopdf'
            ], check=True, timeout=60)

            # Clean up temp file
            os.unlink(html_path)

            return output_path
        except Exception as e:
            logger.error(f"Pandoc PDF generation failed: {e}")
            raise

    def _get_pdf_stats(self, pdf_path: str) -> Dict[str, Any]:
        """Get PDF file statistics"""
        if not os.path.exists(pdf_path):
            return {"page_count": None, "file_size_mb": None}

        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)

        # Try to get page count (requires PyPDF2 or similar)
        page_count = None
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                page_count = len(reader.pages)
        except:
            pass

        return {
            "page_count": page_count,
            "file_size_mb": round(file_size_mb, 2)
        }
