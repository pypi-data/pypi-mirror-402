<script setup lang="ts">
import { computed } from 'vue'
import { NSelect, NButton, NSpace, NInput } from 'naive-ui'
import { PhTreeStructure } from '@phosphor-icons/vue'
import { useThreadsStore } from '@/stores/threads'

const model = defineModel<string>({ default: '' })

defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  build: []
}>()

const threadsStore = useThreadsStore()

const threadOptions = computed(() => {
  return threadsStore.threads.map((t) => ({
    label: `${t.thread_id} (${t.log_count} logs${t.error_count > 0 ? `, ${t.error_count} errors` : ''})`,
    value: t.thread_id,
  }))
})

function handleBuild() {
  if (model.value) {
    emit('build')
  }
}
</script>

<template>
  <div class="hierarchy-selector">
    <NSpace align="center">
      <NSelect
        v-if="threadOptions.length > 0"
        v-model:value="model"
        :options="threadOptions"
        placeholder="Select a thread..."
        filterable
        clearable
        style="min-width: 300px;"
        :disabled="loading"
      />
      <NInput
        v-else
        v-model:value="model"
        placeholder="Enter thread/trace identifier..."
        style="min-width: 300px;"
        :disabled="loading"
        @keyup.enter="handleBuild"
      />
      <NButton
        type="primary"
        :loading="loading"
        :disabled="!model"
        @click="handleBuild"
      >
        <template #icon>
          <PhTreeStructure weight="regular" />
        </template>
        Build Hierarchy
      </NButton>
    </NSpace>
  </div>
</template>

<style scoped>
.hierarchy-selector {
  padding: 12px;
  border-bottom: 1px solid rgba(230, 241, 255, 0.08);
}
</style>
