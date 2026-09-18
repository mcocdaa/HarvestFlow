import api from './client';
import type { ExportParams } from '../types/export';

export const exporterApi = {
  exportSessions: (data: ExportParams) => api.post('/exporter/export', data),
  getHistory: (limit?: number) => api.get('/exporter/history', { params: { limit } }),
  getFormats: () => api.get('/exporter/formats'),
  downloadExport: (filename: string) =>
    api.get('/exporter/download', { params: { filename }, responseType: 'blob' }),
  downloadZip: (filenames: string[]) =>
    api.post('/exporter/download-zip', { filenames }, { responseType: 'blob' }),
};
