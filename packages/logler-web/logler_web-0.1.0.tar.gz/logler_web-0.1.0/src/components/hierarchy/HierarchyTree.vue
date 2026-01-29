<script setup lang="ts">
import { computed, h } from 'vue'
import { NTree, NTag, NSpace, NText } from 'naive-ui'
import type { TreeOption } from 'naive-ui'
import type { HierarchyNode } from '@/api/types'

const props = defineProps<{
  hierarchy: HierarchyNode
}>()

function formatDuration(ms: number | null): string {
  if (ms === null) return ''
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
}

function convertToTreeOptions(node: HierarchyNode): TreeOption {
  const duration = formatDuration(node.duration_ms)

  return {
    key: node.id,
    label: node.label || node.id,
    isLeaf: node.children.length === 0,
    children: node.children.length > 0 ? node.children.map(convertToTreeOptions) : undefined,
    prefix: () =>
      h(NSpace, { size: 'small', align: 'center' }, () => [
        h(
          NTag,
          { size: 'tiny', type: 'success', bordered: false },
          () => `${node.entry_count}`
        ),
        node.error_count > 0
          ? h(
              NTag,
              { size: 'tiny', type: 'error', bordered: false },
              () => `${node.error_count} err`
            )
          : null,
      ]),
    suffix: () =>
      duration
        ? h(NText, { depth: 3, style: { fontSize: '11px' } }, () => duration)
        : null,
  }
}

const treeData = computed<TreeOption[]>(() => {
  return [convertToTreeOptions(props.hierarchy)]
})
</script>

<template>
  <div class="hierarchy-tree">
    <NTree
      :data="treeData"
      block-line
      expand-on-click
      default-expand-all
      selectable
    />
  </div>
</template>

<style scoped>
.hierarchy-tree {
  height: 100%;
  overflow: auto;
  padding: 12px;
}

.hierarchy-tree :deep(.n-tree-node-content__text) {
  font-family: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
}
</style>
