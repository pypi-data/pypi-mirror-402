import { vi, beforeEach } from 'vitest'
import { config } from '@vue/test-utils'

// Mock fetch globally
globalThis.fetch = vi.fn() as typeof fetch

// Configure Vue Test Utils defaults
config.global.stubs = {
  // Stub Naive UI components that are hard to test
  NTooltip: true,
}

// Reset mocks between tests
beforeEach(() => {
  vi.clearAllMocks()
})
