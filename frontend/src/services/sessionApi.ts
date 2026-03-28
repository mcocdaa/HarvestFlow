import api from './client';

export const sessionApi = {
  getSessions: (params?: { status?: string; page?: number; page_size?: number; sort?: string }) =>
    api.get('/sessions', { params }),
  getSession: (sessionId: string) => api.get(`/sessions/${sessionId}`),
  getSessionContent: (sessionId: string) => api.get(`/sessions/${sessionId}/content`),
  createSession: (session: any) => api.post('/sessions', session),
  updateSession: (sessionId: string, updates: any) => api.put(`/sessions/${sessionId}`, updates),
  deleteSession: (sessionId: string) => api.delete(`/sessions/${sessionId}`),
};
