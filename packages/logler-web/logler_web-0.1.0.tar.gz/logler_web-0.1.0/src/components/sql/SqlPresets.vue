<script setup lang="ts">
import { NSpace, NButton } from 'naive-ui'
import { PhLightning } from '@phosphor-icons/vue'

const emit = defineEmits<{
  select: [query: string]
}>()

const presets = [
  {
    label: 'All Errors',
    query: `SELECT * FROM logs WHERE level IN ('ERROR', 'CRITICAL', 'FATAL') LIMIT 100`,
  },
  {
    label: 'By Thread',
    query: `SELECT thread_id, COUNT(*) as count FROM logs GROUP BY thread_id ORDER BY count DESC`,
  },
  {
    label: 'By Level',
    query: `SELECT level, COUNT(*) as count FROM logs GROUP BY level ORDER BY count DESC`,
  },
  {
    label: 'Recent Logs',
    query: `SELECT timestamp, level, message FROM logs ORDER BY timestamp DESC LIMIT 50`,
  },
]
</script>

<template>
  <div class="sql-presets">
    <span class="presets-label">
      <PhLightning weight="regular" :size="14" />
      Quick:
    </span>
    <NSpace size="small">
      <NButton
        v-for="preset in presets"
        :key="preset.label"
        size="tiny"
        quaternary
        @click="emit('select', preset.query)"
      >
        {{ preset.label }}
      </NButton>
    </NSpace>
  </div>
</template>

<style scoped>
.sql-presets {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.presets-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(230, 241, 255, 0.58);
}
</style>
