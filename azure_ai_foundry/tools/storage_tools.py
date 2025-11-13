"""
Storage Tools
Saves reports to disk (filesystem, could be extended to cloud storage)
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


def save_reports_to_disk(
    customer_code: str,
    dimension: str,
    markdown_report: str,
    pdf_report: Optional[bytes] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Save reports to local filesystem

    Args:
        customer_code: Customer identifier
        dimension: Dimension name
        markdown_report: Markdown report content
        pdf_report: Optional PDF report bytes
        metadata: Optional report metadata

    Returns:
        Dictionary with file paths and status

    Example:
        >>> result = save_reports_to_disk(
        ...     customer_code="ACME001",
        ...     dimension="Data Privacy & Compliance",
        ...     markdown_report="# Report...",
        ...     pdf_report=pdf_bytes,
        ...     metadata={"maturity_level": 3}
        ... )
    """
    try:
        # Determine base reports directory
        # Use backend/reports or create azure_ai_foundry/reports
        base_dir = Path(__file__).parent.parent.parent / "backend" / "reports"
        if not base_dir.exists():
            base_dir = Path(__file__).parent.parent / "reports"
            base_dir.mkdir(parents=True, exist_ok=True)

        # Create customer directory
        customer_dir = base_dir / customer_code
        customer_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize dimension name for filename
        safe_dimension = dimension.replace(" ", "_").replace("&", "and")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save markdown
        markdown_path = customer_dir / f"{safe_dimension}.md"
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)

        # Save PDF if provided
        pdf_path = None
        if pdf_report:
            pdf_path = customer_dir / f"{safe_dimension}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(pdf_report)

        # Save JSON metadata
        json_path = customer_dir / f"{safe_dimension}.json"
        report_json = {
            "dimension": dimension,
            "customer_code": customer_code,
            "generated_at": datetime.now().isoformat(),
            "markdown_path": str(markdown_path),
            "pdf_path": str(pdf_path) if pdf_path else None,
            "metadata": metadata or {}
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_json, f, indent=2)

        return {
            "success": True,
            "markdown_path": str(markdown_path),
            "pdf_path": str(pdf_path) if pdf_path else None,
            "json_path": str(json_path),
            "customer_dir": str(customer_dir)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def load_report_from_disk(customer_code: str, dimension: str) -> Optional[Dict]:
    """
    Load existing report from disk

    Args:
        customer_code: Customer identifier
        dimension: Dimension name

    Returns:
        Report data dictionary or None if not found
    """
    try:
        base_dir = Path(__file__).parent.parent.parent / "backend" / "reports"
        if not base_dir.exists():
            base_dir = Path(__file__).parent.parent / "reports"

        customer_dir = base_dir / customer_code
        if not customer_dir.exists():
            return None

        safe_dimension = dimension.replace(" ", "_").replace("&", "and")
        json_path = customer_dir / f"{safe_dimension}.json"

        if not json_path.exists():
            return None

        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    except Exception as e:
        print(f"Error loading report: {e}")
        return None


def list_customer_reports(customer_code: str) -> list:
    """
    List all reports for a customer

    Args:
        customer_code: Customer identifier

    Returns:
        List of report metadata dictionaries
    """
    try:
        base_dir = Path(__file__).parent.parent.parent / "backend" / "reports"
        if not base_dir.exists():
            base_dir = Path(__file__).parent.parent / "reports"

        customer_dir = base_dir / customer_code
        if not customer_dir.exists():
            return []

        reports = []
        for json_file in customer_dir.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                reports.append(json.load(f))

        return reports

    except Exception as e:
        print(f"Error listing reports: {e}")
        return []


# Tool definitions for Azure AI Foundry
TOOL_DEFINITIONS = {
    "save_reports_to_disk": {
        "function": save_reports_to_disk,
        "description": "Save reports to filesystem",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_code": {
                    "type": "string",
                    "description": "Customer identifier"
                },
                "dimension": {
                    "type": "string",
                    "description": "Dimension name"
                },
                "markdown_report": {
                    "type": "string",
                    "description": "Markdown report content"
                },
                "pdf_report": {
                    "type": "string",
                    "description": "Base64-encoded PDF bytes",
                    "format": "byte"
                },
                "metadata": {
                    "type": "object",
                    "description": "Report metadata"
                }
            },
            "required": ["customer_code", "dimension", "markdown_report"]
        }
    }
}


if __name__ == "__main__":
    # Test storage tools
    print("Testing Storage Tools...")

    result = save_reports_to_disk(
        customer_code="TEST001",
        dimension="Test Dimension",
        markdown_report="# Test Report\n\nThis is a test.",
        metadata={"maturity_level": 3}
    )

    print(f"Save Result: {result}")

    if result["success"]:
        # Test load
        loaded = load_report_from_disk("TEST001", "Test Dimension")
        print(f"Loaded Report: {loaded}")

        # Test list
        reports = list_customer_reports("TEST001")
        print(f"Customer Reports: {len(reports)}")
