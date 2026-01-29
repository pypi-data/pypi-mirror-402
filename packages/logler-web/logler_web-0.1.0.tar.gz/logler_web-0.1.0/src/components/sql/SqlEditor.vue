<script setup lang="ts">
import { NInput, NButton, NSpace } from 'naive-ui'
import { PhPlay, PhX } from '@phosphor-icons/vue'

const model = defineModel<string>({ default: '' })

defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  execute: []
  clear: []
}>()

function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault()
    emit('execute')
  }
}
</script>

<template>
  <div class="sql-editor">
    <NInput
      v-model:value="model"
      type="textarea"
      placeholder="Enter SQL query... (Ctrl+Enter to execute)"
      :rows="4"
      :disabled="loading"
      class="query-input"
      @keydown="handleKeydown"
    />
    <NSpace class="editor-actions" justify="end">
      <NButton
        secondary
        size="small"
        :disabled="loading || !model"
        @click="emit('clear')"
      >
        <template #icon>
          <PhX weight="regular" />
        </template>
        Clear
      </NButton>
      <NButton
        type="primary"
        size="small"
        :loading="loading"
        :disabled="!model"
        @click="emit('execute')"
      >
        <template #icon>
          <PhPlay weight="fill" />
        </template>
        Execute
      </NButton>
    </NSpace>
  </div>
</template>

<style scoped>
.sql-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.query-input :deep(textarea) {
  font-family: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
}

.editor-actions {
  padding-top: 4px;
}
</style>
