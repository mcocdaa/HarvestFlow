import api from './client';

export const exporterApi = {
  exportSessions: (data: any) => api.post('/export', data),
  getHistory: (limit?: number) => api.get('/export/history', { params: { limit } }),
  getFormats: () => api.get('/export/formats'),
};
