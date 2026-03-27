export interface Session {
  session_id: string;
  status: 'raw' | 'curated' | 'approved' | 'rejected';
  quality_auto_score?: number;
  quality_manual_score?: number;
  agent_role?: string;
  task_type?: string;
  created_at: string;
}

export interface SessionContent {
  messages?: any[];
  metadata?: Record<string, any>;
  [key: string]: any;
}

export interface SessionListParams {
  status?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface Stats {
  total_sessions: number;
  raw_sessions: number;
  approved_sessions: number;
  rejected_sessions: number;
  avg_auto_score: number;
  curated_sessions: number;
}

export interface Plugin {
  name: string;
  version: string;
  description: string;
  author: string;
  plugin_type: 'collectors' | 'curators' | 'reviewers';
  frontend_entry?: string;
  enabled?: boolean;
}

export interface ExportHistory {
  id: number;
  export_format: string;
  version: string;
  record_count: number;
  file_path: string;
  created_at: string;
}

export interface ExportParams {
  format: string;
  version?: string;
  min_score?: number;
  agent_role?: string;
}

export interface MenuItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  path: string;
}
