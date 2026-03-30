export interface ToolResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface ListParams {
  status?: 'raw' | 'approved' | 'rejected';
  page?: number;
  page_size?: number;
}

export interface Session {
  id: string;
  session_id: string;
  status: string;
  source: string;
  quality_auto_score?: number;
  quality_manual_score?: number;
  [key: string]: any;
}

export interface SessionListResponse {
  items: Session[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface StatsResponse {
  total_sessions: number;
  raw_sessions: number;
  approved_sessions: number;
  rejected_sessions: number;
  avg_auto_score: number;
  curated_sessions: number;
}

export interface ScanResponse {
  files_found: number;
  files: string[];
}

export interface ImportResponse {
  success: boolean;
  session_id: string;
  message: string;
}

export interface ImportAllResponse {
  total_files: number;
  imported: number;
  failed: number;
  failed_files: string[];
}

export interface EvaluateResponse {
  session_id: string;
  quality_auto_score: number;
  evaluation_status: string;
  evaluation_details?: any;
}

export interface EvaluateAllResponse {
  total_pending: number;
  evaluated: number;
  failed: number;
}

export interface PendingResponse {
  items: Session[];
  total: number;
  page: number;
  page_size: number;
}

export interface ReviewResponse {
  session_id: string;
  status: string;
  message: string;
}

export interface BatchReviewResponse {
  total_processed: number;
  success: number;
  failed: number;
  results: ReviewResponse[];
}
