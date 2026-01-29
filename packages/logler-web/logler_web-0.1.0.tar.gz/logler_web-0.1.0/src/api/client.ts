// API Client for logler-web backend

import type {
  BrowseResponse,
  GlobResponse,
  OpenFileRequest,
  OpenFileResponse,
  OpenManyRequest,
  OpenManyResponse,
  FilterRequest,
  FilterResponse,
  ThreadInfo,
  TraceInfo,
  HierarchyRequest,
  HierarchyResponse,
  SqlRequest,
  SqlResponse,
} from './types'

const API_BASE = '/api'

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API Error: ${response.status} - ${error}`)
  }

  return response.json()
}

export const api = {
  // File browsing
  async browse(directory?: string): Promise<BrowseResponse> {
    const params = directory ? `?directory=${encodeURIComponent(directory)}` : ''
    return fetchJson(`${API_BASE}/files/browse${params}`)
  },

  async glob(pattern: string, baseDir?: string, limit = 200): Promise<GlobResponse> {
    const params = new URLSearchParams({ pattern, limit: String(limit) })
    if (baseDir) params.set('base_dir', baseDir)
    return fetchJson(`${API_BASE}/files/glob?${params}`)
  },

  // File operations
  async openFile(request: OpenFileRequest): Promise<OpenFileResponse> {
    return fetchJson(`${API_BASE}/files/open`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  async openMany(request: OpenManyRequest): Promise<OpenManyResponse> {
    return fetchJson(`${API_BASE}/files/open_many`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  async filter(request: FilterRequest): Promise<FilterResponse> {
    return fetchJson(`${API_BASE}/files/filter`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  // Thread and trace info
  async getThreads(): Promise<ThreadInfo[]> {
    return fetchJson(`${API_BASE}/threads`)
  },

  async getTraces(): Promise<TraceInfo[]> {
    return fetchJson(`${API_BASE}/traces`)
  },

  // Hierarchy
  async buildHierarchy(request: HierarchyRequest): Promise<HierarchyResponse> {
    return fetchJson(`${API_BASE}/hierarchy`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  // SQL queries
  async executeSql(request: SqlRequest): Promise<SqlResponse> {
    return fetchJson(`${API_BASE}/sql`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },
}
