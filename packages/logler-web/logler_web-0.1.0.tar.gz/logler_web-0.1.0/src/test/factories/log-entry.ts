import type { LogEntry } from '@/api/types'

let lineCounter = 0

interface LogEntryOverrides {
  line_number?: number
  timestamp?: string | null
  level?: string
  message?: string
  thread_id?: string | null
  correlation_id?: string | null
  trace_id?: string | null
  span_id?: string | null
  service_name?: string | null
  raw?: string
  file?: string
}

export function createLogEntry(overrides: LogEntryOverrides = {}): LogEntry {
  lineCounter++
  const level = overrides.level ?? 'INFO'
  const timestamp = overrides.timestamp ?? `2024-01-15T10:00:00.${String(lineCounter).padStart(3, '0')}Z`
  const message = overrides.message ?? `Log message ${lineCounter}`

  return {
    line_number: overrides.line_number ?? lineCounter,
    timestamp,
    level,
    message,
    thread_id: overrides.thread_id ?? null,
    correlation_id: overrides.correlation_id ?? null,
    trace_id: overrides.trace_id ?? null,
    span_id: overrides.span_id ?? null,
    service_name: overrides.service_name ?? null,
    raw: overrides.raw ?? `${timestamp} [${level}] ${message}`,
    file: overrides.file,
  }
}

export function createLogEntries(count: number, overrides: LogEntryOverrides = {}): LogEntry[] {
  return Array.from({ length: count }, () => createLogEntry(overrides))
}

export function createErrorEntry(overrides: LogEntryOverrides = {}): LogEntry {
  return createLogEntry({
    level: 'ERROR',
    message: 'An error occurred',
    ...overrides,
  })
}

export function createWarningEntry(overrides: LogEntryOverrides = {}): LogEntry {
  return createLogEntry({
    level: 'WARN',
    message: 'A warning occurred',
    ...overrides,
  })
}

export function createDebugEntry(overrides: LogEntryOverrides = {}): LogEntry {
  return createLogEntry({
    level: 'DEBUG',
    message: 'Debug information',
    ...overrides,
  })
}

export function createThreadedEntry(threadId: string, overrides: LogEntryOverrides = {}): LogEntry {
  return createLogEntry({
    thread_id: threadId,
    ...overrides,
  })
}

export function createCorrelatedEntry(correlationId: string, overrides: LogEntryOverrides = {}): LogEntry {
  return createLogEntry({
    correlation_id: correlationId,
    ...overrides,
  })
}

export function resetLineCounter(): void {
  lineCounter = 0
}
