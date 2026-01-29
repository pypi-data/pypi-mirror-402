import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ViewMode = 'logs' | 'hierarchy' | 'waterfall' | 'sql'

export const useUiStore = defineStore('ui', () => {
  // Modal states
  const showFileBrowser = ref(false)
  const showInterleaveDetails = ref(false)

  // View mode
  const viewMode = ref<ViewMode>('logs')

  // Auto-scroll behavior
  const autoScroll = ref(true)

  // WebSocket connection status
  const wsConnected = ref(false)

  // Loading states
  const loading = ref(false)
  const indexing = ref(false)

  // Actions
  function openFileBrowser() {
    showFileBrowser.value = true
  }

  function closeFileBrowser() {
    showFileBrowser.value = false
  }

  function setViewMode(mode: ViewMode) {
    viewMode.value = mode
  }

  function toggleAutoScroll() {
    autoScroll.value = !autoScroll.value
  }

  return {
    // State
    showFileBrowser,
    showInterleaveDetails,
    viewMode,
    autoScroll,
    wsConnected,
    loading,
    indexing,
    // Actions
    openFileBrowser,
    closeFileBrowser,
    setViewMode,
    toggleAutoScroll,
  }
})
