import { useState, useEffect } from 'react';
import { llmAPI } from '../api';

const LLM_PURPOSES = [
  'Default',
  'Orchestrate',
  'Data Privacy & Compliance',
  'Data Quality',
  'Data Governance & Management',
  'Data Security & Access',
  'Data Lineage & Traceability',
  'Metadata & Documentation',
  'Data Value & Lifecycle Management',
  'Data Ethics & Bias'
];

const PROVIDER_TYPES = [
  { value: 'LOCAL', label: 'Local LLM (LM Studio, Ollama, etc.)' },
  { value: 'BEDROCK', label: 'AWS Bedrock' },
  { value: 'AZURE', label: 'Azure OpenAI' }
];

export default function LLMConfig() {
  const [configs, setConfigs] = useState([]);
  const [formData, setFormData] = useState({});
  const [testing, setTesting] = useState({});
  const [statusMessages, setStatusMessages] = useState({});

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      const response = await llmAPI.list();
      const configMap = {};
      response.data.forEach(config => {
        configMap[config.purpose] = config;
      });
      setConfigs(configMap);
      
      const initialFormData = {};
      LLM_PURPOSES.forEach(purpose => {
        initialFormData[purpose] = configMap[purpose] || {
          purpose,
          provider_type: 'LOCAL',
          model_name: 'default',
          api_url: '',
          api_key: '',
          aws_region: '',
          aws_access_key_id: '',
          aws_secret_access_key: '',
          aws_model_id: '',
          azure_endpoint: '',
          azure_api_key: '',
          azure_deployment_name: '',
          azure_api_version: '2024-02-15-preview',
          status: 'Not Tested'
        };
      });
      setFormData(initialFormData);
    } catch (error) {
      console.error('Failed to load LLM configs:', error);
    }
  };

  const handleChange = (purpose, field, value) => {
    setFormData(prev => ({
      ...prev,
      [purpose]: {
        ...prev[purpose],
        [field]: value
      }
    }));
  };

  const validateConfig = (config) => {
    if (config.provider_type === 'LOCAL') {
      if (!config.api_url) return 'Please enter API URL';
    } else if (config.provider_type === 'BEDROCK') {
      if (!config.aws_region) return 'Please enter AWS Region';
      if (!config.aws_access_key_id) return 'Please enter AWS Access Key ID';
      if (!config.aws_secret_access_key) return 'Please enter AWS Secret Access Key';
      if (!config.aws_model_id) return 'Please enter AWS Model ID';
    } else if (config.provider_type === 'AZURE') {
      if (!config.azure_endpoint) return 'Please enter Azure Endpoint';
      if (!config.azure_api_key) return 'Please enter Azure API Key';
      if (!config.azure_deployment_name) return 'Please enter Azure Deployment Name';
    }
    return null;
  };

  const handleTest = async (purpose) => {
    const config = formData[purpose];
    const validationError = validateConfig(config);
    if (validationError) {
      setStatusMessages(prev => ({
        ...prev,
        [purpose]: { type: 'error', message: validationError }
      }));
      return;
    }

    setTesting(prev => ({ ...prev, [purpose]: true }));
    setStatusMessages(prev => ({ ...prev, [purpose]: null }));

    try {
      let configId = config.id;

      if (!configId) {
        const saveResponse = await llmAPI.createOrUpdate(config);
        configId = saveResponse.data.id;
      }

      const testResponse = await llmAPI.test(configId);

      setFormData(prev => ({
        ...prev,
        [purpose]: {
          ...prev[purpose],
          id: configId,
          status: testResponse.data.status
        }
      }));

      const isSuccess = testResponse.data.status === 'Success';
      setStatusMessages(prev => ({
        ...prev,
        [purpose]: {
          type: isSuccess ? 'success' : 'error',
          message: `Test ${testResponse.data.status}`
        }
      }));
    } catch (error) {
      const errorMsg = 'Test Failed: ' + (error.response?.data?.detail || error.message);
      setStatusMessages(prev => ({
        ...prev,
        [purpose]: { type: 'error', message: errorMsg }
      }));
      setFormData(prev => ({
        ...prev,
        [purpose]: {
          ...prev[purpose],
          status: 'Failed'
        }
      }));
    } finally {
      setTesting(prev => ({ ...prev, [purpose]: false }));
    }
  };

  const handleSave = async (purpose) => {
    const config = formData[purpose];
    const validationError = validateConfig(config);
    if (validationError) {
      setStatusMessages(prev => ({
        ...prev,
        [purpose]: { type: 'error', message: validationError }
      }));
      return;
    }

    setStatusMessages(prev => ({ ...prev, [purpose]: null }));

    try {
      const response = await llmAPI.createOrUpdate(config);

      setFormData(prev => ({
        ...prev,
        [purpose]: {
          ...prev[purpose],
          id: response.data.id
        }
      }));

      setStatusMessages(prev => ({
        ...prev,
        [purpose]: { type: 'success', message: 'Saved successfully' }
      }));
    } catch (error) {
      const errorMsg = 'Failed to save: ' + (error.response?.data?.detail || error.message);
      setStatusMessages(prev => ({
        ...prev,
        [purpose]: { type: 'error', message: errorMsg }
      }));
    }
  };

  const renderProviderFields = (purpose, config) => {
    const providerType = config?.provider_type || 'LOCAL';

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        {providerType === 'LOCAL' && (
          <>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">API URL *</label>
              <input
                type="text"
                value={config?.api_url || ''}
                onChange={(e) => handleChange(purpose, 'api_url', e.target.value)}
                placeholder="http://localhost:1234/v1/chat/completions"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Model Name</label>
              <input
                type="text"
                value={config?.model_name || 'default'}
                onChange={(e) => handleChange(purpose, 'model_name', e.target.value)}
                placeholder="default"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key (Optional)</label>
              <input
                type="password"
                value={config?.api_key || ''}
                onChange={(e) => handleChange(purpose, 'api_key', e.target.value)}
                placeholder="Optional"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              />
            </div>
          </>
        )}

        {providerType === 'BEDROCK' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">AWS Region *</label>
              <input
                type="text"
                value={config?.aws_region || ''}
                onChange={(e) => handleChange(purpose, 'aws_region', e.target.value)}
                placeholder="us-east-1"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Model ID *</label>
              <input
                type="text"
                value={config?.aws_model_id || ''}
                onChange={(e) => handleChange(purpose, 'aws_model_id', e.target.value)}
                placeholder="anthropic.claude-v2"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">AWS Access Key ID *</label>
              <input
                type="password"
                value={config?.aws_access_key_id || ''}
                onChange={(e) => handleChange(purpose, 'aws_access_key_id', e.target.value)}
                placeholder="AKIAIOSFODNN7EXAMPLE"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">AWS Secret Access Key *</label>
              <input
                type="password"
                value={config?.aws_secret_access_key || ''}
                onChange={(e) => handleChange(purpose, 'aws_secret_access_key', e.target.value)}
                placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              />
            </div>
          </>
        )}

        {providerType === 'AZURE' && (
          <>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Azure Endpoint *</label>
              <input
                type="text"
                value={config?.azure_endpoint || ''}
                onChange={(e) => handleChange(purpose, 'azure_endpoint', e.target.value)}
                placeholder="https://your-resource.openai.azure.com"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Deployment Name *</label>
              <input
                type="text"
                value={config?.azure_deployment_name || ''}
                onChange={(e) => handleChange(purpose, 'azure_deployment_name', e.target.value)}
                placeholder="my-gpt-4-deployment"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key *</label>
              <input
                type="password"
                value={config?.azure_api_key || ''}
                onChange={(e) => handleChange(purpose, 'azure_api_key', e.target.value)}
                placeholder="Your Azure API Key"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Version</label>
              <input
                type="text"
                value={config?.azure_api_version || '2024-02-15-preview'}
                onChange={(e) => handleChange(purpose, 'azure_api_version', e.target.value)}
                placeholder="2024-02-15-preview"
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              />
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">LLM Configuration</h1>

      <div className="bg-blue-50 p-4 rounded mb-6">
        <p className="text-sm text-blue-900">
          Configure LLM providers for generating summaries and suggestions in reports.
          Support for Local LLMs (LM Studio, Ollama), AWS Bedrock, and Azure OpenAI.
        </p>
      </div>

      <div className="space-y-6">
        {LLM_PURPOSES.map(purpose => (
          <div key={purpose} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{purpose}</h3>
              <span className={`px-3 py-1 rounded text-sm font-medium ${
                formData[purpose]?.status === 'Success' ? 'bg-green-100 text-green-800' :
                formData[purpose]?.status === 'Failed' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {formData[purpose]?.status || 'Not Tested'}
              </span>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Provider Type</label>
              <select
                value={formData[purpose]?.provider_type || 'LOCAL'}
                onChange={(e) => handleChange(purpose, 'provider_type', e.target.value)}
                className="w-full md:w-1/2 px-3 py-2 border rounded focus:ring-2 focus:ring-encora-green"
              >
                {PROVIDER_TYPES.map(provider => (
                  <option key={provider.value} value={provider.value}>
                    {provider.label}
                  </option>
                ))}
              </select>
            </div>

            {renderProviderFields(purpose, formData[purpose])}

            <div className="flex items-center gap-3 mt-6">
              <button
                onClick={() => handleTest(purpose)}
                disabled={testing[purpose]}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
              >
                {testing[purpose] ? 'Testing...' : 'Test Connection'}
              </button>
              <button
                onClick={() => handleSave(purpose)}
                className="px-4 py-2 bg-encora-green text-white rounded hover:bg-green-600"
              >
                Save Configuration
              </button>
              {statusMessages[purpose] && (
                <div className={`flex items-center gap-2 px-4 py-2 rounded ${
                  statusMessages[purpose].type === 'success'
                    ? 'bg-green-50 text-green-800 border border-green-200'
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}>
                  {statusMessages[purpose].type === 'success' ? (
                    <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  )}
                  <span className="text-sm font-medium">{statusMessages[purpose].message}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}