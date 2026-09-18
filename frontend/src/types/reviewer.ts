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

export interface ReviewerExtraField {
  name: string;
  label: string;
  type: string;
  options?: string[];
  placeholder?: string;
  required?: boolean;
}

export interface ReviewerExtraFields {
  fields: ReviewerExtraField[];
}

export type ReviewExtras = Record<string, unknown>;
