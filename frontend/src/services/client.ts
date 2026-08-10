import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const API_KEY = import.meta.env.VITE_API_KEY || '';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
});

// Add API key header if configured
api.interceptors.request.use((config) => {
  if (API_KEY) {
    config.headers.Authorization = `Bearer ${API_KEY}`;
  }
  return config;
});

// Response error interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail;
    if (detail) {
      // Use dynamic import to avoid circular dependency on antd message
      import('antd').then(({ message }) => message.error(detail));
    }
    return Promise.reject(error);
  }
);

export default api;
