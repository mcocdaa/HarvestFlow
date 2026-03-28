import api from './client';

export const reviewerApi = {
  approveSession: (sessionId: string, notes?: string, score?: number) => api.post(`/reviewer/approve/${sessionId}`, null, { params: { notes, score } }),
  rejectSession: (sessionId: string, notes?: string, score?: number) => api.post(`/reviewer/reject/${sessionId}`, null, { params: { notes, score } }),
  updateSession: (sessionId: string, updates: any) => api.put(`/reviewer/update/${sessionId}`, updates),
  batchApprove: (sessionIds: string[]) => api.post('/reviewer/batch-approve', { session_ids: sessionIds }),
  batchReject: (sessionIds: string[]) => api.post('/reviewer/batch-reject', { session_ids: sessionIds }),
  getPending: (page?: number, pageSize?: number) => api.get('/reviewer/pending', { params: { page, page_size: pageSize } }),
  getAuditLogs: (sessionId?: string) => api.get('/reviewer/logs', { params: { session_id: sessionId } }),
};
