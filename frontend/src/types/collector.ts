export interface ScanResult {
  folder_path: string;
  files_found: number;
  files: string[];
}

export interface ImportAllResult {
  total: number;
  imported: number;
  skipped: number;
  failed: number;
  session_ids: string[];
  skipped_ids: string[];
  failed_files: string[];
}

export interface WatchRunResult {
  total: number;
  imported: number;
  skipped: number;
  failed: number;
  error?: string;
  at?: string;
}

export interface WatchState {
  enabled: boolean;
  running: boolean;
  interval: number;
  folders: string[];
  last_runs: Record<string, WatchRunResult>;
}

export interface WatchRunResponse {
  results: Record<string, WatchRunResult>;
}
