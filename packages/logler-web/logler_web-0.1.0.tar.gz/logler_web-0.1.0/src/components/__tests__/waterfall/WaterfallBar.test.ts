import { describe, it, expect } from 'vitest'

// Test the calculation logic from WaterfallBar.vue
// These functions are extracted to verify the math independently

describe('WaterfallBar calculations', () => {
  // Replicate the component's calculation logic for testing
  function calculateLeftPercent(
    startTime: number,
    globalStart: number,
    totalDuration: number
  ): number {
    if (totalDuration <= 0) return 0
    return ((startTime - globalStart) / totalDuration) * 100
  }

  function calculateWidthPercent(
    startTime: number,
    endTime: number,
    totalDuration: number
  ): number {
    if (totalDuration <= 0) return 0
    const duration = endTime - startTime
    return Math.max((duration / totalDuration) * 100, 0.5) // Min 0.5% for visibility
  }

  function formatDuration(ms: number): string {
    if (ms < 1) return '<1ms'
    if (ms < 1000) return `${ms.toFixed(0)}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  describe('leftPercent', () => {
    it('returns 0 when bar starts at global start', () => {
      const result = calculateLeftPercent(0, 0, 1000)
      expect(result).toBe(0)
    })

    it('returns 50 when bar starts in the middle', () => {
      const result = calculateLeftPercent(500, 0, 1000)
      expect(result).toBe(50)
    })

    it('returns correct percentage for arbitrary position', () => {
      const result = calculateLeftPercent(250, 0, 1000)
      expect(result).toBe(25)
    })

    it('handles non-zero global start', () => {
      const result = calculateLeftPercent(150, 100, 200)
      // (150 - 100) / 200 * 100 = 25
      expect(result).toBe(25)
    })

    it('returns 0 when total duration is 0', () => {
      const result = calculateLeftPercent(100, 0, 0)
      expect(result).toBe(0)
    })

    it('returns 0 when total duration is negative', () => {
      const result = calculateLeftPercent(100, 0, -100)
      expect(result).toBe(0)
    })
  })

  describe('widthPercent', () => {
    it('returns full width for bar spanning entire duration', () => {
      const result = calculateWidthPercent(0, 1000, 1000)
      expect(result).toBe(100)
    })

    it('returns 50% for half duration', () => {
      const result = calculateWidthPercent(0, 500, 1000)
      expect(result).toBe(50)
    })

    it('enforces minimum 0.5% width for visibility', () => {
      const result = calculateWidthPercent(0, 1, 1000)
      expect(result).toBe(0.5)
    })

    it('returns minimum width for zero duration', () => {
      const result = calculateWidthPercent(500, 500, 1000)
      expect(result).toBe(0.5)
    })

    it('returns 0 when total duration is 0', () => {
      const result = calculateWidthPercent(0, 100, 0)
      expect(result).toBe(0)
    })

    it('handles small durations correctly', () => {
      // 10ms out of 10000ms = 0.1%, should use min 0.5%
      const result = calculateWidthPercent(0, 10, 10000)
      expect(result).toBe(0.5)
    })

    it('handles normal percentage above minimum', () => {
      // 100ms out of 1000ms = 10%
      const result = calculateWidthPercent(0, 100, 1000)
      expect(result).toBe(10)
    })
  })

  describe('formatDuration', () => {
    it('returns <1ms for sub-millisecond values', () => {
      expect(formatDuration(0)).toBe('<1ms')
      expect(formatDuration(0.5)).toBe('<1ms')
      expect(formatDuration(0.99)).toBe('<1ms')
    })

    it('formats milliseconds correctly', () => {
      expect(formatDuration(1)).toBe('1ms')
      expect(formatDuration(100)).toBe('100ms')
      expect(formatDuration(999)).toBe('999ms')
    })

    it('formats seconds correctly', () => {
      expect(formatDuration(1000)).toBe('1.0s')
      expect(formatDuration(1500)).toBe('1.5s')
      expect(formatDuration(59999)).toBe('60.0s')
    })

    it('formats minutes correctly', () => {
      expect(formatDuration(60000)).toBe('1.0m')
      expect(formatDuration(90000)).toBe('1.5m')
      expect(formatDuration(300000)).toBe('5.0m')
    })
  })

  describe('indent calculation', () => {
    function calculateIndent(depth: number | undefined): number {
      return (depth || 0) * 16
    }

    it('returns 0 for depth 0', () => {
      expect(calculateIndent(0)).toBe(0)
    })

    it('returns 0 for undefined depth', () => {
      expect(calculateIndent(undefined)).toBe(0)
    })

    it('returns 16 for depth 1', () => {
      expect(calculateIndent(1)).toBe(16)
    })

    it('returns correct indent for deeper levels', () => {
      expect(calculateIndent(3)).toBe(48)
      expect(calculateIndent(5)).toBe(80)
    })
  })
})
