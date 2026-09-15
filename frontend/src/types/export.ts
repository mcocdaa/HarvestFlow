export interface ExportHistory {
  id: number;
  export_format: string;
  version: string;
  record_count: number;
  file_path: string;
  filters?: string | null;
  created_at: string;
}

export interface ExportParams {
  format: string;
  version?: string;
  min_score?: number;
  agent_role?: string;
  task_type?: string;
  tags?: string[];
}

export interface ExportResult {
  success: boolean;
  file_path: string;
  filename: string;
  record_count: number;
  format: string;
  version: string;
}

export interface ExportFormats {
  formats: string[];
}
