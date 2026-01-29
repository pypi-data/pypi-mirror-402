import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFilesStore } from '../files'
import type { OpenManyResponse } from '@/api/types'

describe('files store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('computed properties', () => {
    it('hasActiveFiles returns false when no files are active', () => {
      const store = useFilesStore()
      expect(store.hasActiveFiles).toBe(false)
    })

    it('hasActiveFiles returns true when files are active', () => {
      const store = useFilesStore()
      store.setActiveFiles(['/path/to/file.log'])
      expect(store.hasActiveFiles).toBe(true)
    })

    it('isInterleaved returns false for single file', () => {
      const store = useFilesStore()
      store.setActiveFiles(['/path/to/file.log'])
      expect(store.isInterleaved).toBe(false)
    })

    it('isInterleaved returns true for multiple files', () => {
      const store = useFilesStore()
      store.setActiveFiles(['/path/to/file1.log', '/path/to/file2.log'])
      expect(store.isInterleaved).toBe(true)
    })
  })

  describe('setActiveFiles', () => {
    it('sets active files', () => {
      const store = useFilesStore()
      const paths = ['/logs/app.log', '/logs/error.log']

      store.setActiveFiles(paths)

      expect(store.activeFiles).toEqual(paths)
    })

    it('sets file metadata when provided', () => {
      const store = useFilesStore()
      const paths = ['/logs/app.log']
      const meta: OpenManyResponse['file_meta'] = [
        {
          path: '/logs/app.log',
          count: 100,
          first_ts: '2024-01-15T10:00:00Z',
          last_ts: '2024-01-15T10:30:00Z',
        },
      ]

      store.setActiveFiles(paths, meta)

      expect(store.fileMeta).toEqual(meta)
    })

    it('does not overwrite metadata when not provided', () => {
      const store = useFilesStore()
      const existingMeta: OpenManyResponse['file_meta'] = [
        {
          path: '/logs/old.log',
          count: 50,
          first_ts: '2024-01-14T10:00:00Z',
          last_ts: '2024-01-14T11:00:00Z',
        },
      ]
      store.fileMeta = existingMeta

      store.setActiveFiles(['/logs/new.log'])

      expect(store.fileMeta).toEqual(existingMeta)
    })
  })

  describe('clearActiveFiles', () => {
    it('clears active files and metadata', () => {
      const store = useFilesStore()
      store.activeFiles = ['/logs/app.log']
      store.fileMeta = [
        {
          path: '/logs/app.log',
          count: 100,
          first_ts: '2024-01-15T10:00:00Z',
          last_ts: '2024-01-15T10:30:00Z',
        },
      ]

      store.clearActiveFiles()

      expect(store.activeFiles).toHaveLength(0)
      expect(store.fileMeta).toHaveLength(0)
    })
  })

  describe('clearGlobResults', () => {
    it('clears glob pattern and results', () => {
      const store = useFilesStore()
      store.globPattern = '*.log'
      store.globResults = [
        { name: 'app.log', path: '/logs/app.log', size: 1024, modified: '2024-01-15', is_log: true },
      ]

      store.clearGlobResults()

      expect(store.globPattern).toBe('')
      expect(store.globResults).toHaveLength(0)
    })
  })

  describe('state initialization', () => {
    it('initializes with empty state', () => {
      const store = useFilesStore()

      expect(store.currentDir).toBe('')
      expect(store.parentDir).toBeNull()
      expect(store.files).toHaveLength(0)
      expect(store.directories).toHaveLength(0)
      expect(store.logRoot).toBe('')
      expect(store.activeFiles).toHaveLength(0)
      expect(store.globPattern).toBe('')
      expect(store.globResults).toHaveLength(0)
      expect(store.globLoading).toBe(false)
    })
  })
})
