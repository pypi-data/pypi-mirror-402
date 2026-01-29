import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import type { LogEntry, FilterOptions } from '@/api/types'
import { useFilesStore } from './files'
import { useUiStore } from './ui'

const LOG_LEVELS = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL']

export const useLogsStore = defineStore('logs', () => {
  // Log entries
  const entries = ref<LogEntry[]>([])
  const totalAvailable = ref(0)
  const partialLoad = ref(false)

  // Filter state
  const searchQuery = ref('')
  const selectedLevels = ref<string[]>([...LOG_LEVELS])
  const correlationFilter = ref('')
  const threadFilter = ref('')

  // Computed filtered entries
  const filteredEntries = computed(() => {
    let result = entries.value

    // Filter by search query
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(
        (e) =>
          e.message.toLowerCase().includes(query) ||
          e.raw.toLowerCase().includes(query)
      )
    }

    // Filter by levels
    if (selectedLevels.value.length < LOG_LEVELS.length) {
      result = result.filter((e) => selectedLevels.value.includes(e.level))
    }

    // Filter by correlation ID
    if (correlationFilter.value) {
      result = result.filter(
        (e) => e.correlation_id?.includes(correlationFilter.value)
      )
    }

    // Filter by thread ID
    if (threadFilter.value) {
      result = result.filter(
        (e) => e.thread_id?.includes(threadFilter.value)
      )
    }

    return result
  })

  // Stats
  const stats = computed(() => {
    const total = filteredEntries.value.length
    const errors = filteredEntries.value.filter(
      (e) => ['ERROR', 'CRITICAL', 'FATAL'].includes(e.level)
    ).length
    const warnings = filteredEntries.value.filter(
      (e) => ['WARN', 'WARNING'].includes(e.level)
    ).length
    return { total, errors, warnings }
  })

  // Actions
  async function openFile(path: string, quick = true) {
    const uiStore = useUiStore()
    const filesStore = useFilesStore()

    uiStore.loading = true
    try {
      const response = await api.openFile({ path, quick })
      entries.value = response.entries
      totalAvailable.value = response.total
      partialLoad.value = response.partial
      filesStore.setActiveFiles([path])
    } finally {
      uiStore.loading = false
    }
  }

  async function openMany(paths: string[]) {
    const uiStore = useUiStore()
    const filesStore = useFilesStore()

    uiStore.loading = true
    try {
      const response = await api.openMany({ paths })
      entries.value = response.entries
      totalAvailable.value = response.total
      partialLoad.value = false
      filesStore.setActiveFiles(paths, response.file_meta)
    } finally {
      uiStore.loading = false
    }
  }

  async function applyServerFilters() {
    const filesStore = useFilesStore()
    const uiStore = useUiStore()

    if (!filesStore.hasActiveFiles) return

    const filters: FilterOptions = {}
    if (searchQuery.value) filters.search = searchQuery.value
    if (selectedLevels.value.length < LOG_LEVELS.length) {
      filters.levels = selectedLevels.value
    }
    if (correlationFilter.value) filters.correlation_id = correlationFilter.value
    if (threadFilter.value) filters.thread_id = threadFilter.value

    uiStore.loading = true
    try {
      const response = await api.filter({
        paths: filesStore.activeFiles,
        filters,
      })
      entries.value = response.entries
      totalAvailable.value = response.total
    } finally {
      uiStore.loading = false
    }
  }

  function addEntry(entry: LogEntry) {
    entries.value.push(entry)
    totalAvailable.value++
  }

  function clearEntries() {
    entries.value = []
    totalAvailable.value = 0
    partialLoad.value = false
  }

  function setSearchQuery(query: string) {
    searchQuery.value = query
  }

  function toggleLevel(level: string) {
    const index = selectedLevels.value.indexOf(level)
    if (index > -1) {
      selectedLevels.value.splice(index, 1)
    } else {
      selectedLevels.value.push(level)
    }
  }

  function setCorrelationFilter(filter: string) {
    correlationFilter.value = filter
  }

  function setThreadFilter(filter: string) {
    threadFilter.value = filter
  }

  function clearFilters() {
    searchQuery.value = ''
    selectedLevels.value = [...LOG_LEVELS]
    correlationFilter.value = ''
    threadFilter.value = ''
  }

  return {
    // State
    entries,
    totalAvailable,
    partialLoad,
    searchQuery,
    selectedLevels,
    correlationFilter,
    threadFilter,
    // Computed
    filteredEntries,
    stats,
    // Actions
    openFile,
    openMany,
    applyServerFilters,
    addEntry,
    clearEntries,
    setSearchQuery,
    toggleLevel,
    setCorrelationFilter,
    setThreadFilter,
    clearFilters,
  }
})
