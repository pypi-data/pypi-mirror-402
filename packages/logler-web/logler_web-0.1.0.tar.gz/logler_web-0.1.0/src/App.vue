<script setup lang="ts">
import { NConfigProvider, darkTheme, NGlobalStyle, NMessageProvider, NDialogProvider, NNotificationProvider } from 'naive-ui'
import { createDsNaiveThemeOverrides } from '@/design/naive-theme'
import { providePhosphorDefaults } from '@/design/icons'
import Home from '@/views/Home.vue'

// Provide Phosphor icon defaults during setup (CRITICAL: not onMounted)
providePhosphorDefaults()

// Create theme overrides from design tokens
const themeOverrides = createDsNaiveThemeOverrides('dark')
</script>

<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-global-style />
    <n-notification-provider>
      <n-dialog-provider>
        <n-message-provider>
          <Home />
        </n-message-provider>
      </n-dialog-provider>
    </n-notification-provider>
  </n-config-provider>
</template>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
