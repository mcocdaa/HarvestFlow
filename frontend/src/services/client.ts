import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
});

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
