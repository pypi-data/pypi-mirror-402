import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useThreadsStore } from '../threads'
import { createThreadInfo, createWorkerThreads, resetThreadCounter } from '@/test/factories'

describe('threads store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    resetThreadCounter()
  })

  describe('filteredThreads', () => {
    it('returns all threads when no search query', () => {
      const store = useThreadsStore()
      const threads = createWorkerThreads()
      store.threads = threads

      expect(store.filteredThreads).toHaveLength(5)
      expect(store.filteredThreads).toEqual(threads)
    })

    it('filters threads by search query', () => {
      const store = useThreadsStore()
      store.threads = createWorkerThreads()

      store.setThreadSearch('worker')

      expect(store.filteredThreads).toHaveLength(3)
      expect(store.filteredThreads.every((t) => t.thread_id.includes('worker'))).toBe(true)
    })

    it('search is case insensitive', () => {
      const store = useThreadsStore()
      store.threads = createWorkerThreads()

      store.setThreadSearch('MAIN')

      expect(store.filteredThreads).toHaveLength(1)
      expect(store.filteredThreads[0].thread_id).toBe('main')
    })

    it('returns empty array when no matches', () => {
      const store = useThreadsStore()
      store.threads = createWorkerThreads()

      store.setThreadSearch('nonexistent')

      expect(store.filteredThreads).toHaveLength(0)
    })
  })

  describe('hasThreads', () => {
    it('returns false when no threads', () => {
      const store = useThreadsStore()
      expect(store.hasThreads).toBe(false)
    })

    it('returns true when threads exist', () => {
      const store = useThreadsStore()
      store.threads = [createThreadInfo()]
      expect(store.hasThreads).toBe(true)
    })
  })

  describe('toggleThread', () => {
    it('adds thread to selection', () => {
      const store = useThreadsStore()

      store.toggleThread('main')

      expect(store.selectedThreads.has('main')).toBe(true)
    })

    it('removes thread from selection if already selected', () => {
      const store = useThreadsStore()
      store.selectedThreads.add('main')

      store.toggleThread('main')

      expect(store.selectedThreads.has('main')).toBe(false)
    })

    it('allows multiple threads to be selected', () => {
      const store = useThreadsStore()

      store.toggleThread('main')
      store.toggleThread('worker-1')
      store.toggleThread('worker-2')

      expect(store.selectedThreads.size).toBe(3)
      expect(store.selectedThreads.has('main')).toBe(true)
      expect(store.selectedThreads.has('worker-1')).toBe(true)
      expect(store.selectedThreads.has('worker-2')).toBe(true)
    })
  })

  describe('clearSelection', () => {
    it('clears all selected threads', () => {
      const store = useThreadsStore()
      store.selectedThreads.add('main')
      store.selectedThreads.add('worker-1')

      store.clearSelection()

      expect(store.selectedThreads.size).toBe(0)
    })
  })

  describe('clearThreads', () => {
    it('clears threads, selection, and search', () => {
      const store = useThreadsStore()
      store.threads = createWorkerThreads()
      store.selectedThreads.add('main')
      store.threadSearch = 'worker'

      store.clearThreads()

      expect(store.threads).toHaveLength(0)
      expect(store.selectedThreads.size).toBe(0)
      expect(store.threadSearch).toBe('')
    })
  })

  describe('setThreadSearch', () => {
    it('sets the search query', () => {
      const store = useThreadsStore()

      store.setThreadSearch('test query')

      expect(store.threadSearch).toBe('test query')
    })

    it('can clear search by setting empty string', () => {
      const store = useThreadsStore()
      store.threadSearch = 'existing'

      store.setThreadSearch('')

      expect(store.threadSearch).toBe('')
    })
  })
})
