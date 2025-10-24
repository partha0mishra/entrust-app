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
  const [configs, setConfigs] = useState({});
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
          model_name: 'default',
          status: 'Not Tested'
        };
      });
      setFormData(initialFormData);
    } catch (error) {
      console.error('Failed to load LLM configs:', error);
    }
  };

  const handleChange = (purpose, field, value) => {
    console.log(`Changing ${purpose}.${field} to:`, value);
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

    console.log('Testing config:', config);

    setTesting(prev => ({ ...prev, [purpose]: true }));

    try {
      let configId = config.id;
      
      if (!configId) {
        console.log('Saving config first...');
        const saveResponse = await llmAPI.createOrUpdate({
          purpose: config.purpose,
          api_url: config.api_url,
          api_key: config.api_key || null,
          model_name: config.model_name || 'default'
        });
        configId = saveResponse.data.id;
        console.log('Saved with ID:', configId);
      }

      console.log('Testing config ID:', configId);
      const testResponse = await llmAPI.test(configId);
      console.log('Test response:', testResponse.data);
      
      setFormData(prev => ({
        ...prev,
        [purpose]: {
          ...prev[purpose],
          id: configId,
          status: testResponse.data.status
        }
      }));

      // alert(`Test ${testResponse.data.status}${testResponse.data.error ? ': ' + testResponse.data.error : ''}`);
    } catch (error) {
      console.error('Test failed:', error);
      // alert('Test Failed: ' + (error.response?.data?.detail || error.message));
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

    console.log('Saving config:', config);

    try {
      const response = await llmAPI.createOrUpdate({
        purpose: config.purpose,
        api_url: config.api_url,
        api_key: config.api_key || null,
        model_name: config.model_name || 'default'
      });

      console.log('Save response:', response.data);

      setFormData(prev => ({
        ...prev,
        [purpose]: {
          ...prev[purpose],
          id: response.data.id
        }
      }));

      // alert('Saved successfully');
      loadConfigs();
    } catch (error) {
      console.error('Save failed:', error);
      alert('Failed to save: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">LLM Configuration</h1>
      
      <div className="bg-blue-50 p-4 rounded mb-6">
        <p className="text-sm text-blue-900 mb-2">
          Configure LLM endpoints for generating summaries and suggestions in reports.
        </p>
        <p className="text-sm text-blue-900 mb-1">
          <strong>API URL:</strong> <code className="bg-blue-200 px-2 py-1 rounded text-xs">http://host.docker.internal:1234/v1/chat/completions</code>
        </p>
        <p className="text-sm text-blue-900">
          <strong>Model Name:</strong> Leave as "default" or specify (e.g., mistral, llama2)
        </p>
      </div>

      <div className="space-y-4">
        {LLM_PURPOSES.map(purpose => (
          <div key={purpose} className="bg-white rounded-lg shadow p-4">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
              {/* Purpose - spans 2 columns on large screens */}
              <div className="lg:col-span-2">
                <label className="block text-xs font-medium text-gray-500 mb-1">Purpose</label>
                <div className="text-sm font-semibold text-gray-900">{purpose}</div>
              </div>

              {/* API URL - spans 4 columns */}
              <div className="lg:col-span-4">
                <label className="block text-xs font-medium text-gray-500 mb-1">API URL</label>
                <input
                  type="text"
                  value={formData[purpose]?.api_url || ''}
                  onChange={(e) => handleChange(purpose, 'api_url', e.target.value)}
                  placeholder="http://host.docker.internal:1234/..."
                  className="w-full px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-encora-green"
                />
              </div>

              {/* Model Name - spans 2 columns */}
              <div className="lg:col-span-2">
                <label className="block text-xs font-medium text-gray-500 mb-1">Model</label>
                <input
                  type="text"
                  value={formData[purpose]?.model_name || ''}
                  onChange={(e) => handleChange(purpose, 'model_name', e.target.value)}
                  placeholder="default"
                  className="w-full px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-encora-green"
                />
              </div>

              {/* API Key - spans 2 columns */}
              <div className="lg:col-span-2">
                <label className="block text-xs font-medium text-gray-500 mb-1">API Key</label>
                <input
                  type="password"
                  value={formData[purpose]?.api_key || ''}
                  onChange={(e) => handleChange(purpose, 'api_key', e.target.value)}
                  placeholder="Optional"
                  className="w-full px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-encora-green"
                />
              </div>

              {/* Actions - spans 2 columns */}
              <div className="lg:col-span-2 flex flex-col gap-2">
                <label className="block text-xs font-medium text-gray-500 mb-1">Actions</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleTest(purpose)}
                    disabled={testing[purpose]}
                    className="flex-1 px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    {testing[purpose] ? 'Testing...' : 'Test'}
                  </button>
                  <button
                    onClick={() => handleSave(purpose)}
                    className="flex-1 px-3 py-1 text-xs bg-encora-green text-white rounded hover:bg-green-600"
                  >
                    Save
                  </button>
                </div>
                <div>
                  <span className={`inline-block px-2 py-1 rounded text-xs ${
                    formData[purpose]?.status === 'Success' ? 'bg-green-100 text-green-800' :
                    formData[purpose]?.status === 'Failed' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {formData[purpose]?.status || 'Not Tested'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 bg-yellow-50 p-4 rounded">
        <h3 className="font-bold text-sm mb-2">Tips</h3>
        <ul className="text-xs text-gray-700 list-disc list-inside space-y-1">
          <li>Use the same API URL for all purposes if using one LM Studio instance</li>
          <li>Different Model Names allow different models per purpose (if supported by your LLM server)</li>
          <li>Leave Model Name as "default" to use the currently loaded model</li>
          <li>Click "Save" before "Test" to ensure configuration is stored</li>
        </ul>
      </div>
    </div>
  );
}