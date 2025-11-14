import axios from 'axios';

// Get API URL from environment variable (replaced at build time by Vite)
const getApiUrl = () => {
  let apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  
  // Force HTTPS in production if we're on HTTPS
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    // If API_URL is HTTP but we're on HTTPS, convert to HTTPS
    if (apiUrl.startsWith('http://')) {
      apiUrl = apiUrl.replace('http://', 'https://');
    }
    // If no API_URL is set and we're in production, use the Azure backend
    if (apiUrl === 'http://localhost:8000') {
      apiUrl = 'https://entrust-backend.calmbay-c64e42cc.eastus.azurecontainerapps.io';
    }
  }
  
  return apiUrl;
};

// Get the API URL (this runs at module load time, but we'll also check in interceptors)
const API_URL = getApiUrl();

// Debug logging
if (typeof window !== 'undefined') {
  console.log('API_URL:', API_URL);
  console.log('VITE_API_URL env:', import.meta.env.VITE_API_URL);
  console.log('Window protocol:', window.location.protocol);
}

const api = axios.create({
  baseURL: `${API_URL}/api`,
  // Force using the XHR adapter with HTTPS
  adapter: 'xhr',
});

// Add request interceptor to ensure HTTPS is always used
api.interceptors.request.use((config) => {
  console.log('🔍 Request interceptor - Before:', {
    baseURL: config.baseURL,
    url: config.url
  });
  
  // Force HTTPS by constructing the full absolute URL
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    try {
      // Manually construct the full URL to preserve the path
      let fullUrl;
      if (config.url.startsWith('http://') || config.url.startsWith('https://')) {
        // URL is already absolute
        fullUrl = new URL(config.url);
      } else {
        // Relative URL - append to baseURL
        const base = config.baseURL.endsWith('/') ? config.baseURL.slice(0, -1) : config.baseURL;
        const path = config.url.startsWith('/') ? config.url : '/' + config.url;
        fullUrl = new URL(base + path);
      }
      
      console.log('🔧 Constructed URL:', fullUrl.href);
      
      // Force HTTPS protocol
      if (fullUrl.protocol === 'http:') {
        console.warn('⚠️ Converting protocol from HTTP to HTTPS');
        fullUrl.protocol = 'https:';
      }
      
      // Remove any trailing slashes to prevent axios from adding them
      let finalUrl = fullUrl.href;
      if (finalUrl.endsWith('/') && !finalUrl.endsWith('://')) {
        finalUrl = finalUrl.slice(0, -1);
      }
      
      // Set the complete URL and clear baseURL to prevent axios from reconstructing
      config.url = finalUrl;
      config.baseURL = '';  // Empty string instead of undefined
      
      // Also explicitly set the adapter and method
      config.adapter = 'xhr';
      config.method = config.method || 'get';
      
      // Force HTTPS in headers as well
      config.headers = config.headers || {};
      config.headers['X-Requested-With'] = 'XMLHttpRequest';
      
      console.log('✅ Final URL:', config.url);
      console.log('✅ Config method:', config.method);
      console.log('✅ Config adapter:', config.adapter);
      console.log('✅ Full config:', JSON.stringify({
        url: config.url,
        baseURL: config.baseURL,
        method: config.method
      }));
    } catch (e) {
      console.error('❌ Error constructing URL:', e);
    }
  }
  
  // Add authorization token
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
}, (error) => {
  console.error('❌ Request interceptor error:', error);
  return Promise.reject(error);
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (user_id, password) => 
    api.post('/auth/login', null, { params: { user_id, password } }),
  getCurrentUser: () => api.get('/auth/me'),
};

export const customerAPI = {
  list: () => api.get('/customers'),
  get: (id) => api.get(`/customers/${id}`),
  create: (data) => api.post('/customers', data),
  update: (id, data) => api.put(`/customers/${id}`, data),
  delete: (id) => api.delete(`/customers/${id}`),
};

export const userAPI = {
  list: () => api.get('/users'),
  get: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
};

export const llmAPI = {
  list: () => api.get('/llm-config'),
  createOrUpdate: (data) => api.post('/llm-config', data),
  test: (id) => api.post(`/llm-config/${id}/test`),
};

export const surveyAPI = {
  getQuestions: () => api.get('/survey/questions'),
  getDimensions: () => api.get('/survey/dimensions'),
  getProgress: () => api.get('/survey/progress'),
  getQuestionsByDimension: (dimension) => api.get(`/survey/questions/${dimension}`),
  getResponses: (dimension) => api.get(`/survey/responses/${dimension}`),
  saveResponse: (data) => api.post('/survey/responses', data),
  submit: () => api.post('/survey/submit'),
  getStatus: () => api.get('/survey/status'),
};

export const reportAPI = {
  getCustomers: () => api.get('/reports/customers'),
  getDimensions: (customerId) => api.get(`/reports/customer/${customerId}/dimensions`),
  getDimensionReport: (customerId, dimension, forceRegenerate = false) =>
    api.get(`/reports/customer/${customerId}/dimension/${dimension}`, {
      params: { force_regenerate: forceRegenerate }
    }),
  getOverallReport: (customerId, forceRegenerate = false) =>
    api.get(`/reports/customer/${customerId}/overall`, {
      params: { force_regenerate: forceRegenerate }
    }),
  downloadDimensionPDF: (customerId, dimension) =>
    api.get(`/reports/customer/${customerId}/dimension/${dimension}/download`, {
      responseType: 'blob'
    }),
  downloadOverallPDF: (customerId) =>
    api.get(`/reports/customer/${customerId}/overall/download`, {
      responseType: 'blob'
    }),
};

export default api;