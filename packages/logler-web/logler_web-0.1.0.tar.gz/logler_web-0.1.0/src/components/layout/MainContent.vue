<script setup lang="ts">
import { NTabs, NTabPane, NEmpty, NSpin } from 'naive-ui'
import { PhListBullets, PhTreeStructure, PhChartBar, PhDatabase } from '@phosphor-icons/vue'
import { useUiStore } from '@/stores/ui'
import { useFilesStore } from '@/stores/files'
import LogViewer from '@/components/log-viewer/LogViewer.vue'
import HierarchyView from '@/components/hierarchy/HierarchyView.vue'
import WaterfallView from '@/components/waterfall/WaterfallView.vue'
import SqlView from '@/components/sql/SqlView.vue'

const uiStore = useUiStore()
const filesStore = useFilesStore()

function handleTabChange(value: string) {
  uiStore.setViewMode(value as 'logs' | 'hierarchy' | 'waterfall' | 'sql')
}
</script>

<template>
  <div class="main-content">
    <NSpin :show="uiStore.loading" style="height: 100%;">
      <template v-if="filesStore.hasActiveFiles">
        <NTabs
          :value="uiStore.viewMode"
          type="line"
          size="small"
          style="height: 100%;"
          pane-style="height: calc(100% - 40px); padding: 0;"
          @update:value="handleTabChange"
        >
          <NTabPane name="logs" tab="Logs">
            <template #tab>
              <PhListBullets :size="16" style="margin-right: 4px;" />
              Logs
            </template>
            <LogViewer />
          </NTabPane>

          <NTabPane name="hierarchy" tab="Hierarchy">
            <template #tab>
              <PhTreeStructure :size="16" style="margin-right: 4px;" />
              Hierarchy
            </template>
            <HierarchyView />
          </NTabPane>

          <NTabPane name="waterfall" tab="Waterfall">
            <template #tab>
              <PhChartBar :size="16" style="margin-right: 4px;" />
              Waterfall
            </template>
            <WaterfallView />
          </NTabPane>

          <NTabPane name="sql" tab="SQL">
            <template #tab>
              <PhDatabase :size="16" style="margin-right: 4px;" />
              SQL
            </template>
            <SqlView />
          </NTabPane>
        </NTabs>
      </template>

      <template v-else>
        <div class="empty-state">
          <NEmpty description="No file opened">
            <template #extra>
              Click "Open File" to get started
            </template>
          </NEmpty>
        </div>
      </template>
    </NSpin>
  </div>
</template>

<style scoped>
.main-content {
  height: 100%;
  overflow: hidden;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
