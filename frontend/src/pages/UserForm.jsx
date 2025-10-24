import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { userAPI, customerAPI } from '../api';

export default function UserForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [customers, setCustomers] = useState([]);
  const [formData, setFormData] = useState({
    user_id: '',
    username: '',
    password: '',
    user_type: 'Participant',
    customer_id: ''
  });

  useEffect(() => {
    loadCustomers();
    if (id) {
      loadUser();
    }
  }, [id]);

  const loadCustomers = async () => {
    try {
      const response = await customerAPI.list();
      setCustomers(response.data);
    } catch (error) {
      console.error('Failed to load customers:', error);
    }
  };

  const loadUser = async () => {
    try {
      const response = await userAPI.get(id);
      setFormData({
        user_id: response.data.user_id,
        username: response.data.username,
        password: '',
        user_type: response.data.user_type,
        customer_id: response.data.customer_id || ''
      });
    } catch (error) {
      console.error('Failed to load user:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const data = { ...formData };
    if (data.user_type === 'Sales' || data.user_type === 'SystemAdmin') {
      data.customer_id = null;
    }
    
    if (id && !data.password) {
      delete data.password;
    }

    try {
      if (id) {
        await userAPI.update(id, data);
      } else {
        await userAPI.create(data);
      }
      navigate('/users');
    } catch (error) {
      alert('Failed to save user: ' + (error.response?.data?.detail || error.message));
    }
  };

  const needsCustomer = formData.user_type === 'CXO' || formData.user_type === 'Participant';

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl font-bold mb-6">{id ? 'Edit' : 'Add'} User</h1>
      
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            User ID *
          </label>
          <input
            type="text"
            value={formData.user_id}
            onChange={(e) => setFormData({...formData, user_id: e.target.value})}
            className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-encora-green focus:border-transparent"
            required
            disabled={!!id}
          />
          {id && (
            <p className="text-xs text-gray-500 mt-1">User ID cannot be changed</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Name *
          </label>
          <input
            type="text"
            value={formData.username}
            onChange={(e) => setFormData({...formData, username: e.target.value})}
            className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-encora-green focus:border-transparent"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Password {id ? '(leave blank to keep current)' : '*'}
          </label>
          <input
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-encora-green focus:border-transparent"
            required={!id}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            User Type *
          </label>
          <select
            value={formData.user_type}
            onChange={(e) => setFormData({...formData, user_type: e.target.value, customer_id: ''})}
            className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-encora-green focus:border-transparent"
            required
          >
            <option value="CXO">CXO</option>
            <option value="Participant">Participant</option>
            <option value="Sales">Sales</option>
          </select>
        </div>

        {needsCustomer && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Customer *
            </label>
            <select
              value={formData.customer_id}
              onChange={(e) => setFormData({...formData, customer_id: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-encora-green focus:border-transparent"
              required={needsCustomer}
            >
              <option value="">Select Customer</option>
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>
                  {customer.name} ({customer.customer_code})
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex space-x-4">
          <button 
            type="submit" 
            className="px-6 py-2 bg-encora-green text-white rounded hover:bg-green-600"
          >
            Save
          </button>
          <button 
            type="button" 
            onClick={() => navigate('/users')} 
            className="px-6 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}