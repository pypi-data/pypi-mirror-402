import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import type { FileInfo, DirectoryInfo, OpenManyResponse } from '@/api/types'

export const useFilesStore = defineStore('files', () => {
  // Browser state
  const currentDir = ref('')
  const parentDir = ref<string | null>(null)
  const files = ref<FileInfo[]>([])
  const directories = ref<DirectoryInfo[]>([])
  const logRoot = ref('')

  // Glob search state
  const globPattern = ref('')
  const globBaseDir = ref('')
  const globResults = ref<FileInfo[]>([])
  const globLoading = ref(false)

  // Active files
  const activeFiles = ref<string[]>([])
  const fileMeta = ref<OpenManyResponse['file_meta']>([])

  // Computed
  const hasActiveFiles = computed(() => activeFiles.value.length > 0)
  const isInterleaved = computed(() => activeFiles.value.length > 1)

  // Actions
  async function browse(directory?: string) {
    const response = await api.browse(directory)
    currentDir.value = response.current_dir
    parentDir.value = response.parent_dir
    files.value = response.files
    directories.value = response.directories
    logRoot.value = response.log_root
  }

  async function searchGlob(pattern: string, baseDir?: string) {
    globLoading.value = true
    try {
      const response = await api.glob(pattern, baseDir)
      globPattern.value = pattern
      globBaseDir.value = baseDir || ''
      globResults.value = response.files
    } finally {
      globLoading.value = false
    }
  }

  function setActiveFiles(paths: string[], meta?: OpenManyResponse['file_meta']) {
    activeFiles.value = paths
    if (meta) {
      fileMeta.value = meta
    }
  }

  function clearActiveFiles() {
    activeFiles.value = []
    fileMeta.value = []
  }

  function clearGlobResults() {
    globPattern.value = ''
    globResults.value = []
  }

  return {
    // Browser state
    currentDir,
    parentDir,
    files,
    directories,
    logRoot,
    // Glob state
    globPattern,
    globBaseDir,
    globResults,
    globLoading,
    // Active files
    activeFiles,
    fileMeta,
    // Computed
    hasActiveFiles,
    isInterleaved,
    // Actions
    browse,
    searchGlob,
    setActiveFiles,
    clearActiveFiles,
    clearGlobResults,
  }
})
