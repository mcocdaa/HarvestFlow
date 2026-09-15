export type SessionStatus = 'raw' | 'curated' | 'approved' | 'rejected';

export interface ToolUseBlock {
  type: 'tool_use';
  id?: string;
  name?: string;
  input?: unknown;
}

export interface ToolResultBlock {
  type: 'tool_result';
  tool_use_id?: string;
  content?: unknown;
  is_error?: boolean;
}

export type ToolCall = ToolUseBlock | ToolResultBlock | Record<string, unknown>;

export interface Session {
  session_id: string;
  file_path?: string;
  status: SessionStatus;
  quality_auto_score?: number | null;
  quality_manual_score?: number | null;
  agent_role?: string | null;
  task_type?: string | null;
  tools_used?: string[] | null;
  tags?: string[] | null;
  created_at: string;
  updated_at?: string;
}

export interface Message {
  role: string;
  content: string | unknown;
  tool_calls?: ToolCall[] | null;
}

export interface SessionContent {
  session_id?: string;
  messages?: Message[];
  metadata?: Record<string, unknown>;
  tools_used?: string[];
  [key: string]: unknown;
}

export interface SessionListParams {
  status?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface SessionUpdateParams {
  status?: string;
  quality_auto_score?: number;
  quality_manual_score?: number;
  agent_role?: string;
  task_type?: string;
  tools_used?: string[];
  tags?: string[];
}
