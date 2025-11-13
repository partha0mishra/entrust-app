# Azure AI Foundry Deployment Guide

This guide provides step-by-step instructions for deploying and integrating Azure AI Foundry agents with the Entrust survey analysis application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Steps](#deployment-steps)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Production Deployment](#production-deployment)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
8. [Cost Optimization](#cost-optimization)

## Prerequisites

### Azure Requirements

- Azure subscription with Azure AI Foundry access
- Azure AI Studio project created
- API keys and endpoint URLs
- Sufficient quota for GPT-4o models

### Development Environment

- Python 3.10+
- Azure CLI installed and configured
- Git repository access
- Docker (optional, for containerized deployment)

### Python Dependencies

```bash
pip install azure-ai-projects>=1.0.0
pip install azure-identity>=1.15.0
pip install chromadb>=0.4.0
pip install sentence-transformers>=2.2.0
pip install matplotlib>=3.7.0
pip install plotly>=5.14.0
pip install wordcloud>=1.9.0
pip install weasyprint>=59.0
pip install markdown>=3.4.0
```

## Architecture Overview

### Components

1. **Agents** (`agents/`): 5 specialized agents
   - Survey Parser
   - Maturity Assessor
   - Report Generator
   - Self-Critic
   - PDF Formatter

2. **Flows** (`flows/`): 3 orchestrated workflows
   - Dimension Analysis Flow
   - Overall Synthesis Flow
   - Orchestrator Flow

3. **Tools** (`tools/`): Custom Python functions
   - RAG tools (ChromaDB integration)
   - Stats tools (statistical analysis)
   - Graph tools (visualization generation)
   - PDF tools (document conversion)
   - Storage tools (file system operations)

4. **SDK** (`sdk/`): Integration layer
   - Foundry Client (API wrapper)
   - Flow Executor (high-level orchestration)

5. **Configuration** (`config/`): Endpoint management
   - Environment variable support
   - Database configuration support

## Deployment Steps

### Step 1: Create Azure AI Foundry Project

1. Go to [Azure AI Studio](https://ai.azure.com/)
2. Create a new project:
   - Name: `entrust-survey-analysis`
   - Region: Choose based on data residency requirements
   - Resource group: Create or select existing

3. Note your project details:
   - **Project Endpoint**: `https://<your-project>.api.azureml.ms`
   - **API Key**: Found in project settings

### Step 2: Deploy Models

Deploy the following models in Azure AI Studio:

| Agent | Recommended Model | Deployment Name |
|-------|------------------|-----------------|
| Survey Parser | GPT-4o | `gpt-4o-parser` |
| Maturity Assessor | GPT-4o | `gpt-4o-assessor` |
| Report Generator | GPT-4o | `gpt-4o-generator` |
| Self-Critic | GPT-4o | `gpt-4o-critic` |
| PDF Formatter | GPT-4o-mini | `gpt-4o-mini-formatter` |

### Step 3: Create and Deploy Agents

#### Option A: Using Azure AI Studio UI

1. In Azure AI Studio, navigate to "Flows"
2. Create a new flow for each agent:
   - Upload agent YAML from `agents/`
   - Configure model deployment names
   - Test agent with sample inputs

3. Deploy each agent as an endpoint

#### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription <your-subscription-id>

# Deploy dimension analysis flow
az ml flow create \
  --file azure_ai_foundry/flows/dimension_analysis_flow.yaml \
  --resource-group <your-rg> \
  --workspace-name <your-project>

# Deploy overall synthesis flow
az ml flow create \
  --file azure_ai_foundry/flows/overall_synthesis_flow.yaml \
  --resource-group <your-rg> \
  --workspace-name <your-project>

# Deploy orchestrator flow
az ml flow create \
  --file azure_ai_foundry/flows/orchestrator_flow.yaml \
  --resource-group <your-rg> \
  --workspace-name <your-project>
```

### Step 4: Configure ChromaDB RAG Store

#### Local ChromaDB (Development)

```bash
# Navigate to backend
cd backend

# Setup knowledge base
python setup_knowledge.py

# This will:
# 1. Load standards documents from Knowledge/
# 2. Create ChromaDB embeddings
# 3. Store in backend/chroma_db/
```

#### Azure-Hosted ChromaDB (Production)

For production, consider hosting ChromaDB in Azure:

1. **Azure Container Instance**: Run ChromaDB in a container
2. **Azure Kubernetes Service**: For high availability
3. **Azure AI Search**: Migrate to Azure AI Search for cloud-native RAG

Update `tools/rag_tools.py` with Azure connection details.

### Step 5: Configure Entrust-App Backend

#### Option A: Environment Variables (Recommended)

```bash
# .env file in project root
AZURE_AI_FOUNDRY_ENDPOINT=https://<your-project>.api.azureml.ms
AZURE_AI_FOUNDRY_API_KEY=<your-api-key>
AZURE_AI_FOUNDRY_API_VERSION=2024-07-01
```

#### Option B: Database Configuration

Add a new LLMConfig entry in the database:

```sql
INSERT INTO llm_configs (
  purpose,
  provider_type,
  azure_endpoint,
  azure_api_key,
  azure_api_version,
  status
) VALUES (
  'Azure AI Foundry',
  'AZURE',
  'https://<your-project>.api.azureml.ms',
  '<your-api-key>',
  '2024-07-01',
  'Not Tested'
);
```

Then test the connection via the UI.

### Step 6: Integrate with Backend

Update `backend/app/llm_providers.py` to add Azure AI Foundry support:

```python
# Add to llm_providers.py

from azure_ai_foundry.sdk import FlowExecutor
from azure_ai_foundry.config import get_foundry_client

class AzureAIFoundryProvider(BaseLLMProvider):
    """Provider for Azure AI Foundry Agents"""

    def __init__(self):
        self.client = get_foundry_client()
        self.executor = FlowExecutor(self.client)

    async def call_llm(self, messages: List[Dict], max_tokens: int = 500) -> str:
        # Convert messages to flow inputs
        # Call appropriate flow
        # Return result
        pass
```

Update `backend/app/models.py` to add new provider type:

```python
class LLMProviderType(str, enum.Enum):
    LOCAL = "LOCAL"
    BEDROCK = "BEDROCK"
    AZURE = "AZURE"
    AZURE_AI_FOUNDRY = "AZURE_AI_FOUNDRY"  # NEW
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AZURE_AI_FOUNDRY_ENDPOINT` | Project endpoint URL | Yes | - |
| `AZURE_AI_FOUNDRY_API_KEY` | API key | Yes | - |
| `AZURE_AI_FOUNDRY_API_VERSION` | API version | No | `2024-07-01` |
| `AZURE_AI_FOUNDRY_USE_MOCK` | Use mock client for testing | No | `false` |

### Flow Configuration

Edit `azure_ai_foundry/config/model_config.yaml` to adjust model settings:

```yaml
agents:
  survey_parser:
    model: gpt-4o
    temperature: 0.3
    max_tokens: 4000

  # ... other agents
```

### Timeout Configuration

Adjust timeouts based on your requirements:

- **Dimension Analysis**: 1800s (30 minutes) - for complex reports
- **Overall Synthesis**: 1200s (20 minutes)
- **Full Orchestration**: 3600s (60 minutes)

## Testing

### Unit Tests

Test individual components:

```bash
# Test RAG tools
python azure_ai_foundry/tools/rag_tools.py

# Test stats tools
python azure_ai_foundry/tools/stats_tools.py

# Test graph tools
python azure_ai_foundry/tools/graph_tools.py

# Test foundry client
python azure_ai_foundry/sdk/foundry_client.py
```

### Integration Tests

Test flow execution:

```bash
# Set mock mode for testing without deployment
export AZURE_AI_FOUNDRY_USE_MOCK=true

# Test dimension analysis
python -c "
import asyncio
from azure_ai_foundry.sdk import FlowExecutor
from azure_ai_foundry.config import get_foundry_client

async def test():
    client = get_foundry_client()
    executor = FlowExecutor(client)

    result = await executor.execute_dimension_analysis(
        survey_data={'questions': []},
        dimension='Data Privacy & Compliance',
        customer_code='TEST001',
        customer_name='Test Corp'
    )

    print(f'Result: {result[\"success\"]}')

asyncio.run(test())
"
```

### End-to-End Test

Test with real survey data:

```bash
# Navigate to backend
cd backend

# Run report generation with Azure AI Foundry
python -c "
import asyncio
from app.database import SessionLocal
from app import models
from azure_ai_foundry.sdk import FlowExecutor
from azure_ai_foundry.config import get_foundry_client

async def test():
    db = SessionLocal()

    # Get test survey
    survey = db.query(models.Survey).first()
    customer = db.query(models.Customer).filter(
        models.Customer.id == survey.customer_id
    ).first()

    # Execute dimension analysis
    client = get_foundry_client()
    executor = FlowExecutor(client)

    result = await executor.execute_dimension_analysis(
        survey_data={...},  # Load from database
        dimension='Data Privacy & Compliance',
        customer_code=customer.customer_code,
        customer_name=customer.name
    )

    print(f'Report generated: {len(result[\"final_report\"])} chars')

    db.close()

asyncio.run(test())
"
```

## Production Deployment

### Step 1: Security Hardening

1. **API Key Management**:
   - Use Azure Key Vault for API keys
   - Rotate keys regularly
   - Never commit keys to source control

2. **Network Security**:
   - Use Azure Private Link for endpoint access
   - Configure firewall rules
   - Enable Azure AD authentication

3. **Data Protection**:
   - Encrypt survey data in transit and at rest
   - Implement data retention policies
   - Ensure GDPR compliance

### Step 2: Performance Optimization

1. **Caching**:
   - Implement report caching (as already done)
   - Cache RAG query results (TTL: 1 hour)
   - Use Redis for distributed caching

2. **Parallel Processing**:
   - Enable parallel dimension analysis (orchestrator flow)
   - 8x speedup with parallelism

3. **Model Selection**:
   - Use GPT-4o for complex analysis
   - Use GPT-4o-mini for simple tasks (PDF formatting)
   - Monitor token usage and costs

### Step 3: Monitoring & Observability

1. **Azure Monitor Integration**:
   - Enable Application Insights
   - Track flow execution metrics
   - Set up alerts for failures

2. **Logging**:
   - Structured logging with correlation IDs
   - Log levels: INFO for production, DEBUG for development
   - Centralized log aggregation (Azure Log Analytics)

3. **Metrics to Track**:
   - Flow execution time
   - Success/failure rates
   - Token usage per flow
   - Cost per report
   - Agent-level performance

### Step 4: Scaling

1. **Horizontal Scaling**:
   - Deploy multiple flow instances
   - Load balancing across instances

2. **Resource Optimization**:
   - Right-size model deployments
   - Auto-scaling based on demand

## Monitoring & Troubleshooting

### Common Issues

#### 1. Flow Timeout

**Symptom**: Flow execution times out after 30 minutes

**Solution**:
- Increase timeout in flow configuration
- Optimize prompts for shorter responses
- Use parallel processing

#### 2. RAG Context Not Retrieved

**Symptom**: Maturity assessment lacks standards references

**Solution**:
- Verify ChromaDB is running and accessible
- Check knowledge base ingestion (`setup_knowledge.py`)
- Validate RAG tool configuration

#### 3. PDF Generation Fails

**Symptom**: PDF formatter agent errors

**Solution**:
- Ensure WeasyPrint dependencies installed
- Check markdown formatting (valid syntax)
- Verify output path permissions

#### 4. API Key Authentication Failed

**Symptom**: 401/403 errors from Azure AI Foundry

**Solution**:
- Verify API key is correct and not expired
- Check endpoint URL format
- Ensure API key has proper permissions

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Cost Optimization

### Model Selection

| Agent | Model | Avg Tokens/Call | Cost/1M Tokens |
|-------|-------|----------------|----------------|
| Survey Parser | GPT-4o | 3,000 | $5.00 |
| Maturity Assessor | GPT-4o | 6,000 | $5.00 |
| Report Generator | GPT-4o | 12,000 | $5.00 |
| Self-Critic | GPT-4o | 3,000 | $5.00 |
| PDF Formatter | GPT-4o-mini | 1,500 | $0.15 |

**Estimated Cost per Dimension Report**: ~$0.12
**Estimated Cost per Full Survey (8 dims + overall)**: ~$1.00

### Cost Reduction Strategies

1. **Caching**: Implement aggressive caching to avoid re-generation
2. **Model Selection**: Use smaller models where possible
3. **Prompt Optimization**: Reduce prompt verbosity
4. **Batch Processing**: Process multiple surveys in batches

## Next Steps

1. **Deploy to Azure AI Foundry**: Follow steps 1-3 above
2. **Configure Backend Integration**: Set environment variables
3. **Test with Sample Data**: Run integration tests
4. **Monitor and Optimize**: Track metrics and costs
5. **Scale for Production**: Enable parallel processing

## Support & Resources

- **Azure AI Foundry Docs**: https://learn.microsoft.com/azure/ai-studio/
- **Azure AI SDK**: https://pypi.org/project/azure-ai-projects/
- **Prompt Flow**: https://microsoft.github.io/promptflow/
- **Project README**: `azure_ai_foundry/README.md`
- **Architecture**: `azure_ai_foundry/ARCHITECTURE.md`

## Appendix: Quick Reference

### Environment Setup

```bash
# Set environment variables
export AZURE_AI_FOUNDRY_ENDPOINT="https://<project>.api.azureml.ms"
export AZURE_AI_FOUNDRY_API_KEY="<your-api-key>"

# Install dependencies
pip install -r requirements.txt

# Test connection
python -c "
from azure_ai_foundry.config import get_foundry_client
import asyncio

async def test():
    client = get_foundry_client()
    result = await client.test_connection()
    print(result)

asyncio.run(test())
"
```

### Flow Invocation

```python
from azure_ai_foundry.sdk import FlowExecutor
from azure_ai_foundry.config import get_foundry_client

# Initialize
client = get_foundry_client()
executor = FlowExecutor(client)

# Execute dimension analysis
result = await executor.execute_dimension_analysis(
    survey_data=survey_data,
    dimension="Data Privacy & Compliance",
    customer_code="ACME001",
    customer_name="Acme Corp"
)

# Access results
final_report = result["final_report"]
metadata = result["metadata"]
```

---

**Last Updated**: 2025-11-13
**Version**: 1.0.0
