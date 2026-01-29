<script setup lang="ts">
import { ref } from 'vue'
import { NCard } from 'naive-ui'
import SqlEditor from './SqlEditor.vue'
import SqlPresets from './SqlPresets.vue'
import SqlResults from './SqlResults.vue'
import { api } from '@/api/client'
import type { SqlResponse } from '@/api/types'

const query = ref('')
const loading = ref(false)
const results = ref<SqlResponse | null>(null)

async function executeQuery() {
  if (!query.value.trim()) return

  loading.value = true
  results.value = null

  try {
    results.value = await api.executeSql({ query: query.value })
  } catch (err) {
    results.value = {
      columns: [],
      rows: [],
      row_count: 0,
      error: err instanceof Error ? err.message : 'Unknown error',
    }
  } finally {
    loading.value = false
  }
}

function handlePresetSelect(presetQuery: string) {
  query.value = presetQuery
}

function handleClear() {
  query.value = ''
  results.value = null
}
</script>

<template>
  <div class="sql-view">
    <div class="editor-section">
      <NCard size="small" :bordered="false">
        <SqlPresets @select="handlePresetSelect" />
        <SqlEditor
          v-model="query"
          :loading="loading"
          @execute="executeQuery"
          @clear="handleClear"
        />
      </NCard>
    </div>
    <div class="results-section">
      <SqlResults :data="results" :loading="loading" />
    </div>
  </div>
</template>

<style scoped>
.sql-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px;
  gap: 12px;
}

.editor-section {
  flex-shrink: 0;
}

.results-section {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
