import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

export const sessionApi = {
  getSessions: (params?: { status?: string; page?: number; page_size?: number; sort?: string }) =>
    api.get('/sessions', { params }),
  getSession: (sessionId: string) => api.get(`/sessions/${sessionId}`),
  getSessionContent: (sessionId: string) => api.get(`/sessions/${sessionId}/content`),
  createSession: (session: any) => api.post('/sessions', session),
  updateSession: (sessionId: string, updates: any) => api.put(`/sessions/${sessionId}`, updates),
  deleteSession: (sessionId: string) => api.delete(`/sessions/${sessionId}`),
};

export const collectorApi = {
  scanFolder: (folderPath?: string) => api.post('/collector/scan', null, { params: { folder_path: folderPath } }),
  importSession: (filePath: string) => api.post('/collector/import', null, { params: { file_path: filePath } }),
  importAll: (folderPath?: string) => api.post('/collector/import/all', null, { params: { folder_path: folderPath } }),
  getConfig: () => api.get('/collector/config'),
  addWatchFolder: (folderPath: string) => api.post('/collector/config/add-folder', null, { params: { folder_path: folderPath } }),
};

export const curatorApi = {
  evaluateSession: (sessionId: string) => api.post(`/curator/evaluate/${sessionId}`),
  evaluateAll: () => api.post('/curator/evaluate/all'),
  getConfig: () => api.get('/curator/config'),
  updateConfig: (config: any) => api.put('/curator/config', config),
};

export const reviewerApi = {
  approveSession: (sessionId: string, notes?: string) => api.post(`/reviewer/approve/${sessionId}`, null, { params: { notes } }),
  rejectSession: (sessionId: string, notes?: string) => api.post(`/reviewer/reject/${sessionId}`, null, { params: { notes } }),
  updateSession: (sessionId: string, updates: any) => api.put(`/reviewer/update/${sessionId}`, updates),
  batchApprove: (sessionIds: string[]) => api.post('/reviewer/batch-approve', { session_ids: sessionIds }),
  batchReject: (sessionIds: string[]) => api.post('/reviewer/batch-reject', { session_ids: sessionIds }),
  getPending: (page?: number, pageSize?: number) => api.get('/reviewer/pending', { params: { page, page_size: pageSize } }),
  getAuditLogs: (sessionId?: string) => api.get('/reviewer/logs', { params: { session_id: sessionId } }),
};

export const exporterApi = {
  exportSessions: (data: any) => api.post('/export', data),
  getHistory: (limit?: number) => api.get('/export/history', { params: { limit } }),
  getFormats: () => api.get('/export/formats'),
};

export const pluginApi = {
  getAll: () => api.get('/plugins'),
  getByType: (pluginType: string) => api.get(`/plugins/${pluginType}`),
  getDetails: (pluginType: string, pluginName: string) => api.get(`/plugins/${pluginType}/${pluginName}`),
  getFrontend: (pluginType: string, pluginName: string) => api.get(`/plugins/${pluginType}/${pluginName}/frontend`),
  enable: (pluginName: string) => api.post(`/plugins/${pluginName}/enable`),
  disable: (pluginName: string) => api.post(`/plugins/${pluginName}/disable`),
};

export const statsApi = {
  get: () => api.get('/stats'),
};

export default api;
