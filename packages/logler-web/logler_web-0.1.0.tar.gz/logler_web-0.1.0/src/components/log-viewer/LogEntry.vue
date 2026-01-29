<script setup lang="ts">
import { computed } from 'vue'
import { NText, NTag, NSpace } from 'naive-ui'
import type { LogEntry as LogEntryType } from '@/api/types'

const props = defineProps<{
  entry: LogEntryType
}>()

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

const levelColor = computed(() => levelColors[props.entry.level] || '#808080')

const formattedTime = computed(() => {
  if (!props.entry.timestamp) return ''
  try {
    const date = new Date(props.entry.timestamp)
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    } as Intl.DateTimeFormatOptions)
  } catch {
    return props.entry.timestamp
  }
})
</script>

<template>
  <div class="log-entry">
    <div class="entry-header">
      <NSpace :size="8" align="center">
        <NText class="line-number" depth="3">{{ entry.line_number }}</NText>
        <NText class="timestamp" depth="3">{{ formattedTime }}</NText>
        <NTag
          :bordered="false"
          size="tiny"
          :style="{ background: levelColor + '20', color: levelColor }"
        >
          {{ entry.level }}
        </NTag>
        <NTag
          v-if="entry.thread_id"
          :bordered="false"
          size="tiny"
          type="info"
        >
          {{ entry.thread_id }}
        </NTag>
        <NTag
          v-if="entry.correlation_id"
          :bordered="false"
          size="tiny"
          type="warning"
        >
          {{ entry.correlation_id }}
        </NTag>
        <NTag
          v-if="entry.service_name"
          :bordered="false"
          size="tiny"
          type="success"
        >
          {{ entry.service_name }}
        </NTag>
      </NSpace>
    </div>
    <div class="entry-message">
      <NText class="message">{{ entry.message }}</NText>
    </div>
  </div>
</template>

<style scoped>
.log-entry {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-family: var(--font-mono, 'IBM Plex Mono', monospace);
  font-size: 13px;
}

.log-entry:hover {
  background: rgba(255, 255, 255, 0.03);
}

.entry-header {
  margin-bottom: 4px;
}

.line-number {
  font-size: 11px;
  min-width: 40px;
}

.timestamp {
  font-size: 11px;
}

.message {
  word-break: break-word;
  white-space: pre-wrap;
}
</style>
