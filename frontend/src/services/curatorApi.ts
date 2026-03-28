import api from './client';

export const curatorApi = {
  evaluateSession: (sessionId: string) => api.post(`/curator/evaluate/${sessionId}`),
  evaluateAll: () => api.post('/curator/evaluate/all'),
  getConfig: () => api.get('/curator/config'),
  updateConfig: (config: any) => api.put('/curator/config', config),
};
