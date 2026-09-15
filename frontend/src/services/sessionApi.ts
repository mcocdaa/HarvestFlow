import api from './client';
import type { SessionListParams, SessionUpdateParams } from '../types/session';

export const sessionApi = {
  getSessions: (params?: SessionListParams) =>
    api.get('/sessions', { params }),
  getSession: (sessionId: string) => api.get(`/sessions/${sessionId}`),
  getSessionContent: (sessionId: string) => api.get(`/sessions/${sessionId}/content`),
  updateSession: (sessionId: string, data: SessionUpdateParams) =>
    api.patch(`/sessions/${sessionId}`, data),
  deleteSession: (sessionId: string) => api.delete(`/sessions/${sessionId}`),
};
