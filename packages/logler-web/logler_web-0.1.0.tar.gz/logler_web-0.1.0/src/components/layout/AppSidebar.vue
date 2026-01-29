<script setup lang="ts">
import { computed } from 'vue'
import {
  NStatistic,
  NSpace,
  NInput,
  NCheckbox,
  NCheckboxGroup,
  NScrollbar,
  NDivider,
  NText,
  NEmpty,
} from 'naive-ui'
import { PhMagnifyingGlass, PhWarning, PhXCircle } from '@phosphor-icons/vue'
import { useLogsStore } from '@/stores/logs'
import { useThreadsStore } from '@/stores/threads'

const logsStore = useLogsStore()
const threadsStore = useThreadsStore()

const LOG_LEVELS = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL', 'FATAL']

const levelColors: Record<string, string> = {
  TRACE: '#808080',
  DEBUG: '#00e5ff',
  INFO: '#a8ff60',
  WARN: '#ffcc00',
  WARNING: '#ffcc00',
  ERROR: '#ff3b3b',
  CRITICAL: '#ff3b3b',
  FATAL: '#ff3b3b',
}

const stats = computed(() => logsStore.stats)
</script>

<template>
  <div class="sidebar-container">
    <!-- Statistics -->
    <div class="sidebar-section">
      <NSpace :size="12">
        <NStatistic label="Total" :value="stats.total" />
        <NStatistic label="Errors" :value="stats.errors">
          <template #prefix>
            <PhXCircle :size="16" color="#ff3b3b" weight="fill" />
          </template>
        </NStatistic>
        <NStatistic label="Warnings" :value="stats.warnings">
          <template #prefix>
            <PhWarning :size="16" color="#ffcc00" weight="fill" />
          </template>
        </NStatistic>
      </NSpace>
    </div>

    <NDivider style="margin: 12px 0;" />

    <!-- Search Filter -->
    <div class="sidebar-section">
      <NInput
        v-model:value="logsStore.searchQuery"
        placeholder="Search logs..."
        clearable
        size="small"
      >
        <template #prefix>
          <PhMagnifyingGlass :size="16" />
        </template>
      </NInput>
    </div>

    <!-- Correlation Filter -->
    <div class="sidebar-section">
      <NInput
        v-model:value="logsStore.correlationFilter"
        placeholder="Filter by correlation ID..."
        clearable
        size="small"
      />
    </div>

    <NDivider style="margin: 12px 0;" />

    <!-- Level Filters -->
    <div class="sidebar-section">
      <NText depth="3" style="font-size: 12px; margin-bottom: 8px; display: block;">
        Log Levels
      </NText>
      <NCheckboxGroup v-model:value="logsStore.selectedLevels">
        <NSpace vertical :size="4">
          <NCheckbox
            v-for="level in LOG_LEVELS"
            :key="level"
            :value="level"
            :label="level"
            :style="{ color: levelColors[level] }"
          />
        </NSpace>
      </NCheckboxGroup>
    </div>

    <NDivider style="margin: 12px 0;" />

    <!-- Threads Section -->
    <div class="sidebar-section threads-section">
      <NText depth="3" style="font-size: 12px; margin-bottom: 8px; display: block;">
        Threads ({{ threadsStore.threads.length }})
      </NText>

      <NInput
        v-model:value="threadsStore.threadSearch"
        placeholder="Search threads..."
        clearable
        size="small"
        style="margin-bottom: 8px;"
      />

      <NScrollbar style="max-height: 200px;" v-if="threadsStore.hasThreads">
        <div
          v-for="thread in threadsStore.filteredThreads"
          :key="thread.thread_id"
          class="thread-item"
          @click="logsStore.setThreadFilter(thread.thread_id)"
        >
          <NText class="thread-id">{{ thread.thread_id }}</NText>
          <NSpace :size="8">
            <NText depth="3" style="font-size: 11px;">
              {{ thread.log_count }} logs
            </NText>
            <NText
              v-if="thread.error_count > 0"
              style="font-size: 11px; color: #ff3b3b;"
            >
              {{ thread.error_count }} errors
            </NText>
          </NSpace>
        </div>
      </NScrollbar>
      <NEmpty v-else description="No threads" size="small" />
    </div>
  </div>
</template>

<style scoped>
.sidebar-container {
  padding: 12px;
}

.sidebar-section {
  margin-bottom: 8px;
}

.threads-section {
  flex: 1;
  min-height: 0;
}

.thread-item {
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
}

.thread-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.thread-id {
  font-family: var(--font-mono);
  font-size: 12px;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
