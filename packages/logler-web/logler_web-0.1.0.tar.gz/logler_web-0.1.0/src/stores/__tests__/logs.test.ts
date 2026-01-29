import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useLogsStore } from '../logs'
import {
  createLogEntry,
  createLogEntries,
  createErrorEntry,
  createWarningEntry,
  createDebugEntry,
  createThreadedEntry,
  createCorrelatedEntry,
  resetLineCounter,
} from '@/test/factories'

describe('logs store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    resetLineCounter()
  })

  describe('filteredEntries', () => {
    it('returns all entries when no filters are applied', () => {
      const store = useLogsStore()
      const entries = createLogEntries(10)
      store.entries = entries

      expect(store.filteredEntries).toHaveLength(10)
      expect(store.filteredEntries).toEqual(entries)
    })

    it('filters by search query in message', () => {
      const store = useLogsStore()
      store.entries = [
        createLogEntry({ message: 'User logged in successfully' }),
        createLogEntry({ message: 'Database connection established' }),
        createLogEntry({ message: 'User logged out' }),
      ]

      store.setSearchQuery('user')

      expect(store.filteredEntries).toHaveLength(2)
      expect(store.filteredEntries[0].message).toBe('User logged in successfully')
      expect(store.filteredEntries[1].message).toBe('User logged out')
    })

    it('filters by search query in raw field', () => {
      const store = useLogsStore()
      store.entries = [
        createLogEntry({ message: 'Short message', raw: '[INFO] Connection pool: max_size=10' }),
        createLogEntry({ message: 'Another message', raw: '[DEBUG] Memory usage normal' }),
      ]

      store.setSearchQuery('pool')

      expect(store.filteredEntries).toHaveLength(1)
      expect(store.filteredEntries[0].raw).toContain('pool')
    })

    it('search is case insensitive', () => {
      const store = useLogsStore()
      store.entries = [
        createLogEntry({ message: 'ERROR occurred' }),
        createLogEntry({ message: 'error handled' }),
        createLogEntry({ message: 'No issues' }),
      ]

      store.setSearchQuery('ERROR')

      expect(store.filteredEntries).toHaveLength(2)
    })

    it('filters by log levels', () => {
      const store = useLogsStore()
      store.entries = [
        createLogEntry({ level: 'INFO' }),
        createErrorEntry(),
        createWarningEntry(),
        createDebugEntry(),
      ]

      // Deselect DEBUG and INFO
      store.toggleLevel('DEBUG')
      store.toggleLevel('INFO')

      const filtered = store.filteredEntries
      expect(filtered).toHaveLength(2)
      expect(filtered.every((e) => e.level === 'ERROR' || e.level === 'WARN')).toBe(true)
    })

    it('filters by correlation ID', () => {
      const store = useLogsStore()
      store.entries = [
        createCorrelatedEntry('req-123', { message: 'Start' }),
        createCorrelatedEntry('req-123', { message: 'Middle' }),
        createCorrelatedEntry('req-456', { message: 'Different request' }),
        createLogEntry({ message: 'No correlation' }),
      ]

      store.setCorrelationFilter('req-123')

      expect(store.filteredEntries).toHaveLength(2)
      expect(store.filteredEntries.every((e) => e.correlation_id === 'req-123')).toBe(true)
    })

    it('filters by partial correlation ID match', () => {
      const store = useLogsStore()
      store.entries = [
        createCorrelatedEntry('user-request-001'),
        createCorrelatedEntry('user-request-002'),
        createCorrelatedEntry('admin-request-001'),
      ]

      store.setCorrelationFilter('user')

      expect(store.filteredEntries).toHaveLength(2)
    })

    it('filters by thread ID', () => {
      const store = useLogsStore()
      store.entries = [
        createThreadedEntry('main', { message: 'Main thread' }),
        createThreadedEntry('worker-1', { message: 'Worker 1' }),
        createThreadedEntry('worker-2', { message: 'Worker 2' }),
        createLogEntry({ message: 'No thread' }),
      ]

      store.setThreadFilter('worker')

      expect(store.filteredEntries).toHaveLength(2)
      expect(store.filteredEntries.every((e) => e.thread_id?.includes('worker'))).toBe(true)
    })

    it('applies multiple filters together', () => {
      const store = useLogsStore()
      store.entries = [
        createThreadedEntry('main', { level: 'ERROR', message: 'Main error' }),
        createThreadedEntry('main', { level: 'INFO', message: 'Main info' }),
        createThreadedEntry('worker-1', { level: 'ERROR', message: 'Worker error' }),
        createThreadedEntry('worker-1', { level: 'INFO', message: 'Worker info' }),
      ]

      store.setThreadFilter('main')
      store.toggleLevel('INFO')
      store.toggleLevel('DEBUG')
      store.toggleLevel('TRACE')
      store.toggleLevel('WARN')
      store.toggleLevel('WARNING')
      store.toggleLevel('CRITICAL')
      store.toggleLevel('FATAL')

      expect(store.filteredEntries).toHaveLength(1)
      expect(store.filteredEntries[0].message).toBe('Main error')
    })

    it('handles empty entries array', () => {
      const store = useLogsStore()
      store.entries = []

      expect(store.filteredEntries).toHaveLength(0)
    })

    it('handles entries with null values gracefully', () => {
      const store = useLogsStore()
      store.entries = [
        createLogEntry({ thread_id: null, correlation_id: null }),
        createThreadedEntry('main'),
      ]

      store.setThreadFilter('main')

      expect(store.filteredEntries).toHaveLength(1)
      expect(store.filteredEntries[0].thread_id).toBe('main')
    })
  })

  describe('stats', () => {
    it('calculates total count', () => {
      const store = useLogsStore()
      store.entries = createLogEntries(25)

      expect(store.stats.total).toBe(25)
    })

    it('calculates error count for ERROR level', () => {
      const store = useLogsStore()
      store.entries = [
        createLogEntry({ level: 'INFO' }),
        createLogEntry({ level: 'ERROR' }),
        createLogEntry({ level: 'ERROR' }),
        createLogEntry({ level: 'WARN' }),
      ]

      expect(store.stats.errors).toBe(2)
    })

    it('includes CRITICAL and FATAL in error count', () => {
      const store = useLogsStore()
      store.entries = [
        createLogEntry({ level: 'ERROR' }),
        createLogEntry({ level: 'CRITICAL' }),
        createLogEntry({ level: 'FATAL' }),
        createLogEntry({ level: 'INFO' }),
      ]

      expect(store.stats.errors).toBe(3)
    })

    it('calculates warning count for WARN and WARNING', () => {
      const store = useLogsStore()
      store.entries = [
        createLogEntry({ level: 'WARN' }),
        createLogEntry({ level: 'WARNING' }),
        createLogEntry({ level: 'INFO' }),
        createLogEntry({ level: 'ERROR' }),
      ]

      expect(store.stats.warnings).toBe(2)
    })

    it('stats reflect filtered entries', () => {
      const store = useLogsStore()
      store.entries = [
        createThreadedEntry('main', { level: 'ERROR' }),
        createThreadedEntry('main', { level: 'WARN' }),
        createThreadedEntry('worker', { level: 'ERROR' }),
        createThreadedEntry('worker', { level: 'ERROR' }),
      ]

      store.setThreadFilter('main')

      expect(store.stats.total).toBe(2)
      expect(store.stats.errors).toBe(1)
      expect(store.stats.warnings).toBe(1)
    })

    it('returns zeros for empty entries', () => {
      const store = useLogsStore()
      store.entries = []

      expect(store.stats).toEqual({ total: 0, errors: 0, warnings: 0 })
    })
  })

  describe('actions', () => {
    it('addEntry appends to entries and increments total', () => {
      const store = useLogsStore()
      store.entries = createLogEntries(3)
      store.totalAvailable = 3

      const newEntry = createLogEntry({ message: 'New entry' })
      store.addEntry(newEntry)

      expect(store.entries).toHaveLength(4)
      expect(store.entries[3]).toStrictEqual(newEntry)
      expect(store.totalAvailable).toBe(4)
    })

    it('clearEntries resets all entry state', () => {
      const store = useLogsStore()
      store.entries = createLogEntries(10)
      store.totalAvailable = 100
      store.partialLoad = true

      store.clearEntries()

      expect(store.entries).toHaveLength(0)
      expect(store.totalAvailable).toBe(0)
      expect(store.partialLoad).toBe(false)
    })

    it('toggleLevel adds level if not present', () => {
      const store = useLogsStore()
      // Start fresh - remove a level first
      store.selectedLevels = ['INFO', 'WARN']

      store.toggleLevel('ERROR')

      expect(store.selectedLevels).toContain('ERROR')
    })

    it('toggleLevel removes level if present', () => {
      const store = useLogsStore()
      expect(store.selectedLevels).toContain('DEBUG')

      store.toggleLevel('DEBUG')

      expect(store.selectedLevels).not.toContain('DEBUG')
    })

    it('clearFilters resets all filter state', () => {
      const store = useLogsStore()
      store.setSearchQuery('test')
      store.toggleLevel('DEBUG')
      store.setCorrelationFilter('corr-123')
      store.setThreadFilter('main')

      store.clearFilters()

      expect(store.searchQuery).toBe('')
      expect(store.selectedLevels).toHaveLength(8) // All levels
      expect(store.correlationFilter).toBe('')
      expect(store.threadFilter).toBe('')
    })
  })
})
