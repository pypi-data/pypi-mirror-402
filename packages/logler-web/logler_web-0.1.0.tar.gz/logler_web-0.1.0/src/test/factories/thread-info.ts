import type { ThreadInfo, TraceInfo } from '@/api/types'

interface ThreadInfoOverrides {
  thread_id?: string
  log_count?: number
  error_count?: number
  first_seen?: string | null
  last_seen?: string | null
}

interface TraceInfoOverrides {
  trace_id?: string
  spans?: string[]
  start_time?: string | null
  end_time?: string | null
}

let threadCounter = 0
let traceCounter = 0

export function createThreadInfo(overrides: ThreadInfoOverrides = {}): ThreadInfo {
  threadCounter++
  return {
    thread_id: overrides.thread_id ?? `thread-${threadCounter}`,
    log_count: overrides.log_count ?? 50,
    error_count: overrides.error_count ?? 0,
    first_seen: overrides.first_seen ?? '2024-01-15T10:00:00.000Z',
    last_seen: overrides.last_seen ?? '2024-01-15T10:01:00.000Z',
  }
}

export function createThreadInfoList(count: number): ThreadInfo[] {
  return Array.from({ length: count }, () => createThreadInfo())
}

export function createWorkerThreads(): ThreadInfo[] {
  return [
    createThreadInfo({ thread_id: 'main', log_count: 100, error_count: 0 }),
    createThreadInfo({ thread_id: 'worker-1', log_count: 75, error_count: 1 }),
    createThreadInfo({ thread_id: 'worker-2', log_count: 80, error_count: 2 }),
    createThreadInfo({ thread_id: 'worker-3', log_count: 70, error_count: 0 }),
    createThreadInfo({ thread_id: 'http-handler', log_count: 50, error_count: 3 }),
  ]
}

export function createTraceInfo(overrides: TraceInfoOverrides = {}): TraceInfo {
  traceCounter++
  return {
    trace_id: overrides.trace_id ?? `trace-${traceCounter}`,
    spans: overrides.spans ?? [`span-${traceCounter}-a`, `span-${traceCounter}-b`],
    start_time: overrides.start_time ?? '2024-01-15T10:00:00.000Z',
    end_time: overrides.end_time ?? '2024-01-15T10:00:05.000Z',
  }
}

export function resetThreadCounter(): void {
  threadCounter = 0
}

export function resetTraceCounter(): void {
  traceCounter = 0
}
