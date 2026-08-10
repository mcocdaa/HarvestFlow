import api from './client';
import type { SessionListParams } from '../types/session';

export const sessionApi = {
  getSessions: (params?: SessionListParams) =>
    api.get('/sessions', { params }),
  getSessionContent: (sessionId: string) => api.get(`/sessions/${sessionId}/content`),
};
