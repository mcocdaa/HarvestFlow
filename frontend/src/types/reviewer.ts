export interface AuditLog {
  id: number;
  session_id: string;
  action: string;
  operator: string;
  details?: string | null;
  created_at: string;
}

export interface BatchReviewResult {
  total: number;
  success: number;
  failed: number;
  results: { session_id: string; success: boolean }[];
}
