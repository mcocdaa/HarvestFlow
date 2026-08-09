import api from './client';

export const sessionApi = {
  getSessions: (params?: { status?: string; page?: number; page_size?: number; sort?: string }) =>
    api.get('/sessions', { params }),
  getSessionContent: (sessionId: string) => api.get(`/sessions/${sessionId}/content`),
};
