# Agentic Workflow Quick Start

## Overview

The EnTrust agentic workflow transforms survey analysis with 5 specialized agents:
1. **Survey Parser** → Statistics & Themes
2. **Maturity Assessor** → Standards-based Maturity Scores (uses RAG)
3. **Report Generator** → Comprehensive 50+ Page Reports
4. **Self-Critic** → Quality Scoring & Revision
5. **PDF Formatter** → Professional PDFs with Visuals

## Quick Start (Python API)

### Basic Usage

```python
from app.agents import AgenticReportService

# Generate agentic report
result = await AgenticReportService.generate_agentic_report(
    dimension="Data Privacy & Compliance",
    customer_code="ACME",
    customer_name="Acme Corporation",
    questions_data=survey_questions,  # List of question dicts
    llm_config=llm_config,  # From database
)

if result['success']:
    final_report = result['final_report']
    print(f"Quality Score: {result['execution_summary']['final_quality_score']}/10")
    print(f"Maturity: {final_report['metadata']['composite_maturity']}/5")
else:
    print(f"Error: {result['error']}")
```

### With PDF Generation

```python
result = await AgenticReportService.generate_agentic_report(
    dimension="Data Quality",
    customer_code="ACME",
    customer_name="Acme Corporation",
    questions_data=survey_questions,
    llm_config=llm_config,
    enable_pdf=True,
    pdf_output_path="/app/entrust/reports/ACME/quality_report.pdf"
)
```

### Custom Configuration

```python
result = await AgenticReportService.generate_agentic_report(
    dimension="Data Security & Access",
    customer_code="ACME",
    customer_name="Acme Corporation",
    questions_data=survey_questions,
    llm_config=llm_config,
    enable_pdf=True,
    pdf_output_path="/app/entrust/reports/ACME/security_report.pdf",
    enable_revision=True,       # Allow Self-Critic revisions
    max_revisions=2,            # Up to 2 revision attempts
    quality_threshold=8.5       # Higher quality threshold
)
```

## Expected Output

### Report Structure

The final report includes:
- **Executive Summary** (1-2 pages)
- **Current State Assessment** (metrics, score distribution)
- **Category/Process/Lifecycle Analysis** (tables with scores)
- **Maturity Assessment** (framework-specific scores, gaps)
- **Question-Level Analysis** (detailed table)
- **Prioritized Action Items** (RICE-scored initiatives)
- **Strategic Roadmap** (6-12 month phased plan)
- **Visuals Data** (graphs, word clouds)

### Maturity Assessment

Each dimension is assessed against 3-4 industry frameworks:
- **Data Privacy**: GDPR, CCPA, NIST Privacy, ISO 27701 → Composite Score (1-5)
- **Data Quality**: ISO 8000, TDQM, DAMA-DMBOK → Composite Score (1-5)
- **Governance**: DAMA-DMBOK, COBIT, Gartner EIM → Composite Score (1-5)
- **Security**: NIST 800-53, ISO 27001, CIS Controls → Composite Score (1-5)
- **Lineage**: DAMA-DMBOK, W3C PROV-DM → Composite Score (1-5)
- **Metadata**: Dublin Core, DAMA-DMBOK, ISO 11179 → Composite Score (1-5)
- **Value/Lifecycle**: DAMA-DMBOK, ILM → Composite Score (1-5)
- **Ethics/Bias**: IEEE Ethically Aligned Design → Composite Score (1-5)

### Quality Scoring

Self-Critic scores on 4 dimensions (1-10):
- **Clarity**: Structure, readability
- **Actionability**: Specific recommendations, ownership
- **Standards Alignment**: Framework references
- **Completeness**: Section depth, detail

**Threshold**: Average ≥ 8.0 → Approved, < 8.0 → Revision triggered

## Prerequisites

### 1. ChromaDB Knowledge Base

Initialize RAG store with standards:
```bash
cd backend
python -m app.rag  # First time
python -m app.rag --force  # Re-ingest if needed
```

### 2. LLM Configuration

Configure in EnTrust admin UI or database:
- **LOCAL**: LM Studio at `http://localhost:1234`
- **AWS Bedrock**: Claude Sonnet with thinking mode
- **Azure OpenAI**: GPT-5 with reasoning effort

### 3. Survey Data Format

Questions data must include:
```python
[
    {
        "question_id": 1,
        "text": "Are automated reconciliation checks...",
        "category": "Accuracy",
        "process": "Data Ingestion",
        "lifecycle_stage": "Creation",
        "avg_score": 6.5,
        "count": 10,
        "comments": ["Manual processes", "Need automation"]
    },
    ...
]
```

## Integration with Existing System

### Option 1: Drop-In Replacement

Convert agentic report to legacy format:
```python
from app.agents import AgenticReportService
from app.report_utils import save_reports

# Generate agentic report
workflow_result = await AgenticReportService.generate_agentic_report(...)

# Convert to legacy format
legacy_report = AgenticReportService.convert_to_legacy_format(
    workflow_result, questions_data
)

# Save using existing function
save_reports(
    customer_code=customer_code,
    customer_name=customer_name,
    dimension=dimension,
    report_data=legacy_report
)
```

### Option 2: New API Response Format

Use agentic-specific format:
```python
api_response = AgenticReportService.format_agentic_report_for_api(
    workflow_result
)
# Returns: {success, agentic_workflow, executive_summary, sections, action_items, ...}
```

## Performance

| Dimension | Questions | Execution Time |
|-----------|-----------|----------------|
| Data Privacy | 30 | ~2.5 minutes |
| Data Quality | 25 | ~2.0 minutes |
| Data Security | 35 | ~3.0 minutes |
| Overall (8 dimensions) | 200+ | ~20-25 minutes |

**Optimization**: Run dimensions in parallel:
```python
import asyncio

tasks = [
    AgenticReportService.generate_agentic_report(
        dimension=dim, customer_code="ACME", ...
    )
    for dim in ["Data Privacy", "Data Quality", "Data Security"]
]

results = await asyncio.gather(*tasks)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "RAG service not enabled" | Run `python -m app.rag` to initialize ChromaDB |
| "PDF generation skipped" | Install: `pip install weasyprint` |
| LLM timeout | Reduce question count, use faster model |
| Low quality score (< 8) | Check that `questions_data` has comments, increase RAG context |

## Next Steps

1. **Read full documentation**: `AGENTIC_WORKFLOW.md`
2. **Explore agent code**: `backend/app/agents/`
3. **Customize prompts**: `backend/app/agents/maturity_assessor.py`, `report_generator.py`
4. **Add knowledge**: `backend/Knowledge/` (add .txt files, re-run `python -m app.rag --force`)
5. **Integrate with UI**: Use `AgenticReportService.convert_to_legacy_format()`

## Example: Full Workflow

```python
from app.agents import AgenticReportService
from app.llm_providers import get_llm_provider
from app.database import SessionLocal
from app.models import LLMConfig

# 1. Get LLM config from database
db = SessionLocal()
llm_config = db.query(LLMConfig).filter(
    LLMConfig.purpose == "dimension_analysis"
).first()

# 2. Prepare survey data (from database)
questions_data = [
    {
        "question_id": q.question_id,
        "text": q.text,
        "category": q.category,
        "process": q.process,
        "lifecycle_stage": q.lifecycle_stage,
        "avg_score": 6.5,  # Computed from responses
        "count": 10,
        "comments": ["Sample comment 1", "Sample comment 2"]
    }
    for q in questions  # From database query
]

# 3. Generate agentic report
result = await AgenticReportService.generate_agentic_report(
    dimension="Data Privacy & Compliance",
    customer_code="ACME",
    customer_name="Acme Corporation",
    questions_data=questions_data,
    llm_config=llm_config,
    enable_pdf=True,
    pdf_output_path="/app/entrust/reports/ACME/privacy_report.pdf"
)

# 4. Process result
if result['success']:
    final_report = result['final_report']
    execution_summary = result['execution_summary']

    print(f"Report Generated Successfully!")
    print(f"- Executive Summary: {len(final_report['executive_summary'])} chars")
    print(f"- Sections: {len(final_report['sections'])}")
    print(f"- Action Items: {len(final_report['action_items'])}")
    print(f"- Quality Score: {execution_summary['final_quality_score']}/10")
    print(f"- Maturity: {final_report['metadata']['composite_maturity']}/5")
    print(f"- Execution Time: {execution_summary['total_time_seconds']:.1f}s")

    # Access maturity assessment
    workflow_results = result['workflow_results']
    maturity_assessor = workflow_results['maturity_assessor']
    maturity_assessment = maturity_assessor['output']

    print(f"\nMaturity by Framework:")
    for ml in maturity_assessment['maturity_levels']:
        print(f"  - {ml['framework']}: {ml['score']}/5 ({ml['current_level']})")

    # Access action items
    print(f"\nTop 3 Action Items:")
    for i, item in enumerate(final_report['action_items'][:3], 1):
        print(f"  {i}. [{item['priority']}] {item['action']}")
        print(f"     Owner: {item['owner']}, Timeline: {item['timeline']}")
else:
    print(f"Error: {result['error']}")

db.close()
```

## Support

For issues, questions, or feature requests, refer to the main documentation (`AGENTIC_WORKFLOW.md`) or contact the EnTrust development team.
