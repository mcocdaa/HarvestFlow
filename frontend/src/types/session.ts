export type SessionStatus = 'raw' | 'curated' | 'approved' | 'rejected';

export interface Session {
  session_id: string;
  status: SessionStatus;
  quality_auto_score?: number;
  quality_manual_score?: number;
  agent_role?: string;
  task_type?: string;
  created_at: string;
}

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string | any;
}

export interface SessionContent {
  messages?: Message[];
  metadata?: Record<string, any>;
  [key: string]: any;
}

export interface SessionListParams {
  status?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}
