import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import type { ThreadInfo } from '@/api/types'

export const useThreadsStore = defineStore('threads', () => {
  // Thread list
  const threads = ref<ThreadInfo[]>([])
  const threadSearch = ref('')

  // Selected threads for filtering
  const selectedThreads = ref<Set<string>>(new Set())

  // Computed
  const filteredThreads = computed(() => {
    if (!threadSearch.value) return threads.value
    const query = threadSearch.value.toLowerCase()
    return threads.value.filter((t) =>
      t.thread_id.toLowerCase().includes(query)
    )
  })

  const hasThreads = computed(() => threads.value.length > 0)

  // Actions
  async function loadThreads() {
    threads.value = await api.getThreads()
  }

  function setThreadSearch(query: string) {
    threadSearch.value = query
  }

  function toggleThread(threadId: string) {
    if (selectedThreads.value.has(threadId)) {
      selectedThreads.value.delete(threadId)
    } else {
      selectedThreads.value.add(threadId)
    }
  }

  function clearSelection() {
    selectedThreads.value.clear()
  }

  function clearThreads() {
    threads.value = []
    selectedThreads.value.clear()
    threadSearch.value = ''
  }

  return {
    // State
    threads,
    threadSearch,
    selectedThreads,
    // Computed
    filteredThreads,
    hasThreads,
    // Actions
    loadThreads,
    setThreadSearch,
    toggleThread,
    clearSelection,
    clearThreads,
  }
})
