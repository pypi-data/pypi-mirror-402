<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NEmpty, NAlert, NSpin } from 'naive-ui'
import HierarchySelector from './HierarchySelector.vue'
import HierarchyTree from './HierarchyTree.vue'
import ErrorAnalysisPanel from './ErrorAnalysisPanel.vue'
import { api } from '@/api/client'
import { useFilesStore } from '@/stores/files'
import { useThreadsStore } from '@/stores/threads'
import type { HierarchyResponse } from '@/api/types'

const filesStore = useFilesStore()
const threadsStore = useThreadsStore()

const selectedIdentifier = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const hierarchyData = ref<HierarchyResponse | null>(null)

async function loadHierarchy() {
  if (!selectedIdentifier.value || filesStore.activeFiles.length === 0) return

  loading.value = true
  error.value = null
  hierarchyData.value = null

  try {
    hierarchyData.value = await api.buildHierarchy({
      paths: filesStore.activeFiles,
      root_identifier: selectedIdentifier.value,
    })
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to build hierarchy'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!threadsStore.hasThreads) {
    threadsStore.loadThreads()
  }
})
</script>

<template>
  <div class="hierarchy-view">
    <HierarchySelector
      v-model="selectedIdentifier"
      :loading="loading"
      @build="loadHierarchy"
    />

    <div class="hierarchy-content">
      <NSpin :show="loading">
        <NAlert v-if="error" type="error" :bordered="false" style="margin: 12px;">
          {{ error }}
        </NAlert>

        <template v-else-if="hierarchyData">
          <ErrorAnalysisPanel
            v-if="hierarchyData.error_analysis"
            :analysis="hierarchyData.error_analysis"
            style="margin: 12px;"
          />
          <HierarchyTree :hierarchy="hierarchyData.hierarchy" />
        </template>

        <div v-else class="empty-state">
          <NEmpty description="Select a thread or trace identifier and click 'Build Hierarchy'" />
        </div>
      </NSpin>
    </div>
  </div>
</template>

<style scoped>
.hierarchy-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.hierarchy-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}
</style>
