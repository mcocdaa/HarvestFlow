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
