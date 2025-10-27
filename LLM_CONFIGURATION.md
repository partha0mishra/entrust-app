# Multi-Provider LLM Configuration Guide

The EnTrust application now supports multiple LLM providers, allowing system administrators to configure different AI models for each dimension, orchestrator, and default purposes.

## Supported Providers

### 1. Local LLMs (LM Studio, Ollama, etc.)
- **Use Case**: Run models locally for data privacy and cost savings
- **Examples**: LM Studio, Ollama, LocalAI, or any OpenAI-compatible local server
- **Requirements**:
  - API endpoint URL
  - Optional API key (if your local server requires authentication)
  - Model name

### 2. AWS Bedrock
- **Use Case**: Enterprise-grade AI with AWS infrastructure
- **Supported Models**:
  - Anthropic Claude (claude-v2, claude-instant-v1)
  - Amazon Titan
  - AI21 Jurassic
- **Requirements**:
  - AWS Region (e.g., us-east-1)
  - AWS Access Key ID
  - AWS Secret Access Key
  - Model ID (e.g., anthropic.claude-v2)

### 3. Azure OpenAI
- **Use Case**: Microsoft Azure-hosted OpenAI models
- **Supported Models**: GPT-3.5, GPT-4, and other Azure OpenAI deployments
- **Requirements**:
  - Azure Endpoint URL
  - Azure API Key
  - Deployment Name
  - API Version (default: 2024-02-15-preview)

## Configuration Purposes

The system supports configuring different LLM providers for each of the following purposes:

1. **Default** - Fallback LLM for any dimension without specific configuration
2. **Orchestrate** - Generates overall executive summaries from all dimension summaries
3. **Data Privacy & Compliance** - Analyzes privacy and compliance survey responses
4. **Data Quality** - Analyzes data quality metrics and feedback
5. **Data Governance & Management** - Evaluates governance policies and practices
6. **Data Security & Access** - Reviews security controls and access management
7. **Data Lineage & Traceability** - Assesses data lineage tracking
8. **Metadata & Documentation** - Analyzes metadata completeness
9. **Data Value & Lifecycle Management** - Evaluates data lifecycle processes
10. **Data Ethics & Bias** - Reviews ethical considerations and bias detection

## Setup Instructions

### Step 1: Run Database Migration

Before using the new multi-provider features, run the database migration:

```bash
cd backend
python migrate_llm_providers.py
```

This will add the necessary columns to support multiple providers.

### Step 2: Install Dependencies

Install the required packages for AWS and Azure support:

```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Configure Providers via UI

1. Log in as a System Administrator
2. Navigate to **LLM Configuration** page
3. For each purpose (Default, Orchestrate, dimensions):
   - Select the **Provider Type** from the dropdown
   - Fill in the required fields for that provider
   - Click **Test Connection** to verify the configuration
   - Click **Save Configuration** to persist the settings

## Provider-Specific Configuration Examples

### Local LLM (LM Studio)

```
Provider Type: Local LLM
API URL: http://localhost:1234/v1/chat/completions
Model Name: neural-chat (or your loaded model name)
API Key: (leave empty if not required)
```

### AWS Bedrock (Claude)

```
Provider Type: AWS Bedrock
AWS Region: us-east-1
Model ID: anthropic.claude-v2
AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### Azure OpenAI

```
Provider Type: Azure OpenAI
Azure Endpoint: https://your-resource.openai.azure.com
Deployment Name: my-gpt-4-deployment
API Key: your-azure-api-key
API Version: 2024-02-15-preview
```

## Best Practices

### 1. Use Different Providers for Different Purposes

Example configuration strategy:
- **Default & Orchestrate**: Use Azure OpenAI GPT-4 for high-quality executive summaries
- **Dimension-Specific**: Use local LLMs for privacy-sensitive dimensions (Data Privacy, Data Security)
- **Cost Optimization**: Use AWS Bedrock Claude Instant for less critical dimensions

### 2. Security Considerations

- **API Keys**: All API keys and secrets are stored in the database. Consider using environment variables or secret management services for production.
- **Local LLMs**: For sensitive data, use local LLMs to ensure data never leaves your infrastructure.
- **AWS IAM**: Use AWS IAM roles instead of access keys when running on EC2 instances.
- **Azure Managed Identity**: Use Azure Managed Identity when running on Azure VMs.

### 3. Testing

Always test each configuration after saving:
1. Click **Test Connection** button
2. Verify the status shows "Success"
3. Only configurations with "Success" status will be used for report generation

### 4. Fallback Behavior

- If a dimension-specific LLM is not configured, the system falls back to the **Default** configuration
- If the **Orchestrate** LLM is not configured, it also falls back to **Default**
- If no LLM is configured or all tests fail, reports will be generated without AI summaries

## Troubleshooting

### Local LLM Connection Failed

- Verify LM Studio or your local LLM server is running
- Check the port number in the API URL
- Ensure the model is loaded in LM Studio
- Try accessing the URL in your browser or with curl

### AWS Bedrock Access Denied

- Verify your AWS credentials have bedrock:InvokeModel permission
- Check that the region matches your Bedrock model availability
- Ensure the model ID is correct (e.g., anthropic.claude-v2)

### Azure OpenAI Rate Limit

- Check your Azure OpenAI quota and rate limits
- Verify the deployment name matches your Azure resource
- Ensure the API version is compatible with your deployment

## Architecture

The multi-provider architecture uses a factory pattern:

```
Frontend (LLMConfig.jsx)
    ↓
API Router (llm_config.py)
    ↓
LLM Service (llm_service.py)
    ↓
Provider Factory (llm_providers.py)
    ↓
├─ LocalLLMProvider (OpenAI-compatible)
├─ AWSBedrockProvider (boto3)
└─ AzureOpenAIProvider (httpx)
```

Each provider implements a common interface:
- `test_connection()`: Verifies connectivity and credentials
- `call_llm(messages, max_tokens)`: Sends requests and returns responses

## API Endpoints

- `POST /api/llm-config/` - Create or update LLM configuration
- `GET /api/llm-config/` - List all LLM configurations
- `POST /api/llm-config/{config_id}/test` - Test a specific configuration

## Environment Variables (Optional)

For production deployments, you can set default values using environment variables:

```bash
# AWS Bedrock
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-key

# Azure OpenAI
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_API_KEY=your-api-key
```

## Cost Considerations

| Provider | Cost Model | Typical Cost (per 1M tokens) |
|----------|------------|-------------------------------|
| Local LLM | Hardware + Electricity | ~$0 (after initial setup) |
| AWS Bedrock Claude | Pay per token | $8-$24 (varies by model) |
| Azure OpenAI GPT-4 | Pay per token | $30-$60 (varies by model) |

**Recommendation**: Use local LLMs for high-volume, less critical summaries, and cloud providers for executive-level orchestration.

## Support

For issues or questions:
1. Check the application logs in `backend/logs/`
2. Verify your configuration in the LLM Configuration page
3. Test the provider connection using the Test button
4. Review this documentation for troubleshooting steps
