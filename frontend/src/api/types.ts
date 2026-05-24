export type UserRole = "admin" | "researcher" | "viewer";

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  is_staff: boolean;
  is_superuser: boolean;
  is_active?: boolean;
}

export interface Dataset {
  id: number;
  name: string;
  slug: string;
  description: string;
  file_path: string;
  dataset_type: "full" | "pilot" | "sample" | "generated" | "unknown";
  total_cases: number;
  attack_cases: number;
  benign_cases: number;
  utility_cases: number;
  rummlu_cases: number;
  sberquad_cases: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DefenseProfile {
  id: number;
  name: string;
  slug: string;
  level: "D0" | "D1" | "D2" | "D3" | "custom";
  description: string;
  yaml_path: string;
  parameters_json: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ModelEndpoint {
  id: number;
  name: string;
  display_name?: string;
  slug: string;
  provider: "lmstudio" | "ollama" | "openai_compatible" | "other";
  model_name: string;
  base_url: string;
  default_temperature: number;
  default_max_tokens: number;
  context_window: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_check_at: string | null;
  last_check_status: string;
}

export type RunStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface RunMetrics {
  id: number;
  run: number;
  proxy_asr: number | null;
  one_minus_asr: number | null;
  tpr: number | null;
  fpr: number | null;
  u_mean: number | null;
  rummlu_accuracy: number | null;
  sberquad_f1: number | null;
  sberquad_em: number | null;
  p50_latency: number | null;
  p95_latency: number | null;
  parse_error_rate: number | null;
  total_cases: number;
  ok_cases: number;
  error_cases: number;
  created_at: string;
  updated_at: string;
}

export interface BenchmarkRun {
  id: number;
  run_id: string;
  title: string;
  created_by: number | null;
  created_by_username: string | null;
  model_endpoint: number;
  model_endpoint_name: string;
  dataset: number;
  dataset_name: string;
  defense_profile: number;
  defense_profile_name: string;
  status: RunStatus;
  started_at: string | null;
  finished_at: string | null;
  output_dir: string;
  error_message: string;
  config_snapshot_json: Record<string, unknown>;
  temperature_override?: number | null;
  max_tokens_override?: number | null;
  extra_params_json?: Record<string, unknown>;
  metrics?: RunMetrics | null;
  can_start?: boolean;
  can_cancel?: boolean;
  logs_available?: boolean;
  artifacts_count?: number;
  created_at: string;
  updated_at: string;
}

export interface RunArtifact {
  id: number;
  run: number;
  run_id: string;
  run_title: string;
  artifact_type: string;
  file_path: string;
  size_bytes: number;
  created_at: string;
  source?: string;
  project_artifact?: ProjectArtifact;
}

export type ProjectArtifactType =
  | "dataset"
  | "config"
  | "run_artifact"
  | "report"
  | "table"
  | "figure"
  | "json"
  | "jsonl"
  | "log"
  | "markdown"
  | "document"
  | "script"
  | "other";

export interface ProjectArtifact {
  id: number;
  name: string;
  artifact_type: ProjectArtifactType;
  file_path: string;
  source_dir: string;
  extension: string;
  size_bytes: number;
  line_count: number | null;
  sha256: string;
  related_run: number | null;
  related_run_id: string | null;
  related_run_title: string | null;
  related_dataset: number | null;
  related_dataset_name: string | null;
  related_defense_profile: number | null;
  related_defense_profile_name: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ProjectArtifactsResponse {
  count: number;
  limit: number;
  offset: number;
  results: ProjectArtifact[];
}

export interface ProjectArtifactPreview {
  type?: string;
  text?: string;
  columns?: string[];
  rows?: Array<Record<string, unknown>>;
  view_url?: string;
  message?: string;
  metadata?: Record<string, unknown>;
  truncated?: boolean;
  missing?: boolean;
}

export interface DashboardResponse {
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  pending_runs: number;
  running_runs: number;
  models_count: number;
  datasets_count: number;
  defense_profiles_count: number;
  project_artifacts_count?: number;
  figures_count?: number;
  tables_count?: number;
  reports_count?: number;
  datasets_files_count?: number;
  configs_files_count?: number;
  avg_proxy_asr: number | null;
  avg_one_minus_asr: number | null;
  avg_fpr: number | null;
  avg_u_mean: number | null;
  avg_p95_latency: number | null;
  latest_runs: BenchmarkRun[];
  dataset_distribution: Record<string, number>;
  asr_by_profile: Array<{ profile: string; defense_level: string; proxy_asr: number | null }>;
  heatmap_by_model_profile: Array<{ model: string; profile: string; defense_level: string; proxy_asr: number | null }>;
}

export interface ResultRow {
  run_id: string;
  title: string;
  model: string;
  dataset: string;
  defense_profile: string;
  defense_level: string;
  proxy_asr: number | null;
  one_minus_asr: number | null;
  fpr: number | null;
  u_mean: number | null;
  p95_latency: number | null;
  parse_error_rate: number | null;
  created_at: string;
}

export interface ParetoPoint {
  run_id: string;
  model: string;
  profile: string;
  defense_level: string;
  proxy_asr: number | null;
  one_minus_asr: number | null;
  fpr: number | null;
  u_mean: number | null;
  p95_latency: number | null;
}

export interface HeatmapResponse {
  rows: string[];
  columns: string[];
  values: Array<Array<number | null>>;
}

export interface CompareRunInfo {
  id: number;
  run_id: string;
  title: string;
  model: string;
  model_endpoint?: number;
  dataset: string;
  dataset_id?: number;
  profile: string;
  defense_profile?: number;
  status: RunStatus;
  created_at?: string;
  finished_at: string | null;
}

export interface CompareMetric {
  key: string;
  label: string;
  value_a: number | null;
  value_b: number | null;
  delta: number | null;
  better: "a" | "b" | "equal" | null;
  direction: "lower" | "higher" | "neutral";
}

export interface CompareWarning {
  code: string;
  message: string;
}

export interface CategoryBreakdown {
  category: string;
  proxy_asr_a: number | null;
  proxy_asr_b: number | null;
  delta: number | null;
  better: "a" | "b" | "equal" | null;
}

export interface DifferentCase {
  case_id: string;
  category: string;
  result_a: string;
  result_b: string;
  better: "a" | "b" | "equal" | null;
  difference?: string;
}

export interface CompareResponse {
  run_a: CompareRunInfo;
  run_b: CompareRunInfo;
  model_a?: string;
  model_b?: string;
  dataset_a?: string;
  dataset_b?: string;
  defense_profile_a?: string;
  defense_profile_b?: string;
  metrics: CompareMetric[];
  warnings: CompareWarning[];
  category_breakdown: CategoryBreakdown[];
  top_different_cases: DifferentCase[];
}

export interface CompareOptionRun {
  id: number;
  run_id: string;
  title: string;
  model: string;
  dataset: string;
  dataset_id: number;
  profile: string;
  defense_profile_id: number;
  status: RunStatus;
  finished_at: string | null;
  label: string;
  has_metrics: boolean;
}

export interface CompareOptionsResponse {
  runs: CompareOptionRun[];
  groups: Array<{
    model: string;
    dataset: string;
    profile: string;
    runs: CompareOptionRun[];
  }>;
}

export interface TokenPair {
  access: string;
  refresh: string;
}
