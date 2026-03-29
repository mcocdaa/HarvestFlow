import api from './client';

export const exporterApi = {
  exportSessions: (data: any) => api.post('/exporter/export', data),
  getHistory: (limit?: number) => api.get('/exporter/history', { params: { limit } }),
  getFormats: () => api.get('/exporter/formats'),
};
