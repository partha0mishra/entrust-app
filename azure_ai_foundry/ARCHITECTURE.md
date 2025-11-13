# Azure AI Foundry Architecture for Entrust Survey Analysis

## Executive Summary

This document describes the architecture for migrating the Entrust survey analysis system from direct LLM API calls to Azure AI Foundry Agents, implementing an agentic workflow with memory, orchestration, and standards-based maturity analysis.

## System Overview

### Current State (Before Migration)
- **LLM Integration**: Direct API calls to LM Studio (local), AWS Bedrock, or Azure OpenAI
- **Report Generation**: Monolithic LLM calls with chunking for large survey data
- **RAG**: ChromaDB local instance with standards documents
- **Output**: JSON/Markdown reports saved to filesystem

### Target State (After Migration)
- **LLM Integration**: Azure AI Foundry Agent endpoints
- **Report Generation**: Modular agentic workflow with specialized agents
- **RAG**: ChromaDB (local or Azure-hosted) accessed via custom tools
- **Output**: Enhanced reports with maturity assessments, action items, roadmaps
- **Observability**: Built-in tracing, monitoring, and evaluations

## Azure AI Foundry Architecture

### Core Components

#### 1. Agent Framework

Five specialized agents orchestrated via Azure AI Foundry flows:

##### **Survey Parser Agent**
- **Purpose**: Analyze survey JSON data, compute statistics, extract themes
- **Inputs**: Survey JSON (questions, scores, comments, metadata)
- **Outputs**: Statistical summaries, theme extractions, data quality checks
- **Tools Used**: `stats_tools.py`
- **Prompt**: Chain-of-Thought reasoning for statistical analysis

##### **Maturity Assessor Agent**
- **Purpose**: Evaluate organizational maturity against industry standards
- **Inputs**: Survey statistics, dimension focus
- **Outputs**: Maturity level (1-5), gap analysis, benchmark comparisons
- **Tools Used**: `rag_tools.py` for standards retrieval
- **Prompt**: Standards-grounded assessment (GDPR, DAMA-DMBOK, NIST, ISO 8000)

##### **Report Generator Agent**
- **Purpose**: Synthesize comprehensive, action-oriented reports
- **Inputs**: Statistics, maturity assessment, RAG context
- **Outputs**: 50+ page markdown report with sections:
  - Executive Summary
  - Current State Assessment
  - Maturity Analysis (standards-based)
  - Category/Process/Lifecycle Breakdown
  - Key Findings & Insights
  - Risk Analysis
  - Prioritized Action Items (risk/impact matrix)
  - 6-12 Month Roadmap
  - Visualizations (graphs, word clouds)
- **Tools Used**: `graph_tools.py` for visualizations
- **Prompt**: Professional, detailed, action-oriented generation

##### **Self-Critic Agent**
- **Purpose**: Quality assurance and report refinement
- **Inputs**: Draft report, original survey data
- **Outputs**: Quality score, revision suggestions, refined report
- **Prompt**: Evaluate completeness, accuracy, alignment with standards

##### **PDF Formatter Agent**
- **Purpose**: Convert markdown to professional PDF
- **Inputs**: Markdown report
- **Outputs**: Styled PDF with branding, table of contents, page numbers
- **Tools Used**: `pdf_tools.py` (WeasyPrint/Pandoc)

#### 2. Flow Orchestration

##### **Dimension Analysis Flow**
For each of the 8 dimensions:

```yaml
flow: dimension_analysis
inputs:
  - survey_data: JSON
  - dimension: str
  - customer_code: str
steps:
  1. survey_parser:
       agent: survey_parser_agent
       inputs: {survey_data, dimension}
       outputs: {statistics, themes}
  2. maturity_assessor:
       agent: maturity_assessor_agent
       inputs: {statistics, dimension}
       tools: [rag_query_tool]
       outputs: {maturity_level, gaps, standards_context}
  3. report_generator:
       agent: report_generator_agent
       inputs: {statistics, maturity_level, gaps, standards_context}
       tools: [graph_generation_tool]
       outputs: {draft_report}
  4. self_critic:
       agent: self_critic_agent
       inputs: {draft_report, survey_data}
       outputs: {quality_score, final_report}
  5. pdf_formatter:
       agent: pdf_formatter_agent
       inputs: {final_report}
       tools: [pdf_conversion_tool]
       outputs: {pdf_report}
outputs:
  - final_report: markdown
  - pdf_report: binary
  - metadata: {maturity_level, quality_score}
```

##### **Overall Synthesis Flow**
Cross-dimension synthesis:

```yaml
flow: overall_synthesis
inputs:
  - dimension_reports: List[Dict]
  - customer_code: str
steps:
  1. consolidation:
       agent: report_generator_agent
       inputs: {dimension_reports}
       prompt: overall_summary_prompt
       outputs: {consolidated_report}
  2. self_critic:
       agent: self_critic_agent
       inputs: {consolidated_report}
       outputs: {quality_score, final_overall_report}
  3. pdf_formatter:
       agent: pdf_formatter_agent
       inputs: {final_overall_report}
       outputs: {pdf_report}
outputs:
  - final_report: markdown
  - pdf_report: binary
```

##### **Orchestrator Flow**
Top-level orchestration for complete survey analysis:

```yaml
flow: orchestrator
inputs:
  - survey_data: JSON
  - customer_code: str
steps:
  1. dimension_analyses:
       flow: dimension_analysis
       parallel: true
       for_each: dimension in [
         "Data Privacy & Compliance",
         "Data Quality",
         "Data Governance & Management",
         "Data Security & Access",
         "Data Lineage & Traceability",
         "Metadata & Documentation",
         "Data Value & Lifecycle Management",
         "Data Ethics & Bias"
       ]
       inputs: {survey_data, dimension, customer_code}
       outputs: dimension_reports[]
  2. overall_synthesis:
       flow: overall_synthesis
       inputs: {dimension_reports, customer_code}
       outputs: {final_overall_report}
outputs:
  - dimension_reports: List[Dict]
  - overall_report: Dict
```

#### 3. Memory & State Management

- **Flow State**: Azure AI Foundry maintains state between agent calls within a flow
- **Conversation History**: Each agent can access previous agent outputs via flow state
- **RAG Context**: Retrieved standards context persisted in flow state for consistency
- **Survey Context**: Original survey data accessible throughout the flow

#### 4. Custom Tools

Tools are Python functions callable by agents:

##### **RAG Tools** (`tools/rag_tools.py`)
```python
@tool
def query_rag_standards(dimension: str, query: str, top_k: int = 5) -> str:
    """
    Query ChromaDB for standards and best practices

    Args:
        dimension: Data dimension (e.g., "Data Privacy & Compliance")
        query: Search query
        top_k: Number of results

    Returns:
        Formatted standards context
    """
    # Implementation uses backend/app/rag.py
```

##### **Stats Tools** (`tools/stats_tools.py`)
```python
@tool
def compute_survey_statistics(survey_data: Dict) -> Dict:
    """Compute comprehensive statistics from survey data"""

@tool
def compute_maturity_score(scores: List[float], weights: Dict) -> float:
    """Calculate weighted maturity score"""

@tool
def identify_risk_areas(survey_data: Dict, threshold: float = 5.0) -> List[Dict]:
    """Identify low-scoring areas requiring attention"""
```

##### **Graph Tools** (`tools/graph_tools.py`)
```python
@tool
def generate_score_distribution_chart(scores: List[float]) -> str:
    """Generate histogram of score distribution (returns base64 PNG)"""

@tool
def generate_dimension_comparison_radar(dimension_scores: Dict) -> str:
    """Generate radar chart comparing dimensions"""

@tool
def generate_word_cloud(comments: List[str]) -> str:
    """Generate word cloud from comments"""
```

##### **PDF Tools** (`tools/pdf_tools.py`)
```python
@tool
def convert_markdown_to_pdf(markdown: str, title: str, metadata: Dict) -> bytes:
    """Convert markdown report to styled PDF"""
```

#### 5. Prompt Templates

Modular Jinja2 templates for reusability:

##### **Base Prompts** (`prompts/base/`)
- `system_prompts.jinja`: Role definitions, output formatting
- `cot_reasoning.jinja`: Chain-of-Thought reasoning patterns

##### **Dimension-Specific Prompts** (`prompts/dimensions/`)
Each dimension has a tailored prompt emphasizing relevant standards:

- `privacy_compliance.jinja`: GDPR, CCPA, HIPAA focus
- `data_quality.jinja`: ISO 8000, DAMA-DMBOK Data Quality chapter
- `governance_management.jinja`: DAMA-DMBOK Governance chapter
- `security_access.jinja`: NIST CSF, ISO 27001
- `lineage_traceability.jinja`: Data lineage best practices
- `metadata_documentation.jinja`: Metadata standards
- `value_lifecycle.jinja`: Data lifecycle management
- `ethics_bias.jinja`: Ethical AI frameworks

Example template structure:
```jinja
{% extends "base/system_prompts.jinja" %}

{% block role %}
You are an expert data governance analyst specializing in {{ dimension }}.
{% endblock %}

{% block standards_context %}
Relevant Standards:
{{ rag_context }}
{% endblock %}

{% block task %}
Analyze the survey data for {{ dimension }} and provide:
1. Current State Assessment
2. Maturity Level (1-5) based on {{ standards|join(", ") }}
3. Gap Analysis
4. Prioritized Action Items
5. 6-12 Month Roadmap
{% endblock %}

{% block output_format %}
Output as markdown with the following structure:
...
{% endblock %}
```

## Integration with Entrust-App Backend

### SDK Integration Layer (`sdk/`)

#### **Foundry Client** (`sdk/foundry_client.py`)
```python
class AzureAIFoundryClient:
    """Client for interacting with Azure AI Foundry endpoints"""

    def __init__(self, project_endpoint: str, api_key: str):
        self.project_endpoint = project_endpoint
        self.api_key = api_key
        self.client = self._initialize_client()

    async def invoke_flow(
        self,
        flow_name: str,
        inputs: Dict,
        timeout: int = 1800
    ) -> Dict:
        """Invoke a deployed flow with inputs"""
        # Uses azure-ai-projects SDK
```

#### **Agent Runner** (`sdk/agent_runner.py`)
```python
class AgentRunner:
    """Execute individual agents for testing"""

    async def run_agent(
        self,
        agent_name: str,
        inputs: Dict,
        tools: List[Callable] = None
    ) -> Dict:
        """Run a single agent with specified tools"""
```

#### **Flow Executor** (`sdk/flow_executor.py`)
```python
class FlowExecutor:
    """Orchestrate flow execution from entrust-app"""

    async def execute_dimension_analysis(
        self,
        survey_data: Dict,
        dimension: str,
        customer_code: str
    ) -> Dict:
        """Execute dimension analysis flow"""

    async def execute_overall_synthesis(
        self,
        dimension_reports: List[Dict],
        customer_code: str
    ) -> Dict:
        """Execute overall synthesis flow"""
```

### Backend Integration Points

#### **Modified LLM Service** (`backend/app/llm_service.py`)
Add new provider type for Azure AI Foundry:

```python
class AzureAIFoundryProvider(BaseLLMProvider):
    """Provider for Azure AI Foundry Agents"""

    def __init__(self, project_endpoint: str, api_key: str, flow_name: str):
        self.client = AzureAIFoundryClient(project_endpoint, api_key)
        self.flow_name = flow_name

    async def call_llm(self, messages: List[Dict], max_tokens: int = 500) -> str:
        """Call Azure AI Foundry flow instead of direct LLM"""
        # Convert messages to flow inputs
        inputs = self._prepare_flow_inputs(messages)
        result = await self.client.invoke_flow(self.flow_name, inputs)
        return result.get("output", "")
```

#### **Updated Reports Router** (`backend/app/routers/reports.py`)
Replace direct LLM calls with Foundry flow calls:

```python
@router.get("/customer/{customer_id}/dimension/{dimension}")
async def get_dimension_report(...):
    # ... existing code ...

    # Instead of:
    # llm_response = await LLMService.generate_deep_dimension_analysis(...)

    # Use Foundry flow:
    flow_executor = FlowExecutor(foundry_config)
    flow_result = await flow_executor.execute_dimension_analysis(
        survey_data={
            "questions": questions_for_llm,
            "statistics": overall_metrics,
            "facets": {
                "categories": category_analysis,
                "processes": process_analysis,
                "lifecycle": lifecycle_analysis
            }
        },
        dimension=dimension,
        customer_code=customer.customer_code
    )

    dimension_llm_analysis = flow_result.get("final_report")
    maturity_assessment = flow_result.get("metadata", {}).get("maturity_level")
```

### Configuration Management (`config/`)

#### **Endpoints Configuration** (`config/endpoints.py`)
```python
from typing import Dict
from dataclasses import dataclass

@dataclass
class AzureAIFoundryConfig:
    project_endpoint: str
    api_key: str
    flows: Dict[str, str]  # flow_name -> endpoint_url

def load_foundry_config() -> AzureAIFoundryConfig:
    """Load configuration from environment or database"""
    # Check for environment variables first
    # Fall back to database LLMConfig table
```

#### **Model Configuration** (`config/model_config.yaml`)
```yaml
agents:
  survey_parser:
    model: gpt-4o
    temperature: 0.3
    max_tokens: 4000

  maturity_assessor:
    model: gpt-4o
    temperature: 0.5
    max_tokens: 8000

  report_generator:
    model: gpt-4o
    temperature: 0.7
    max_tokens: 16000

  self_critic:
    model: gpt-4o
    temperature: 0.3
    max_tokens: 4000

  pdf_formatter:
    model: gpt-4o-mini
    temperature: 0.1
    max_tokens: 2000

flows:
  dimension_analysis:
    timeout: 1800  # 30 minutes
    retry_attempts: 2

  overall_synthesis:
    timeout: 1200  # 20 minutes
    retry_attempts: 2
```

## RAG Integration with Azure

### Option 1: Keep ChromaDB Local
- Minimal changes to existing `backend/app/rag.py`
- Tools access local ChromaDB instance
- Pro: No migration needed
- Con: Not cloud-native, scaling limitations

### Option 2: Azure AI Search
- Migrate ChromaDB knowledge base to Azure AI Search
- Update `tools/rag_tools.py` to use Azure AI Search SDK
- Pro: Cloud-native, better scalability, integrated with Foundry
- Con: Migration effort, additional cost

**Recommendation**: Start with Option 1, migrate to Option 2 for production at scale.

### RAG Tool Implementation

```python
# tools/rag_tools.py
from azure.ai.projects import tool
from backend.app.rag import get_dimension_context

@tool
def query_standards(dimension: str, query: str, top_k: int = 5) -> str:
    """
    Query knowledge base for standards and best practices

    This tool retrieves relevant standards context from the RAG store
    to ground maturity assessments in established frameworks.
    """
    context = get_dimension_context(dimension, query, top_k)
    return context
```

## Deployment Strategy

### Phase 1: Development & Testing (Local)
1. Implement agent definitions locally
2. Test agents with sample survey data
3. Validate report quality against existing reports
4. Iterate on prompts and tools

### Phase 2: Azure AI Foundry Deployment
1. Create Azure AI Foundry project
2. Deploy agent flows to Foundry
3. Configure endpoints and API keys
4. Test deployed flows with entrust-app backend

### Phase 3: Integration
1. Update `backend/app/llm_providers.py` with Foundry provider
2. Add Foundry configuration to `LLMConfig` database model
3. Update UI to allow Foundry configuration
4. Migrate existing LLM configs to Foundry

### Phase 4: Production
1. Performance optimization
2. Monitoring and observability setup
3. Cost optimization (model selection, caching)
4. Scale testing

## Security & Best Practices

### Security
- **API Keys**: Store in Azure Key Vault, never in code
- **Data Protection**: Encrypt survey data in transit and at rest
- **Access Control**: Use Azure AD for authentication
- **Audit Logging**: Enable Azure AI Foundry audit logs

### Observability
- **Tracing**: Azure AI Foundry built-in tracing for agent calls
- **Monitoring**: Azure Monitor for flow execution metrics
- **Logging**: Structured logging for debugging
- **Evaluations**: Continuous evaluation of report quality

### Best Practices
1. **Modularity**: Each agent is independent and testable
2. **Prompt Engineering**: Use Chain-of-Thought for reasoning
3. **Tool Design**: Tools are stateless and reusable
4. **Error Handling**: Graceful degradation if agents fail
5. **Cost Optimization**:
   - Use smaller models for simple tasks (PDF formatting)
   - Cache RAG queries
   - Implement token usage tracking
6. **Quality Assurance**: Self-Critic agent for report validation

## Performance Considerations

### Latency
- **Current**: 5-20 minutes per dimension report (AWS Bedrock with thinking mode)
- **Target**: 10-30 minutes per dimension (with agent orchestration overhead)
- **Optimization**: Parallel execution of dimension flows

### Throughput
- **Current**: Sequential processing of dimensions
- **Target**: Parallel processing of 8 dimensions + overall
- **Benefit**: ~8x speedup for full survey analysis

### Cost
- **Model Selection**: Use cost-effective models per agent task
- **Caching**: Cache RAG queries and intermediate results
- **Monitoring**: Track token usage per customer

## Testing Strategy

### Unit Tests
- Individual agent tests with mock inputs
- Tool function tests
- Prompt template rendering tests

### Integration Tests
- End-to-end flow tests with sample survey data
- Validation against existing report quality
- Standards alignment verification

### Evaluation Metrics
- **Completeness**: All report sections present
- **Accuracy**: Maturity scores align with survey data
- **Actionability**: Action items are specific and prioritized
- **Alignment**: References to relevant standards
- **Quality**: Report readability and professionalism

## Migration Checklist

- [x] Architecture design documented
- [ ] Agent definitions created
- [ ] Prompt templates migrated
- [ ] Custom tools implemented
- [ ] Flow definitions created
- [ ] SDK integration layer built
- [ ] Backend integration updated
- [ ] Configuration management implemented
- [ ] Local testing completed
- [ ] Azure AI Foundry deployment
- [ ] Integration testing
- [ ] Performance benchmarking
- [ ] Documentation updated
- [ ] Production deployment

## References

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Azure AI Projects SDK](https://learn.microsoft.com/python/api/azure-ai-projects/)
- [Prompt Flow](https://microsoft.github.io/promptflow/)
- [DAMA-DMBOK](https://www.dama.org/cpages/body-of-knowledge)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [GDPR Compliance](https://gdpr.eu/)
- [ISO 8000 Data Quality](https://www.iso.org/standard/50798.html)
