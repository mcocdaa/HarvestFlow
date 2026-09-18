import api from './client';
import type { ReviewExtras } from '../types';

const reviewBody = (extras?: ReviewExtras) =>
  extras && Object.keys(extras).length > 0 ? { extras } : null;

export const reviewerApi = {
  approveSession: (sessionId: string, notes?: string, score?: number, extras?: ReviewExtras) =>
    api.post(`/reviewer/approve/${sessionId}`, reviewBody(extras), { params: { notes, score } }),
  rejectSession: (sessionId: string, notes?: string, score?: number, extras?: ReviewExtras) =>
    api.post(`/reviewer/reject/${sessionId}`, reviewBody(extras), { params: { notes, score } }),
  getPending: (page?: number, pageSize?: number) =>
    api.get('/reviewer/pending', { params: { page, page_size: pageSize } }),
  getExtraFields: () => api.get('/reviewer/extra-fields'),
  batchApprove: (sessionIds: string[]) => api.post('/reviewer/batch-approve', sessionIds),
  batchReject: (sessionIds: string[]) => api.post('/reviewer/batch-reject', sessionIds),
  getAuditLogs: (sessionId?: string) =>
    api.get('/reviewer/audit-logs', { params: { session_id: sessionId } }),
};
