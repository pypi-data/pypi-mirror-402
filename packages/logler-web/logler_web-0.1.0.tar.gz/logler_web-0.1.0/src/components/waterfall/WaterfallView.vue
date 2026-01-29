<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NEmpty, NAlert, NSpin, NSelect, NSpace, NButton } from 'naive-ui'
import { PhChartBar } from '@phosphor-icons/vue'
import WaterfallTimeline from './WaterfallTimeline.vue'
import WaterfallBar from './WaterfallBar.vue'
import { api } from '@/api/client'
import { useFilesStore } from '@/stores/files'
import { useThreadsStore } from '@/stores/threads'
import type { HierarchyNode, HierarchyResponse } from '@/api/types'

interface FlattenedItem {
  id: string
  label: string
  startTime: number
  endTime: number
  hasErrors: boolean
  depth: number
}

const filesStore = useFilesStore()
const threadsStore = useThreadsStore()

const selectedIdentifier = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const hierarchyData = ref<HierarchyResponse | null>(null)

const threadOptions = computed(() => {
  return threadsStore.threads.map((t) => ({
    label: `${t.thread_id} (${t.log_count} logs)`,
    value: t.thread_id,
  }))
})

function flattenHierarchy(node: HierarchyNode, depth = 0): FlattenedItem[] {
  const items: FlattenedItem[] = []

  // Only include nodes with valid time data
  if (node.start_time && node.end_time) {
    items.push({
      id: node.id,
      label: node.label || node.id,
      startTime: new Date(node.start_time).getTime(),
      endTime: new Date(node.end_time).getTime(),
      hasErrors: node.error_count > 0,
      depth,
    })
  }

  for (const child of node.children) {
    items.push(...flattenHierarchy(child, depth + 1))
  }

  return items
}

const flattenedItems = computed<FlattenedItem[]>(() => {
  if (!hierarchyData.value?.hierarchy) return []
  return flattenHierarchy(hierarchyData.value.hierarchy)
})

const globalStart = computed(() => {
  if (flattenedItems.value.length === 0) return 0
  return Math.min(...flattenedItems.value.map((i) => i.startTime))
})

const globalEnd = computed(() => {
  if (flattenedItems.value.length === 0) return 0
  return Math.max(...flattenedItems.value.map((i) => i.endTime))
})

async function loadWaterfall() {
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
    error.value = err instanceof Error ? err.message : 'Failed to build waterfall'
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
  <div class="waterfall-view">
    <div class="waterfall-header">
      <NSpace align="center">
        <NSelect
          v-if="threadOptions.length > 0"
          v-model:value="selectedIdentifier"
          :options="threadOptions"
          placeholder="Select a thread..."
          filterable
          clearable
          style="min-width: 300px;"
          :disabled="loading"
        />
        <NButton
          type="primary"
          :loading="loading"
          :disabled="!selectedIdentifier"
          @click="loadWaterfall"
        >
          <template #icon>
            <PhChartBar weight="regular" />
          </template>
          Build Waterfall
        </NButton>
      </NSpace>
    </div>

    <div class="waterfall-content">
      <NSpin :show="loading">
        <NAlert v-if="error" type="error" :bordered="false" style="margin: 12px;">
          {{ error }}
        </NAlert>

        <template v-else-if="flattenedItems.length > 0">
          <div class="waterfall-chart">
            <WaterfallTimeline
              :start-time="0"
              :end-time="globalEnd - globalStart"
            />
            <div class="waterfall-bars">
              <WaterfallBar
                v-for="item in flattenedItems"
                :key="item.id"
                :label="item.label"
                :start-time="item.startTime"
                :end-time="item.endTime"
                :global-start="globalStart"
                :global-end="globalEnd"
                :has-errors="item.hasErrors"
                :depth="item.depth"
              />
            </div>
          </div>
        </template>

        <div v-else class="empty-state">
          <NEmpty description="Select a thread and click 'Build Waterfall' to visualize timings" />
        </div>
      </NSpin>
    </div>
  </div>
</template>

<style scoped>
.waterfall-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.waterfall-header {
  padding: 12px;
  border-bottom: 1px solid rgba(230, 241, 255, 0.08);
}

.waterfall-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.waterfall-chart {
  padding: 12px;
}

.waterfall-bars {
  display: flex;
  flex-direction: column;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}
</style>
