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

export default function LLMConfig() {
  const [configs, setConfigs] = useState([]);
  const [formData, setFormData] = useState({});
  const [testing, setTesting] = useState({});

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
          api_url: '',
          api_key: '',
          model_name: 'default',  // ADD THIS
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

  const handleTest = async (purpose) => {
    const config = formData[purpose];
    if (!config.api_url) {
      alert('Please enter API URL first');
      return;
    }

    setTesting(prev => ({ ...prev, [purpose]: true }));

    try {
      let configId = config.id;
      
      if (!configId) {
        const saveResponse = await llmAPI.createOrUpdate({
          purpose: config.purpose,
          api_url: config.api_url,
          api_key: config.api_key || null,
          model_name: config.model_name || 'default'  // ADD THIS
        });
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

      alert(`Test ${testResponse.data.status}`);
    } catch (error) {
      alert('Test Failed: ' + (error.response?.data?.detail || error.message));
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
    if (!config.api_url) {
      alert('Please enter API URL');
      return;
    }

    try {
      const response = await llmAPI.createOrUpdate({
        purpose: config.purpose,
        api_url: config.api_url,
        api_key: config.api_key || null,
        model_name: config.model_name || 'default'  // ADD THIS
      });

      setFormData(prev => ({
        ...prev,
        [purpose]: {
          ...prev[purpose],
          id: response.data.id
        }
      }));

      alert('Saved successfully');
    } catch (error) {
      alert('Failed to save: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">LLM Configuration</h1>
      
      <div className="bg-blue-50 p-4 rounded mb-6">
        <p className="text-sm text-blue-900">
          Configure LLM endpoints for generating summaries and suggestions in reports.
          Use OpenAI-compatible API format (e.g., LM Studio local endpoints).
        </p>
      </div>

      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Purpose</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">API URL</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">API Key</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Test</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Save</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {LLM_PURPOSES.map(purpose => (
              <tr key={purpose}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  {purpose}
                </td>
                <td className="px-6 py-4">
                  <input
                    type="text"
                    value={formData[purpose]?.api_url || ''}
                    onChange={(e) => handleChange(purpose, 'api_url', e.target.value)}
                    placeholder="http://localhost:1234/v1/chat/completions"
                    className="w-full px-3 py-1 text-sm border rounded focus:ring-2 focus:ring-encora-green"
                  />
                </td>
                <td className="px-6 py-4">
                  <input
                    type="text"
                    value={formData[purpose]?.model_name || 'default'}
                    onChange={(e) => handleChange(purpose, 'model_name', e.target.value)}
                    placeholder="default"
                    className="w-full px-3 py-1 text-sm border rounded focus:ring-2 focus:ring-encora-green"
                  />
                </td>
                <td className="px-6 py-4">
                  <input
                    type="password"
                    value={formData[purpose]?.api_key || ''}
                    onChange={(e) => handleChange(purpose, 'api_key', e.target.value)}
                    placeholder="Optional"
                    className="w-full px-3 py-1 text-sm border rounded focus:ring-2 focus:ring-encora-green"
                  />
                </td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => handleTest(purpose)}
                    disabled={testing[purpose]}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    {testing[purpose] ? 'Testing...' : 'Test'}
                  </button>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`px-2 py-1 rounded text-xs ${
                    formData[purpose]?.status === 'Success' ? 'bg-green-100 text-green-800' :
                    formData[purpose]?.status === 'Failed' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {formData[purpose]?.status || 'Not Tested'}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => handleSave(purpose)}
                    className="px-3 py-1 text-sm bg-encora-green text-white rounded hover:bg-green-600"
                  >
                    Save
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}