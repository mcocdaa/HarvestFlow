import api from './client';
import type { ExportParams } from '../types/export';

export const exporterApi = {
  exportSessions: (data: ExportParams) => api.post('/exporter/export', data),
  getHistory: (limit?: number) => api.get('/exporter/history', { params: { limit } }),
  getFormats: () => api.get('/exporter/formats'),
};
