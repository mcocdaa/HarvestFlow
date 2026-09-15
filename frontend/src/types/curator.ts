export interface CuratorStatus {
  enabled: boolean;
  auto_approve_threshold: number;
}

export interface EvaluateResult {
  session_id?: string;
  score?: number;
  is_high_value?: boolean;
  tags?: string[];
  tools_used?: string[];
  auto_approved?: boolean;
  score_reasons?: string[];
  [key: string]: unknown;
}

export interface EvaluateAllResult {
  total: number;
  high_value: number;
  low_value: number;
  results: EvaluateResult[];
}
