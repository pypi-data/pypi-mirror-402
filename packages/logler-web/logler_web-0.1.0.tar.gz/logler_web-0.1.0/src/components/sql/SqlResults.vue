<script setup lang="ts">
import { computed } from 'vue'
import { NDataTable, NAlert, NText } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { SqlResponse } from '@/api/types'

const props = defineProps<{
  data: SqlResponse | null
  loading?: boolean
}>()

const columns = computed<DataTableColumns>(() => {
  if (!props.data?.columns) return []
  return props.data.columns.map((col) => ({
    title: col,
    key: col,
    ellipsis: {
      tooltip: true,
    },
    resizable: true,
    minWidth: 80,
  }))
})

const rows = computed(() => {
  if (!props.data?.rows) return []
  return props.data.rows.map((row, index) => ({
    ...row,
    _key: index,
  }))
})
</script>

<template>
  <div class="sql-results">
    <NAlert v-if="data?.error" type="error" :bordered="false">
      {{ data.error }}
    </NAlert>

    <template v-else-if="data">
      <NDataTable
        :columns="columns"
        :data="rows"
        :row-key="(row: Record<string, unknown>) => row._key as string | number"
        :loading="loading"
        :bordered="false"
        :single-line="false"
        size="small"
        flex-height
        class="results-table"
      />
      <div class="results-footer">
        <NText depth="3">{{ data.row_count }} row{{ data.row_count === 1 ? '' : 's' }}</NText>
      </div>
    </template>

    <div v-else class="empty-results">
      <NText depth="3">Execute a query to see results</NText>
    </div>
  </div>
</template>

<style scoped>
.sql-results {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.results-table {
  flex: 1;
  min-height: 0;
}

.results-table :deep(td) {
  font-family: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
}

.results-footer {
  padding: 8px;
  border-top: 1px solid rgba(230, 241, 255, 0.08);
  font-size: 12px;
}

.empty-results {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 100px;
}
</style>
