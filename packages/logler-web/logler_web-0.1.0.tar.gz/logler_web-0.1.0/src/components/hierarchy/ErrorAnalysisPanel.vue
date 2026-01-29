<script setup lang="ts">
import { NCard, NCollapse, NCollapseItem, NText, NTag, NSpace, NList, NListItem } from 'naive-ui'
import { PhWarning, PhLightning, PhArrowRight } from '@phosphor-icons/vue'
import type { ErrorAnalysis } from '@/api/types'

defineProps<{
  analysis: ErrorAnalysis
}>()
</script>

<template>
  <NCard class="error-analysis-panel" size="small">
    <template #header>
      <NSpace align="center" size="small">
        <PhWarning weight="fill" :size="18" class="error-icon" />
        <span>Error Analysis</span>
      </NSpace>
    </template>

    <NCollapse default-expanded-names="root-cause">
      <NCollapseItem v-if="analysis.root_cause" name="root-cause" title="Root Cause">
        <NText class="mono-text">{{ analysis.root_cause }}</NText>
      </NCollapseItem>

      <NCollapseItem v-if="analysis.error_chain.length > 0" name="error-chain" title="Error Chain">
        <div class="error-chain">
          <div
            v-for="(error, index) in analysis.error_chain"
            :key="index"
            class="chain-item"
          >
            <PhArrowRight v-if="index > 0" weight="regular" :size="14" class="chain-arrow" />
            <NTag size="small" :bordered="false">
              {{ error }}
            </NTag>
          </div>
        </div>
      </NCollapseItem>

      <NCollapseItem v-if="analysis.recommendations.length > 0" name="recommendations" title="Recommendations">
        <NList :bordered="false" size="small">
          <NListItem v-for="(rec, index) in analysis.recommendations" :key="index">
            <NSpace align="center" size="small">
              <PhLightning weight="regular" :size="14" class="rec-icon" />
              <NText>{{ rec }}</NText>
            </NSpace>
          </NListItem>
        </NList>
      </NCollapseItem>

      <NCollapseItem v-if="analysis.impact_summary" name="impact" title="Impact Summary">
        <NText depth="2">{{ analysis.impact_summary }}</NText>
      </NCollapseItem>
    </NCollapse>
  </NCard>
</template>

<style scoped>
.error-analysis-panel {
  border-left: 3px solid #ff3b3b;
}

.error-icon {
  color: #ff3b3b;
}

.mono-text {
  font-family: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
}

.error-chain {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.chain-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.chain-arrow {
  color: rgba(230, 241, 255, 0.38);
}

.rec-icon {
  color: #ffcc00;
}
</style>
