import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
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