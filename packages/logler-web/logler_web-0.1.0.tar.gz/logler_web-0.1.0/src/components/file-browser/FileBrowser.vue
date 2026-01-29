<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  NModal,
  NTabs,
  NTabPane,
  NInput,
  NButton,
  NSpace,
  NList,
  NListItem,
  NText,
  NIcon,
  NScrollbar,
  NSpin,
  NEmpty,
  NCheckbox,
} from 'naive-ui'
import {
  PhFolder,
  PhFile,
  PhArrowLeft,
  PhMagnifyingGlass,
  PhFileText,
} from '@phosphor-icons/vue'
import { useFilesStore } from '@/stores/files'
import { useLogsStore } from '@/stores/logs'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const filesStore = useFilesStore()
const logsStore = useLogsStore()

const mode = ref<'browse' | 'glob'>('browse')
const globInput = ref('')
const selectedFiles = ref<Set<string>>(new Set())
const loading = ref(false)

// Preset glob patterns
const presets = ['*.log', '**/*.log', '**/app-*.log', '**/*error*.log']

// Initialize browser when modal opens
watch(
  () => props.show,
  async (show) => {
    if (show && !filesStore.currentDir) {
      loading.value = true
      try {
        await filesStore.browse()
      } finally {
        loading.value = false
      }
    }
  }
)

async function navigateTo(path: string) {
  loading.value = true
  try {
    await filesStore.browse(path)
  } finally {
    loading.value = false
  }
}

async function goUp() {
  if (filesStore.parentDir) {
    await navigateTo(filesStore.parentDir)
  }
}

async function searchGlob() {
  if (!globInput.value) return
  loading.value = true
  try {
    await filesStore.searchGlob(globInput.value, filesStore.currentDir)
  } finally {
    loading.value = false
  }
}

function toggleFileSelection(path: string) {
  if (selectedFiles.value.has(path)) {
    selectedFiles.value.delete(path)
  } else {
    selectedFiles.value.add(path)
  }
}

async function openSelectedFiles() {
  const paths = Array.from(selectedFiles.value)
  if (paths.length === 0) return

  if (paths.length === 1) {
    await logsStore.openFile(paths[0])
  } else {
    await logsStore.openMany(paths)
  }

  selectedFiles.value.clear()
  emit('update:show', false)
}

async function openSingleFile(path: string) {
  await logsStore.openFile(path)
  emit('update:show', false)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function close() {
  emit('update:show', false)
}
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    title="Open Log File"
    style="width: 700px; max-width: 90vw;"
    @update:show="emit('update:show', $event)"
  >
    <NSpin :show="loading">
      <NTabs v-model:value="mode" type="line" size="small">
        <NTabPane name="browse" tab="Browse">
          <!-- Navigation -->
          <NSpace align="center" style="margin-bottom: 12px;">
            <NButton
              size="small"
              :disabled="!filesStore.parentDir"
              @click="goUp"
            >
              <template #icon>
                <PhArrowLeft />
              </template>
            </NButton>
            <NText depth="3" style="font-family: monospace; font-size: 12px;">
              {{ filesStore.currentDir }}
            </NText>
          </NSpace>

          <!-- Directory and File List -->
          <NScrollbar style="max-height: 400px;">
            <NList hoverable clickable>
              <!-- Directories -->
              <NListItem
                v-for="dir in filesStore.directories"
                :key="dir.path"
                @click="navigateTo(dir.path)"
              >
                <template #prefix>
                  <NIcon :component="PhFolder" :size="20" color="#ffcc00" />
                </template>
                <NText>{{ dir.name }}</NText>
              </NListItem>

              <!-- Files -->
              <NListItem
                v-for="file in filesStore.files"
                :key="file.path"
                @click="openSingleFile(file.path)"
              >
                <template #prefix>
                  <NCheckbox
                    :checked="selectedFiles.has(file.path)"
                    @click.stop
                    @update:checked="toggleFileSelection(file.path)"
                  />
                </template>
                <template #suffix>
                  <NText depth="3" style="font-size: 12px;">
                    {{ formatSize(file.size) }}
                  </NText>
                </template>
                <NSpace align="center" :size="8">
                  <NIcon
                    :component="file.is_log ? PhFileText : PhFile"
                    :size="18"
                    :color="file.is_log ? '#a8ff60' : '#808080'"
                  />
                  <NText>{{ file.name }}</NText>
                </NSpace>
              </NListItem>
            </NList>

            <NEmpty
              v-if="filesStore.files.length === 0 && filesStore.directories.length === 0"
              description="Empty directory"
            />
          </NScrollbar>
        </NTabPane>

        <NTabPane name="glob" tab="Search">
          <!-- Glob Search Input -->
          <NSpace vertical :size="12">
            <NInput
              v-model:value="globInput"
              placeholder="Enter glob pattern (e.g., **/*.log)"
              @keyup.enter="searchGlob"
            >
              <template #prefix>
                <PhMagnifyingGlass :size="16" />
              </template>
              <template #suffix>
                <NButton size="tiny" @click="searchGlob">Search</NButton>
              </template>
            </NInput>

            <!-- Preset Patterns -->
            <NSpace :size="8">
              <NButton
                v-for="preset in presets"
                :key="preset"
                size="tiny"
                secondary
                @click="globInput = preset; searchGlob()"
              >
                {{ preset }}
              </NButton>
            </NSpace>

            <!-- Results -->
            <NScrollbar style="max-height: 350px;">
              <NList v-if="filesStore.globResults.length > 0" hoverable clickable>
                <NListItem
                  v-for="file in filesStore.globResults"
                  :key="file.path"
                  @click="openSingleFile(file.path)"
                >
                  <template #prefix>
                    <NCheckbox
                      :checked="selectedFiles.has(file.path)"
                      @click.stop
                      @update:checked="toggleFileSelection(file.path)"
                    />
                  </template>
                  <template #suffix>
                    <NText depth="3" style="font-size: 12px;">
                      {{ formatSize(file.size) }}
                    </NText>
                  </template>
                  <NText style="font-family: monospace; font-size: 12px;">
                    {{ file.path }}
                  </NText>
                </NListItem>
              </NList>

              <NEmpty
                v-else-if="filesStore.globPattern"
                description="No files match the pattern"
              />
            </NScrollbar>
          </NSpace>
        </NTabPane>
      </NTabs>
    </NSpin>

    <template #footer>
      <NSpace justify="space-between">
        <NText v-if="selectedFiles.size > 0" depth="3">
          {{ selectedFiles.size }} file(s) selected
        </NText>
        <span v-else />
        <NSpace>
          <NButton @click="close">Cancel</NButton>
          <NButton
            type="primary"
            :disabled="selectedFiles.size === 0"
            @click="openSelectedFiles"
          >
            Open Selected ({{ selectedFiles.size }})
          </NButton>
        </NSpace>
      </NSpace>
    </template>
  </NModal>
</template>
