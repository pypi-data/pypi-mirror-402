<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  startTime: number
  endTime: number
}>()

const totalDuration = computed(() => props.endTime - props.startTime)

function formatTime(ms: number): string {
  if (ms < 1000) return `${ms.toFixed(0)}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
}

const ticks = computed(() => {
  const duration = totalDuration.value
  if (duration <= 0) return []

  // Determine tick interval based on total duration
  let tickCount = 5
  if (duration < 100) tickCount = 4
  if (duration > 60000) tickCount = 6

  const interval = duration / tickCount
  const result = []

  for (let i = 0; i <= tickCount; i++) {
    const time = i * interval
    const percent = (time / duration) * 100
    result.push({
      time,
      percent,
      label: formatTime(time),
    })
  }

  return result
})
</script>

<template>
  <div class="waterfall-timeline">
    <div class="timeline-ruler">
      <div
        v-for="tick in ticks"
        :key="tick.time"
        class="tick"
        :style="{ left: `${tick.percent}%` }"
      >
        <div class="tick-line" />
        <span class="tick-label">{{ tick.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.waterfall-timeline {
  position: relative;
  height: 28px;
  border-bottom: 1px solid rgba(230, 241, 255, 0.08);
  margin-bottom: 8px;
}

.timeline-ruler {
  position: relative;
  height: 100%;
}

.tick {
  position: absolute;
  bottom: 0;
  transform: translateX(-50%);
}

.tick-line {
  width: 1px;
  height: 8px;
  background: rgba(230, 241, 255, 0.2);
  margin: 0 auto;
}

.tick-label {
  display: block;
  font-size: 10px;
  color: rgba(230, 241, 255, 0.5);
  text-align: center;
  white-space: nowrap;
  transform: translateY(-16px);
}
</style>
