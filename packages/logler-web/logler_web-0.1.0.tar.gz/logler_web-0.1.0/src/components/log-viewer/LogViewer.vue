<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { NVirtualList, NText } from 'naive-ui'
import LogEntry from './LogEntry.vue'
import { useLogsStore } from '@/stores/logs'
import { useUiStore } from '@/stores/ui'

const logsStore = useLogsStore()
const uiStore = useUiStore()

const virtualListRef = ref<InstanceType<typeof NVirtualList> | null>(null)

const entries = computed(() => logsStore.filteredEntries)

// Auto-scroll to bottom when new entries arrive
watch(
  () => entries.value.length,
  async () => {
    if (uiStore.autoScroll && virtualListRef.value) {
      await nextTick()
      virtualListRef.value.scrollTo({ position: 'bottom' })
    }
  }
)
</script>

<template>
  <div class="log-viewer">
    <NVirtualList
      ref="virtualListRef"
      :items="entries"
      :item-size="56"
      item-resizable
      class="log-list"
    >
      <template #default="{ item }">
        <LogEntry :entry="item" />
      </template>
    </NVirtualList>

    <div v-if="entries.length === 0" class="empty-logs">
      <NText depth="3">No log entries match the current filters</NText>
    </div>
  </div>
</template>

<style scoped>
.log-viewer {
  height: 100%;
  background: var(--color-void, #07080d);
}

.log-list {
  height: 100%;
}

.empty-logs {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
