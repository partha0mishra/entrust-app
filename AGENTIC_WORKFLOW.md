# Agentic Workflow for EnTrust Survey Analysis

## Overview

The EnTrust platform has been enhanced with an **agentic workflow** system that transforms survey analysis into a sophisticated, multi-agent pipeline. This enhancement brings standards-based maturity analysis, iterative quality refinement, and professional PDF generation to the existing robust survey platform.

## Architecture

### Agent-Based Design

The agentic workflow consists of 5 specialized agents, each with a single responsibility:

```
Survey Data
    ↓
[1. Survey Parser Agent]
    → Statistics & Themes
    ↓
[2. Maturity Assessor Agent] ← ChromaDB RAG (Standards & Best Practices)
    → Maturity Scores & Gaps
    ↓
[3. Report Generator Agent]
    → Comprehensive 50+ Page Report
    ↓
[4. Self-Critic Agent]
    → Quality Scores (1-10)
    ↓ (if score < 8)
[Revision Loop] (optional, max 1 iteration)
    ↓
[5. PDF Formatter Agent] (optional)
    → Professional PDF with Visuals
    ↓
Final Report
```

### Agent Descriptions

#### 1. **Survey Parser Agent**
- **Purpose**: Analyze JSON survey data and compute comprehensive statistics
- **Capabilities**:
  - Overall metrics (avg score, response rate, distribution)
  - Statistics by category, process, and lifecycle stage
  - Comment theme extraction (LLM-based or keyword fallback)
  - Score distribution analysis
- **Output**: Structured `SurveyStats` JSON

#### 2. **Maturity Assessor Agent**
- **Purpose**: Evaluate organizational maturity against industry standards
- **Capabilities**:
  - Query ChromaDB for relevant standards (GDPR, DAMA-DMBOK, NIST, ISO, etc.)
  - Assess maturity on 1-5 scale per framework
  - Identify maturity gaps with survey evidence
  - Map to framework-specific best practices
- **Standards Used** (dimension-specific):
  - **Privacy**: GDPR, CCPA, NIST Privacy Framework, ISO 27701
  - **Quality**: ISO 8000, TDQM, DAMA-DMBOK, Six Sigma
  - **Governance**: DAMA-DMBOK, COBIT, Gartner EIM, CMMI DMM
  - **Security**: NIST 800-53, ISO 27001, CIS Controls
  - **Lineage**: DAMA-DMBOK, W3C PROV-DM, Provenance Standards
  - **Metadata**: Dublin Core, DAMA-DMBOK, ISO 11179
  - **Value/Lifecycle**: DAMA-DMBOK, ILM, ROI Frameworks
  - **Ethics**: IEEE Ethically Aligned Design, AI Ethics Guidelines
- **Output**: Structured `MaturityAssessment` JSON with composite score, framework-specific levels, and prioritized gaps

#### 3. **Report Generator Agent**
- **Purpose**: Craft professional, consultative 50+ page reports
- **Capabilities**:
  - Executive summary (1-2 pages, high-impact)
  - Detailed sections (current state, category/process/lifecycle analysis, maturity assessment, question-level details)
  - Prioritized action items with RICE scoring
  - 6-12 month strategic roadmap (3 phases)
  - Visual data preparation (graphs, word clouds)
- **Output**: Structured `GeneratedReport` JSON with Markdown content

#### 4. **Self-Critic Agent**
- **Purpose**: Quality assurance and iterative refinement
- **Capabilities**:
  - Score report on 4 dimensions (1-10 scale):
    - **Clarity**: Structure, readability, organization
    - **Actionability**: Specific recommendations, clear ownership/timelines
    - **Standards Alignment**: Framework references, best practice grounding
    - **Completeness**: Section depth, detail coverage
  - Generate revision notes if average score < threshold (default: 8.0)
  - Trigger revision loop (optional, max 1 iteration by default)
- **Output**: Structured `CritiqueScores` JSON

#### 5. **PDF Formatter Agent**
- **Purpose**: Convert reports to professional PDFs
- **Capabilities**:
  - Markdown to HTML conversion
  - Professional styling (headers, fonts, branding)
  - Graph generation (category scores, maturity levels)
  - Word cloud creation (comment themes)
  - WeasyPrint or Pandoc support
- **Note**: PDF generation is optional and gracefully degrades if tools unavailable
- **Output**: Structured `PDFOutput` JSON with file path and stats

### Orchestrator

The **AgenticWorkflowOrchestrator** coordinates all agents:
- Sequential execution with data flow
- Error handling and recovery
- Revision loop management
- Execution logging and timing
- Final result aggregation

## Integration with Existing System

### Preserved Functionality
- **Existing endpoints**: All current report generation endpoints remain unchanged
- **UI compatibility**: Reports maintain the expected JSON/Markdown structure
- **Storage**: Reports are still saved to `/app/entrust/reports` (Markdown) and `/app/entrust/report_json` (JSON)
- **LLM providers**: Supports LOCAL (LM Studio), AWS Bedrock, Azure OpenAI
- **ChromaDB RAG**: Leverages existing standards knowledge base

### New Capabilities
- **Standards-based maturity analysis**: Each dimension assessed against 3-4 industry frameworks
- **Quality scoring**: Reports scored on clarity, actionability, standards alignment, completeness
- **Iterative refinement**: Self-Critic can trigger revisions (if score < 8)
- **Professional PDFs**: Optional PDF generation with graphs and word clouds
- **Comprehensive action items**: RICE-scored, prioritized initiatives
- **Strategic roadmaps**: 6-12 month phased plans

## Usage

### Option 1: Programmatic API (Python)

```python
from app.agents import AgenticReportService

# Generate agentic report
result = await AgenticReportService.generate_agentic_report(
    dimension="Data Privacy & Compliance",
    customer_code="ACME",
    customer_name="Acme Corporation",
    questions_data=survey_questions,  # List of question dicts
    llm_config=llm_config,  # From database
    enable_pdf=True,
    pdf_output_path="/app/entrust/reports/ACME/privacy_report.pdf",
    enable_revision=True,
    max_revisions=1,
    quality_threshold=8.0
)

if result['success']:
    final_report = result['final_report']
    quality_score = result['execution_summary']['final_quality_score']
    print(f"Report generated with quality score: {quality_score}/10")
else:
    print(f"Error: {result['error']}")
```

### Option 2: Direct Orchestrator Usage

```python
from app.agents import AgenticWorkflowOrchestrator
from app.llm_providers import get_llm_provider
from app.rag import get_rag_service

# Initialize
llm_provider = get_llm_provider(llm_config)
rag_service = get_rag_service()

orchestrator = AgenticWorkflowOrchestrator(
    llm_provider=llm_provider,
    rag_service=rag_service,
    enable_pdf=True,
    enable_revision=True,
    max_revisions=1,
    quality_threshold=8.0
)

# Execute workflow
result = await orchestrator.execute_workflow(
    dimension="Data Quality",
    questions_data=survey_questions,
    customer_name="Acme Corporation",
    customer_code="ACME",
    pdf_output_path="/path/to/output.pdf"
)
```

### Option 3: Individual Agents

Each agent can be used independently:

```python
from app.agents import SurveyParserAgent, MaturityAssessorAgent
from app.llm_providers import get_llm_provider

llm_provider = get_llm_provider(llm_config)

# Step 1: Parse survey
parser = SurveyParserAgent(llm_provider)
parser_result = await parser.execute(
    dimension="Data Quality",
    questions_data=survey_questions
)

survey_stats = parser_result.output

# Step 2: Assess maturity
assessor = MaturityAssessorAgent(llm_provider, rag_service)
assessor_result = await assessor.execute(
    dimension="Data Quality",
    survey_stats=survey_stats,
    questions_data=survey_questions
)

maturity_assessment = assessor_result.output
composite_score = maturity_assessment['composite_score']
print(f"Composite maturity: {composite_score}/5")
```

## Configuration

### Workflow Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_pdf` | bool | False | Generate PDF output |
| `enable_revision` | bool | True | Allow Self-Critic revisions |
| `max_revisions` | int | 1 | Max revision attempts |
| `quality_threshold` | float | 8.0 | Min acceptable quality score (1-10) |

### LLM Configuration

The agentic workflow uses the same LLM configurations as the existing system:
- **LOCAL**: LM Studio at `http://localhost:1234`
- **AWS Bedrock**: Claude Sonnet with optional thinking mode
- **Azure OpenAI**: GPT-5 with reasoning effort

Configure via the EnTrust admin UI or database.

### RAG Configuration

ChromaDB knowledge base must be initialized:
```bash
cd backend
python -m app.rag --force  # Re-ingest if needed
```

Knowledge base location: `backend/Knowledge/`
- `privacy_compliance/`: GDPR, CCPA docs
- `quality/`: ISO 8000, data quality frameworks
- `governance_management/`: DAMA-DMBOK, COBIT
- `security_access/`: NIST 800-53, ISO 27001
- `lineage_traceability/`: Lineage standards
- `metadata_documentation/`: Dublin Core, ISO 11179
- `value_lifecycle/`: Lifecycle management
- `ethics_bias/`: AI ethics, IEEE guidelines
- `maturity/`: DAMA-DMBOK, Gartner EIM maturity models

## Output Structure

### Workflow Result

```json
{
  "success": true,
  "workflow_results": {
    "dimension": "Data Privacy & Compliance",
    "customer_name": "Acme Corporation",
    "customer_code": "ACME",
    "agents_executed": [
      "SurveyParserAgent",
      "MaturityAssessorAgent",
      "ReportGeneratorAgent",
      "SelfCriticAgent (Attempt 1)",
      "PDFFormatterAgent"
    ],
    "revision_count": 0,
    "final_quality_score": 8.7,
    "quality_approved": true,
    "survey_parser": {...},
    "maturity_assessor": {...},
    "report_generator": {...},
    "self_critic_attempt_0": {...},
    "pdf_formatter": {...}
  },
  "final_report": {
    "dimension": "Data Privacy & Compliance",
    "executive_summary": "...",
    "sections": [...],
    "action_items": [...],
    "roadmap": {...},
    "visuals": {...},
    "metadata": {...}
  },
  "execution_summary": {
    "total_time_seconds": 145.6,
    "agents_executed": 5,
    "revision_count": 0,
    "final_quality_score": 8.7,
    "quality_approved": true
  }
}
```

### Report Structure

```json
{
  "dimension": "Data Privacy & Compliance",
  "executive_summary": "# Executive Summary\n\nThe organization demonstrates...",
  "sections": [
    {
      "section_id": "current_state",
      "title": "Current State Assessment",
      "content": "## Current State Assessment\n\n**Overview Metrics:**\n- Average Score: 6.8/10\n..."
    },
    {
      "section_id": "category_analysis",
      "title": "Analysis by Category",
      "content": "## Analysis by Category\n\n| Category | Avg Score | ... |\n..."
    },
    {
      "section_id": "maturity_assessment",
      "title": "Maturity Assessment",
      "content": "## Maturity Assessment\n\n**Composite Maturity Score:** 2.8/5\n..."
    }
  ],
  "action_items": [
    {
      "action": "Implement GDPR-compliant consent management system",
      "priority": "High",
      "owner": "Chief Privacy Officer",
      "timeline": "Q2 2026",
      "expected_outcome": "Reduce consent-related compliance risk by 80%",
      "framework": "GDPR Article 7"
    }
  ],
  "roadmap": {
    "Phase 1: Foundation (0-6 months)": [...],
    "Phase 2: Enhancement (6-12 months)": [...],
    "Phase 3: Optimization (12+ months)": [...]
  },
  "visuals": {
    "category_scores": {"Consent Management": 4.2, "Data Minimization": 7.8, ...},
    "maturity_by_framework": {"GDPR": 2.5, "CCPA": 3.0, "NIST Privacy": 2.8, ...},
    "score_distribution": {"1-4 (Low)": 15, "5-7 (Medium)": 32, "8-10 (High)": 8},
    "word_cloud_themes": ["manual processes", "consent tracking", "data retention", ...]
  },
  "metadata": {
    "customer_name": "Acme Corporation",
    "generation_timestamp": 1699564800.0,
    "avg_score": 6.8,
    "composite_maturity": 2.8
  }
}
```

## Maturity Scoring

### Maturity Levels (1-5 Scale)

| Level | Name | Characteristics |
|-------|------|----------------|
| 1 | Initial/Ad-hoc | No formal processes, reactive, ad-hoc practices |
| 2 | Repeatable/Reactive | Some documentation, reactive management, inconsistent execution |
| 3 | Defined/Proactive | Formalized processes, proactive management, standardized practices |
| 4 | Managed/Quantified | Measured processes, data-driven decisions, optimization focus |
| 5 | Optimized/Continuous Improvement | Automated, continuously improved, industry-leading practices |

### Framework-Specific Assessment

Each dimension is assessed against 3-4 relevant frameworks:
- **Data Privacy**: GDPR (Articles 5-7, 13-15, 32-34), CCPA (Sections 1798.100-1798.150), NIST Privacy Framework, ISO 27701
- **Data Quality**: ISO 8000 (data quality principles), TDQM (Total Data Quality Management), DAMA-DMBOK Quality Knowledge Area
- **Governance**: DAMA-DMBOK (governance knowledge area), COBIT (APO01, DSS06), Gartner EIM Maturity Model
- **Security**: NIST 800-53 (controls), ISO 27001 (Annex A controls), CIS Controls
- **Lineage**: DAMA-DMBOK (lineage), W3C PROV-DM (provenance data model)
- **Metadata**: Dublin Core (metadata standard), DAMA-DMBOK (metadata management), ISO 11179
- **Value/Lifecycle**: DAMA-DMBOK (lifecycle), Information Lifecycle Management (ILM)
- **Ethics/Bias**: IEEE Ethically Aligned Design, AI Ethics Guidelines

### Composite Maturity Score

The composite score is the average of all framework-specific scores:
```
Composite Score = (GDPR Score + CCPA Score + NIST Score + ISO 27701 Score) / 4
```

### Gap Prioritization

Gaps are prioritized by:
1. **Business Impact**: Regulatory risk, operational efficiency, data quality impact
2. **Urgency**: Immediate (< 3 months), Short-term (3-6 months), Long-term (6-12 months)
3. **Remediation Complexity**: Low (< 1 month, < $50k), Medium (1-3 months, $50k-$200k), High (3-6 months, > $200k)

## Quality Scoring

### Self-Critic Dimensions (1-10 Scale)

| Dimension | Description | Quality Indicators |
|-----------|-------------|-------------------|
| **Clarity** | Structure, readability, logical flow | Clear headers, concise paragraphs, logical progression |
| **Actionability** | Specific recommendations, ownership, timelines | Concrete actions, named owners, dates (e.g., Q2 2026) |
| **Standards Alignment** | Framework references, best practice grounding | Cites GDPR Article 7, NIST 800-53, ISO 8000, etc. |
| **Completeness** | Section depth, detail coverage | All sections present, sufficient detail, evidence-based |

### Quality Thresholds

- **Score ≥ 8.0**: Report approved, no revision needed
- **Score < 8.0**: Revision triggered (if `enable_revision=True`)

### Revision Loop

If average score < threshold:
1. Self-Critic generates specific revision notes (3-5 recommendations)
2. Report Generator re-runs with feedback (if `max_revisions` not exceeded)
3. Self-Critic re-scores the revised report
4. Repeat until approved or max revisions reached

## Performance

### Typical Execution Times

| Agent | Avg Time | Notes |
|-------|----------|-------|
| Survey Parser | 5-10s | Depends on question count, LLM for themes |
| Maturity Assessor | 30-60s | Multiple framework assessments, RAG queries |
| Report Generator | 45-90s | Comprehensive sections, LLM-generated content |
| Self-Critic | 10-20s | Quality scoring |
| PDF Formatter | 15-30s | If enabled, graph generation + PDF conversion |
| **Total** | **105-210s** | **~2-3.5 minutes per dimension** |

### Optimization Tips

1. **Disable PDF generation** if not needed: `enable_pdf=False`
2. **Reduce max revisions**: `max_revisions=0` (no revisions)
3. **Use local LLM** for faster responses (LM Studio)
4. **Batch dimensions**: Run multiple dimensions in parallel (separate workflows)

## Error Handling

### Graceful Degradation

- **RAG unavailable**: Workflow proceeds without RAG context, uses LLM knowledge
- **PDF tools missing**: PDF generation skipped, report still generated
- **LLM timeout**: Agent retries once, then fails with clear error message
- **Agent failure**: Workflow stops at failed agent, returns partial results

### Error Response

```json
{
  "success": false,
  "error": "Maturity Assessor Agent failed: LLM timeout",
  "workflow_results": {
    "agents_executed": ["SurveyParserAgent"],
    "survey_parser": {...}
  },
  "final_report": null,
  "execution_summary": {
    "total_time_seconds": 45.2,
    "agents_executed": 1,
    "failed_at": "Maturity Assessor Agent"
  }
}
```

## Comparison: Agentic vs. Traditional

| Feature | Traditional Workflow | Agentic Workflow |
|---------|---------------------|------------------|
| **Analysis Depth** | Single LLM call per dimension | 5 specialized agents, multi-step |
| **Maturity Assessment** | Generic maturity mention | Framework-specific (3-4 per dimension) with scores |
| **Standards Integration** | RAG context injected once | RAG queried per framework + maturity gaps |
| **Quality Assurance** | None | Self-Critic with 4-dimensional scoring |
| **Revisions** | None | Iterative (max 1 by default) |
| **Action Items** | LLM-generated list | RICE-scored, prioritized initiatives |
| **Roadmap** | None | 6-12 month phased plan |
| **PDF Output** | None | Optional professional PDF with visuals |
| **Execution Time** | ~30-60s | ~105-210s (2-3.5 minutes) |

## Backward Compatibility

### Legacy Format Conversion

The `AgenticReportService.convert_to_legacy_format()` method transforms agentic reports into the existing EnTrust format:

```python
legacy_report = AgenticReportService.convert_to_legacy_format(
    workflow_result, questions_data
)

# Saves to existing paths
save_reports(
    customer_code=customer_code,
    customer_name=customer_name,
    dimension=dimension,
    report_data=legacy_report
)
```

### Existing UI Compatibility

The agentic workflow output is compatible with the existing React UI:
- `overall_metrics`: Survey stats (avg_score, response_rate, etc.)
- `category_analysis`: Category-level stats
- `process_analysis`: Process-level stats
- `lifecycle_analysis`: Lifecycle-level stats
- `dimension_llm_analysis`: Executive summary (Markdown)
- `questions`: Question-level data

**New fields** (optional):
- `agentic_report`: Boolean flag
- `agentic_sections`: Detailed sections
- `action_items`: Prioritized actions
- `roadmap`: Strategic roadmap
- `maturity_assessment`: Framework-specific maturity
- `quality_score`: Self-Critic score
- `visuals`: Graph/word cloud data

## Future Enhancements

1. **Automatic Revision**: Implement Report Generator revision logic (currently manual)
2. **Multi-Dimension Reports**: Generate overall report by orchestrating 8 dimension workflows
3. **Custom Agents**: Allow users to define custom agents (e.g., industry-specific analysis)
4. **Agent Chaining**: Support more complex workflows (e.g., parallel agents, conditional execution)
5. **Performance Optimization**: Cache intermediate results, parallel LLM calls
6. **Advanced PDF**: Interactive PDFs with clickable links, table of contents, bookmarks
7. **Real-Time Streaming**: Stream agent progress to UI (WebSocket)

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| RAG context not used | ChromaDB not initialized | Run `python -m app.rag` to ingest knowledge base |
| PDF generation skipped | WeasyPrint/Pandoc missing | Install: `pip install weasyprint` or `apt-get install pandoc` |
| LLM timeout | Model overloaded | Reduce question count, increase timeout, use faster model |
| Low quality score | Report lacks detail | Increase `max_tokens` for Report Generator, add more RAG context |
| Agent error | Invalid input format | Check `questions_data` schema (must have `question_id`, `text`, `avg_score`, etc.) |

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Inspect workflow results:
```python
result = await orchestrator.execute_workflow(...)
print(json.dumps(result['workflow_results'], indent=2))
```

## Contributors

Developed by Claude (Anthropic) for the EnTrust platform.

## License

Follows EnTrust platform licensing.
