<script setup lang="ts">
import { NButton, NSpace, NTag, NText, NBadge } from 'naive-ui'
import { PhFolderOpen, PhPlugsConnected, PhPlugs } from '@phosphor-icons/vue'
import { useUiStore } from '@/stores/ui'
import { useFilesStore } from '@/stores/files'
import { useLogsStore } from '@/stores/logs'

const uiStore = useUiStore()
const filesStore = useFilesStore()
const logsStore = useLogsStore()
</script>

<template>
  <div class="header-container">
    <div class="header-left">
      <NSpace align="center" :size="12">
        <img src="/favicon.svg" alt="Logler" class="logo" width="28" height="28" />
        <NText strong style="font-size: 18px;">Logler</NText>

        <NButton
          type="primary"
          size="small"
          @click="uiStore.openFileBrowser"
        >
          <template #icon>
            <PhFolderOpen weight="bold" />
          </template>
          Open File
        </NButton>
      </NSpace>
    </div>

    <div class="header-center">
      <NSpace v-if="filesStore.hasActiveFiles" align="center" :size="8">
        <NTag
          v-for="file in filesStore.activeFiles"
          :key="file"
          size="small"
          :bordered="false"
        >
          {{ file.split('/').pop() }}
        </NTag>
        <NText depth="3" v-if="logsStore.partialLoad">
          ({{ logsStore.totalAvailable.toLocaleString() }} total, quick load)
        </NText>
      </NSpace>
    </div>

    <div class="header-right">
      <NSpace align="center" :size="12">
        <NBadge :dot="true" :type="uiStore.wsConnected ? 'success' : 'error'">
          <component
            :is="uiStore.wsConnected ? PhPlugsConnected : PhPlugs"
            :size="20"
            weight="regular"
          />
        </NBadge>
      </NSpace>
    </div>
  </div>
</template>

<style scoped>
.header-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.header-left,
.header-center,
.header-right {
  display: flex;
  align-items: center;
}

.header-center {
  flex: 1;
  justify-content: center;
}

.logo {
  border-radius: 4px;
}
</style>
