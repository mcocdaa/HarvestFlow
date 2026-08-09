import api from './client';

export const reviewerApi = {
  approveSession: (sessionId: string, notes?: string, score?: number) => api.post(`/reviewer/approve/${sessionId}`, null, { params: { notes, score } }),
  rejectSession: (sessionId: string, notes?: string, score?: number) => api.post(`/reviewer/reject/${sessionId}`, null, { params: { notes, score } }),
  getPending: (page?: number, pageSize?: number) => api.get('/reviewer/pending', { params: { page, page_size: pageSize } }),
};
