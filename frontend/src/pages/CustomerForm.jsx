import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { customerAPI } from '../api';

export default function CustomerForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    customer_code: '',
    industry: '',
    location: '',
    description: ''
  });

  useEffect(() => {
    if (id) {
      loadCustomer();
    }
  }, [id]);

  const loadCustomer = async () => {
    try {
      const response = await customerAPI.get(id);
      setFormData(response.data);
    } catch (error) {
      console.error('Failed to load customer:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (id) {
        await customerAPI.update(id, formData);
      } else {
        await customerAPI.create(formData);
      }
      navigate('/customers');
    } catch (error) {
      alert('Failed to save customer: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl font-bold mb-6">{id ? 'Edit' : 'Add'} Customer</h1>
      
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Name *
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-encora-green focus:border-transparent"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Customer Code *
          </label>
          <input
            type="text"
            value={formData.customer_code}
            onChange={(e) => setFormData({...formData, customer_code: e.target.value})}
            className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-encora-green focus:border-transparent"
            required
            disabled={!!id}
          />
          {id && (
            <p className="text-xs text-gray-500 mt-1">Customer code cannot be changed</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Industry
          </label>
          <input
            type="text"
            value={formData.industry}
            onChange={(e) => setFormData({...formData, industry: e.target.value})}
            className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-encora-green focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Location
          </label>
          <input
            type="text"
            value={formData.location}
            onChange={(e) => setFormData({...formData, location: e.target.value})}
            className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-encora-green focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-encora-green focus:border-transparent"
            rows="4"
          />
        </div>

        <div className="flex space-x-4">
          <button 
            type="submit" 
            className="px-6 py-2 bg-encora-green text-white rounded hover:bg-green-600"
          >
            Save
          </button>
          <button 
            type="button" 
            onClick={() => navigate('/customers')} 
            className="px-6 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}