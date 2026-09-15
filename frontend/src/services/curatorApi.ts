import api from './client';

export const curatorApi = {
  evaluate: (sessionId: string) => api.post(`/curator/evaluate/${sessionId}`),
  evaluateAll: () => api.post('/curator/evaluate-all'),
  getStatus: () => api.get('/curator/status'),
};
