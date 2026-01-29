// API Request/Response Types

export interface LogEntry {
  line_number: number
  timestamp: string | null
  level: string
  message: string
  thread_id: string | null
  correlation_id: string | null
  trace_id: string | null
  span_id: string | null
  service_name: string | null
  raw: string
  file?: string
}

export interface FileInfo {
  name: string
  path: string
  size: number
  modified: string
  is_log: boolean
}

export interface DirectoryInfo {
  name: string
  path: string
}

export interface BrowseResponse {
  current_dir: string
  parent_dir: string | null
  files: FileInfo[]
  directories: DirectoryInfo[]
  log_root: string
}

export interface GlobResponse {
  pattern: string
  count: number
  files: FileInfo[]
  truncated: boolean
}

export interface OpenFileRequest {
  path: string
  filters?: FilterOptions
  limit?: number
  quick?: boolean
}

export interface OpenFileResponse {
  file_path: string
  entries: LogEntry[]
  total: number
  partial: boolean
}

export interface OpenManyRequest {
  paths: string[]
  filters?: FilterOptions
  limit?: number
}

export interface OpenManyResponse {
  files: string[]
  entries: LogEntry[]
  total: number
  file_counts: Record<string, number>
  file_meta: Array<{
    path: string
    count: number
    first_ts: string | null
    last_ts: string | null
  }>
}

export interface FilterOptions {
  search?: string
  levels?: string[]
  thread_id?: string
  correlation_id?: string
  trace_id?: string
}

export interface FilterRequest {
  paths: string[]
  filters?: FilterOptions
  limit?: number
  sample_per_level?: number
  sample_per_thread?: number
}

export interface FilterResponse {
  entries: LogEntry[]
  total: number
  sampled?: boolean
}

export interface ThreadInfo {
  thread_id: string
  log_count: number
  error_count: number
  first_seen: string | null
  last_seen: string | null
}

export interface TraceInfo {
  trace_id: string
  spans: string[]
  start_time: string | null
  end_time: string | null
}

export interface HierarchyRequest {
  paths: string[]
  root_identifier: string
  max_depth?: number
  min_confidence?: number
  use_naming_patterns?: boolean
  use_temporal_inference?: boolean
}

export interface HierarchyNode {
  id: string
  label: string
  entry_count: number
  error_count: number
  start_time: string | null
  end_time: string | null
  duration_ms: number | null
  children: HierarchyNode[]
}

export interface ErrorAnalysis {
  root_cause: string | null
  error_chain: string[]
  recommendations: string[]
  impact_summary: string
}

export interface HierarchyResponse {
  hierarchy: HierarchyNode
  error_analysis: ErrorAnalysis | null
}

export interface SqlRequest {
  query: string
}

export interface SqlResponse {
  columns: string[]
  rows: Record<string, unknown>[]
  row_count: number
  error?: string
}
