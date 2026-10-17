import axios from 'axios';
import { message } from 'antd';
import { getStoredLocale } from '../i18n';

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
    const isZh = getStoredLocale() === 'zh';
    const status = error.response?.status;
    const detail = error.response?.data?.detail;
    let text: string;
    if (Array.isArray(detail)) {
      // Pydantic validation errors return a list of objects
      text = detail.map((item) => (typeof item === 'string' ? item : item?.msg ?? JSON.stringify(item))).join('; ');
    } else if (typeof detail === 'string') {
      text = detail;
    } else if (typeof error.response?.data?.message === 'string' && error.response.data.message) {
      // 部分端点失败时返回 {success: false, message}
      text = error.response.data.message;
    } else if (status === 401) {
      text = isZh ? '认证失败' : 'Authentication failed';
    } else if (status === 404) {
      text = isZh ? '请求的资源不存在' : 'Requested resource not found';
    } else {
      text = isZh ? '请求失败' : 'Request failed';
    }
    if (text) {
      message.error(text);
    }
    return Promise.reject(error);
  }
);

export default api;
