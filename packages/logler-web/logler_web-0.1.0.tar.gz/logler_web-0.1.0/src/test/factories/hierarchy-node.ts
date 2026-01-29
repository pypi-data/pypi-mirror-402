import type { HierarchyNode, ErrorAnalysis } from '@/api/types'

interface HierarchyNodeOverrides {
  id?: string
  label?: string
  entry_count?: number
  error_count?: number
  start_time?: string | null
  end_time?: string | null
  duration_ms?: number | null
  children?: HierarchyNode[]
}

let nodeIdCounter = 0

export function createHierarchyNode(overrides: HierarchyNodeOverrides = {}): HierarchyNode {
  nodeIdCounter++
  const id = overrides.id ?? `node-${nodeIdCounter}`

  return {
    id,
    label: overrides.label ?? `Node ${nodeIdCounter}`,
    entry_count: overrides.entry_count ?? 10,
    error_count: overrides.error_count ?? 0,
    start_time: overrides.start_time ?? '2024-01-15T10:00:00.000Z',
    end_time: overrides.end_time ?? '2024-01-15T10:00:01.000Z',
    duration_ms: overrides.duration_ms ?? 1000,
    children: overrides.children ?? [],
  }
}

export function createHierarchyTree(depth: number, childrenPerNode: number = 2): HierarchyNode {
  function buildLevel(currentDepth: number): HierarchyNode {
    const children =
      currentDepth < depth
        ? Array.from({ length: childrenPerNode }, () => buildLevel(currentDepth + 1))
        : []

    return createHierarchyNode({
      children,
      entry_count: 5 + currentDepth * 2,
      error_count: currentDepth === depth ? 1 : 0,
    })
  }

  return buildLevel(0)
}

export function createErrorAnalysis(overrides: Partial<ErrorAnalysis> = {}): ErrorAnalysis {
  return {
    root_cause: overrides.root_cause ?? 'Connection timeout',
    error_chain: overrides.error_chain ?? ['Service unavailable', 'Connection timeout'],
    recommendations: overrides.recommendations ?? ['Check network connectivity', 'Verify service health'],
    impact_summary: overrides.impact_summary ?? 'Partial service degradation affecting 5% of requests',
  }
}

export function resetNodeIdCounter(): void {
  nodeIdCounter = 0
}
