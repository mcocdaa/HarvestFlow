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
