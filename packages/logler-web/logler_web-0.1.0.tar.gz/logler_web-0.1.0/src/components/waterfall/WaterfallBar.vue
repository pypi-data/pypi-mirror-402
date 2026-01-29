<script setup lang="ts">
import { computed } from 'vue'
import { NTooltip } from 'naive-ui'

const props = defineProps<{
  label: string
  startTime: number
  endTime: number
  globalStart: number
  globalEnd: number
  hasErrors?: boolean
  depth?: number
}>()

const totalDuration = computed(() => props.globalEnd - props.globalStart)

const leftPercent = computed(() => {
  if (totalDuration.value <= 0) return 0
  return ((props.startTime - props.globalStart) / totalDuration.value) * 100
})

const widthPercent = computed(() => {
  if (totalDuration.value <= 0) return 0
  const duration = props.endTime - props.startTime
  return Math.max((duration / totalDuration.value) * 100, 0.5) // Min 0.5% for visibility
})

const duration = computed(() => props.endTime - props.startTime)

function formatDuration(ms: number): string {
  if (ms < 1) return '<1ms'
  if (ms < 1000) return `${ms.toFixed(0)}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
}

const indent = computed(() => (props.depth || 0) * 16)
</script>

<template>
  <div class="waterfall-bar-row" :style="{ paddingLeft: `${indent}px` }">
    <div class="bar-label">{{ label }}</div>
    <div class="bar-track">
      <NTooltip>
        <template #trigger>
          <div
            class="bar"
            :class="{ 'has-errors': hasErrors }"
            :style="{
              left: `${leftPercent}%`,
              width: `${widthPercent}%`,
            }"
          />
        </template>
        <div>
          <strong>{{ label }}</strong><br />
          Duration: {{ formatDuration(duration) }}
        </div>
      </NTooltip>
    </div>
    <div class="bar-duration">{{ formatDuration(duration) }}</div>
  </div>
</template>

<style scoped>
.waterfall-bar-row {
  display: grid;
  grid-template-columns: 200px 1fr 80px;
  gap: 8px;
  align-items: center;
  padding: 4px 0;
}

.bar-label {
  font-size: 12px;
  font-family: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgba(230, 241, 255, 0.78);
}

.bar-track {
  position: relative;
  height: 18px;
  background: rgba(230, 241, 255, 0.04);
  border-radius: 2px;
}

.bar {
  position: absolute;
  top: 2px;
  bottom: 2px;
  background: linear-gradient(90deg, #00e5ff, #00bcd4);
  border-radius: 2px;
  min-width: 2px;
}

.bar.has-errors {
  background: linear-gradient(90deg, #ff3b3b, #ff6b6b);
}

.bar-duration {
  font-size: 11px;
  font-family: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color: rgba(230, 241, 255, 0.58);
  text-align: right;
}
</style>
