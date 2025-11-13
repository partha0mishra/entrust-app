# Azure AI Foundry Integration for Entrust Survey Analysis

This directory contains the Azure AI Foundry-based agentic workflow for generating comprehensive, professional, action-oriented data management survey reports.

## Overview

The system migrates from direct LLM API calls (LM Studio, AWS Bedrock, Azure OpenAI) to Azure AI Foundry Agents with memory, orchestration, and enhanced observability.

## Architecture

### Agentic Workflow

For each of the 8 data management dimensions plus overall synthesis, we deploy modular agent flows:

1. **Survey Parser Agent**: Analyzes JSON survey data, computes statistics, extracts themes
2. **Maturity Assessor Agent**: Evaluates maturity against standards (GDPR, DAMA-DMBOK, NIST, ISO 8000) using RAG
3. **Report Generator Agent**: Crafts detailed 50+ page reports with stats, action items, roadmaps, graphs, word clouds
4. **Self-Critic Agent**: Scores and revises reports for quality and alignment
5. **PDF Formatter Agent**: Converts markdown to professional PDF

### Memory & State Management

- **Flow State**: Azure AI Foundry flows maintain state between agent calls
- **Standards Consistency**: ChromaDB RAG store provides consistent standards context
- **Survey Context**: Passed through flow for context-aware analysis

## Directory Structure

```
azure_ai_foundry/
├── README.md                    # This file
├── ARCHITECTURE.md              # Detailed architecture documentation
├── agents/                      # Agent definitions (YAML/JSON for Foundry)
│   ├── survey_parser.yaml
│   ├── maturity_assessor.yaml
│   ├── report_generator.yaml
│   ├── self_critic.yaml
│   └── pdf_formatter.yaml
├── prompts/                     # Reusable prompt templates (.jinja)
│   ├── base/
│   │   ├── system_prompts.jinja
│   │   └── cot_reasoning.jinja
│   ├── dimensions/              # Per-dimension prompts
│   │   ├── privacy_compliance.jinja
│   │   ├── data_quality.jinja
│   │   ├── governance_management.jinja
│   │   ├── security_access.jinja
│   │   ├── lineage_traceability.jinja
│   │   ├── metadata_documentation.jinja
│   │   ├── value_lifecycle.jinja
│   │   └── ethics_bias.jinja
│   └── overall_summary.jinja
├── tools/                       # Custom Python tools for agents
│   ├── __init__.py
│   ├── rag_tools.py            # ChromaDB query tools
│   ├── stats_tools.py          # Statistical analysis tools
│   ├── graph_tools.py          # Visualization generation
│   └── pdf_tools.py            # PDF conversion tools
├── flows/                       # Azure AI Foundry flow definitions
│   ├── dimension_analysis_flow.yaml
│   ├── overall_synthesis_flow.yaml
│   └── orchestrator_flow.yaml
├── sdk/                         # Azure AI SDK integration
│   ├── __init__.py
│   ├── foundry_client.py       # Client for Foundry endpoints
│   ├── agent_runner.py         # Agent execution wrapper
│   └── flow_executor.py        # Flow orchestration
└── config/                      # Configuration files
    ├── __init__.py
    ├── endpoints.py            # Endpoint configuration
    ├── model_config.yaml       # Model selection config
    └── security_config.yaml    # Security & auth config
```

## The 8 Data Management Dimensions

1. **Data Privacy & Compliance**: GDPR, CCPA, regulatory compliance
2. **Data Quality**: Accuracy, completeness, consistency, timeliness
3. **Data Governance & Management**: Policies, ownership, stewardship
4. **Data Security & Access**: Encryption, access control, threat protection
5. **Data Lineage & Traceability**: Data flow, transformation tracking
6. **Metadata & Documentation**: Data dictionaries, catalogs, descriptions
7. **Data Value & Lifecycle Management**: ROI, retention, archival
8. **Data Ethics & Bias**: Fairness, transparency, ethical use

## Integration with Entrust-App

The entrust-app backend (FastAPI) calls Azure AI Foundry endpoints via the Python SDK:

1. **Survey Data Input**: JSON survey data sent to flow endpoints
2. **Agent Execution**: Foundry orchestrates agent sequence with memory
3. **Report Output**: Agents return structured JSON reports
4. **Storage**: Reports saved as JSON/Markdown/PDF on filesystem

## Setup & Configuration

### Prerequisites

- Azure AI Foundry project with deployed endpoints
- API keys for authentication
- ChromaDB instance (local or Azure-hosted)
- Python 3.10+

### Installation

```bash
# Install Azure AI SDK
pip install azure-ai-projects azure-identity

# Install dependencies for tools
pip install chromadb sentence-transformers matplotlib plotly wordcloud weasyprint
```

### Configuration

Update `config/endpoints.py` with your Azure AI Foundry endpoints and API keys from the LLM setup screen.

```python
# Example configuration
AZURE_AI_FOUNDRY_CONFIG = {
    "project_endpoint": "https://<your-project>.api.azureml.ms",
    "api_key": "<your-api-key>",
    "flows": {
        "dimension_analysis": "<flow-endpoint-url>",
        "overall_synthesis": "<flow-endpoint-url>"
    }
}
```

## Best Practices from Azure AI Foundry

1. **Observability**: All agent calls traced via Foundry's built-in monitoring
2. **Security**:
   - API keys stored securely (Azure Key Vault recommended)
   - Identity-based access control
   - Data protection with encryption
3. **Guardrails**: Content safety filters for ethical analysis
4. **Evaluations**: Continuous testing of agent outputs
5. **Model Selection**: Benchmark-based model selection per agent task
6. **Connected Agents**: Integration with 1400+ connectors if needed

## Development Workflow

1. **Define Agents**: Create YAML definitions in `agents/`
2. **Create Prompts**: Develop Jinja templates in `prompts/`
3. **Build Tools**: Implement custom tools in `tools/`
4. **Compose Flows**: Orchestrate agents in Foundry flow definitions
5. **Deploy**: Deploy flows to Azure AI Foundry endpoints
6. **Integrate**: Update entrust-app to call Foundry endpoints via SDK
7. **Test**: Validate report quality and alignment with standards

## RAG Integration

ChromaDB stores standards documents for each dimension:
- GDPR, DAMA-DMBOK, NIST, ISO 8000, etc.
- Query via `tools/rag_tools.py`
- Context injected into Maturity Assessor Agent prompts

## Testing

```bash
# Test individual agents
python -m azure_ai_foundry.sdk.agent_runner --agent survey_parser --test-data sample_survey.json

# Test full flow
python -m azure_ai_foundry.sdk.flow_executor --flow dimension_analysis --dimension "Data Privacy & Compliance"
```

## Migration Status

- [x] Directory structure created
- [ ] Agent definitions created
- [ ] Prompts migrated to templates
- [ ] Custom tools implemented
- [ ] Flow definitions created
- [ ] SDK integration layer built
- [ ] Backend updated to use Foundry endpoints
- [ ] Configuration management implemented
- [ ] Testing and validation

## References

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Prompt Flow Documentation](https://microsoft.github.io/promptflow/)
- [Azure AI SDK](https://pypi.org/project/azure-ai-projects/)
- [DAMA-DMBOK Framework](https://www.dama.org/cpages/body-of-knowledge)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## License

Proprietary - Entrust Data Governance Survey Analysis System
