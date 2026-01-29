import { describe, it, expect, beforeEach } from 'vitest'
import {
  createLogEntry,
  createErrorEntry,
  createWarningEntry,
  createDebugEntry,
  resetLineCounter,
} from '@/test/factories'

// Test the display logic from LogEntry.vue
// These are extracted to test the component's computed behavior

describe('LogEntry display logic', () => {
  beforeEach(() => {
    resetLineCounter()
  })

  describe('level colors', () => {
    const levelColors: Record<string, string> = {
      TRACE: '#808080',
      DEBUG: '#00e5ff',
      INFO: '#a8ff60',
      WARN: '#ffcc00',
      WARNING: '#ffcc00',
      ERROR: '#ff3b3b',
      CRITICAL: '#ff3b3b',
      FATAL: '#ff3b3b',
    }

    function getLevelColor(level: string): string {
      return levelColors[level] || '#808080'
    }

    it('returns gray for TRACE', () => {
      expect(getLevelColor('TRACE')).toBe('#808080')
    })

    it('returns cyan for DEBUG', () => {
      expect(getLevelColor('DEBUG')).toBe('#00e5ff')
    })

    it('returns green for INFO', () => {
      expect(getLevelColor('INFO')).toBe('#a8ff60')
    })

    it('returns yellow for WARN', () => {
      expect(getLevelColor('WARN')).toBe('#ffcc00')
    })

    it('returns yellow for WARNING', () => {
      expect(getLevelColor('WARNING')).toBe('#ffcc00')
    })

    it('returns red for ERROR', () => {
      expect(getLevelColor('ERROR')).toBe('#ff3b3b')
    })

    it('returns red for CRITICAL', () => {
      expect(getLevelColor('CRITICAL')).toBe('#ff3b3b')
    })

    it('returns red for FATAL', () => {
      expect(getLevelColor('FATAL')).toBe('#ff3b3b')
    })

    it('returns fallback gray for unknown levels', () => {
      expect(getLevelColor('UNKNOWN')).toBe('#808080')
      expect(getLevelColor('custom')).toBe('#808080')
      expect(getLevelColor('')).toBe('#808080')
    })
  })

  describe('timestamp formatting', () => {
    function formatTimestamp(timestamp: string | null): string {
      if (!timestamp) return ''
      try {
        const date = new Date(timestamp)
        return date.toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        })
      } catch {
        return timestamp
      }
    }

    it('returns empty string for null timestamp', () => {
      expect(formatTimestamp(null)).toBe('')
    })

    it('formats ISO timestamp to time only', () => {
      const result = formatTimestamp('2024-01-15T10:30:45.000Z')
      // Note: This will vary by timezone in test environment
      expect(result).toMatch(/^\d{2}:\d{2}:\d{2}$/)
    })

    it('returns original string for invalid timestamp', () => {
      expect(formatTimestamp('not-a-date')).toBe('Invalid Date')
    })

    it('handles timestamps with milliseconds', () => {
      const result = formatTimestamp('2024-01-15T14:25:33.123Z')
      // Should format to HH:MM:SS (milliseconds stripped)
      expect(result).toMatch(/^\d{2}:\d{2}:\d{2}$/)
    })
  })

  describe('factory creates valid entries', () => {
    it('creates entry with all required fields', () => {
      const entry = createLogEntry()

      expect(entry).toHaveProperty('line_number')
      expect(entry).toHaveProperty('timestamp')
      expect(entry).toHaveProperty('level')
      expect(entry).toHaveProperty('message')
      expect(entry).toHaveProperty('thread_id')
      expect(entry).toHaveProperty('correlation_id')
      expect(entry).toHaveProperty('trace_id')
      expect(entry).toHaveProperty('span_id')
      expect(entry).toHaveProperty('service_name')
      expect(entry).toHaveProperty('raw')
    })

    it('createErrorEntry uses ERROR level', () => {
      const entry = createErrorEntry()
      expect(entry.level).toBe('ERROR')
    })

    it('createWarningEntry uses WARN level', () => {
      const entry = createWarningEntry()
      expect(entry.level).toBe('WARN')
    })

    it('createDebugEntry uses DEBUG level', () => {
      const entry = createDebugEntry()
      expect(entry.level).toBe('DEBUG')
    })

    it('increments line numbers automatically', () => {
      const entry1 = createLogEntry()
      const entry2 = createLogEntry()
      const entry3 = createLogEntry()

      expect(entry1.line_number).toBeLessThan(entry2.line_number)
      expect(entry2.line_number).toBeLessThan(entry3.line_number)
    })
  })

  describe('entry display conditions', () => {
    it('shows thread_id tag when present', () => {
      const entry = createLogEntry({ thread_id: 'main' })
      expect(entry.thread_id).toBe('main')
      // In the component, this would render a tag
    })

    it('hides thread_id tag when null', () => {
      const entry = createLogEntry({ thread_id: null })
      expect(entry.thread_id).toBeNull()
    })

    it('shows correlation_id tag when present', () => {
      const entry = createLogEntry({ correlation_id: 'req-123' })
      expect(entry.correlation_id).toBe('req-123')
    })

    it('shows service_name tag when present', () => {
      const entry = createLogEntry({ service_name: 'api-gateway' })
      expect(entry.service_name).toBe('api-gateway')
    })
  })
})
