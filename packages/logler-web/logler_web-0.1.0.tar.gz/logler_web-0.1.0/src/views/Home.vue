<script setup lang="ts">
import { NLayout, NLayoutHeader, NLayoutSider, NLayoutContent } from 'naive-ui'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import MainContent from '@/components/layout/MainContent.vue'
import FileBrowser from '@/components/file-browser/FileBrowser.vue'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()
</script>

<template>
  <n-layout class="app-layout" has-sider position="absolute">
    <n-layout-sider
      bordered
      :width="280"
      content-style="padding: 0;"
      :native-scrollbar="false"
    >
      <AppSidebar />
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered style="height: 56px; padding: 0 16px;">
        <AppHeader />
      </n-layout-header>

      <n-layout-content content-style="padding: 0;">
        <MainContent />
      </n-layout-content>
    </n-layout>

    <!-- File Browser Modal -->
    <FileBrowser
      v-model:show="uiStore.showFileBrowser"
    />
  </n-layout>
</template>

<style scoped>
.app-layout {
  height: 100vh;
}
</style>
