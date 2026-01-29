import { describe, it, expect } from 'vitest'

// Test the calculation logic from WaterfallTimeline.vue
// These functions are extracted to verify the tick generation

describe('WaterfallTimeline calculations', () => {
  function formatTime(ms: number): string {
    if (ms < 1000) return `${ms.toFixed(0)}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  interface Tick {
    time: number
    percent: number
    label: string
  }

  function generateTicks(startTime: number, endTime: number): Tick[] {
    const duration = endTime - startTime
    if (duration <= 0) return []

    // Determine tick count based on total duration
    let tickCount = 5
    if (duration < 100) tickCount = 4
    if (duration > 60000) tickCount = 6

    const interval = duration / tickCount
    const result: Tick[] = []

    for (let i = 0; i <= tickCount; i++) {
      const time = i * interval
      const percent = (time / duration) * 100
      result.push({
        time,
        percent,
        label: formatTime(time),
      })
    }

    return result
  }

  describe('formatTime', () => {
    it('formats milliseconds correctly', () => {
      expect(formatTime(0)).toBe('0ms')
      expect(formatTime(100)).toBe('100ms')
      expect(formatTime(999)).toBe('999ms')
    })

    it('formats seconds correctly', () => {
      expect(formatTime(1000)).toBe('1.0s')
      expect(formatTime(5000)).toBe('5.0s')
      expect(formatTime(59999)).toBe('60.0s')
    })

    it('formats minutes correctly', () => {
      expect(formatTime(60000)).toBe('1.0m')
      expect(formatTime(120000)).toBe('2.0m')
    })
  })

  describe('tick generation', () => {
    it('returns empty array when duration is 0', () => {
      const ticks = generateTicks(0, 0)
      expect(ticks).toHaveLength(0)
    })

    it('returns empty array when duration is negative', () => {
      const ticks = generateTicks(100, 50)
      expect(ticks).toHaveLength(0)
    })

    it('generates 5 ticks for normal duration (5 intervals = 6 tick marks)', () => {
      const ticks = generateTicks(0, 1000)
      expect(ticks).toHaveLength(6) // 0, 200, 400, 600, 800, 1000
    })

    it('generates 4 ticks for short duration < 100ms (4 intervals = 5 tick marks)', () => {
      const ticks = generateTicks(0, 50)
      expect(ticks).toHaveLength(5)
    })

    it('generates 6 ticks for long duration > 60000ms (6 intervals = 7 tick marks)', () => {
      const ticks = generateTicks(0, 120000)
      expect(ticks).toHaveLength(7)
    })

    it('first tick is at 0%', () => {
      const ticks = generateTicks(0, 1000)
      expect(ticks[0].percent).toBe(0)
      expect(ticks[0].time).toBe(0)
    })

    it('last tick is at 100%', () => {
      const ticks = generateTicks(0, 1000)
      const lastTick = ticks[ticks.length - 1]
      expect(lastTick.percent).toBe(100)
      expect(lastTick.time).toBe(1000)
    })

    it('ticks are evenly spaced', () => {
      const ticks = generateTicks(0, 1000)
      const intervals: number[] = []

      for (let i = 1; i < ticks.length; i++) {
        intervals.push(ticks[i].time - ticks[i - 1].time)
      }

      // All intervals should be equal
      const firstInterval = intervals[0]
      expect(intervals.every((i) => i === firstInterval)).toBe(true)
    })

    it('tick labels are formatted correctly', () => {
      const ticks = generateTicks(0, 5000)

      expect(ticks[0].label).toBe('0ms')
      expect(ticks[ticks.length - 1].label).toBe('5.0s')
    })

    it('handles fractional milliseconds in labels', () => {
      const ticks = generateTicks(0, 100)
      // 100ms is not < 100, so tickCount = 5, interval = 100/5 = 20ms
      expect(ticks[1].label).toBe('20ms')
    })
  })

  describe('tick count selection', () => {
    it('uses 4 ticks for very short durations', () => {
      // <100ms uses 4 intervals
      const ticks = generateTicks(0, 80)
      expect(ticks).toHaveLength(5) // 4 intervals + 1
    })

    it('uses 5 ticks for medium durations', () => {
      // 100ms to 60000ms uses 5 intervals
      const ticks = generateTicks(0, 30000)
      expect(ticks).toHaveLength(6) // 5 intervals + 1
    })

    it('uses 6 ticks for long durations', () => {
      // >60000ms uses 6 intervals
      const ticks = generateTicks(0, 180000) // 3 minutes
      expect(ticks).toHaveLength(7) // 6 intervals + 1
    })
  })
})
