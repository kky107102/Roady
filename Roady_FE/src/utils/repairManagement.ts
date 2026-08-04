import type { DamageListItem } from '@/types/damage'

export type RepairStatusFilter = 'requested' | 'in_progress' | 'completed'
export type RepairSort = 'priority' | 'latest' | 'oldest'

export const REPAIR_STATUS_FILTERS: readonly RepairStatusFilter[] = [
  'requested',
  'in_progress',
  'completed',
] as const

export const REPAIR_SORT_OPTIONS: { value: RepairSort; label: string }[] = [
  { value: 'priority', label: '우선순위 높은 순' },
  { value: 'latest', label: '최신순' },
  { value: 'oldest', label: '오래된 순' },
]

const REPAIR_STATUSES = new Set(['REQUESTED', 'REPAIR_IN_PROGRESS', 'REPAIR_COMPLETED'])

const PRIORITY_ORDER: Record<string, number> = {
  URGENT: 0,
  HIGH: 1,
  NORMAL: 2,
  MEDIUM: 2,
  LOW: 3,
}

export function isRepairItem(item: DamageListItem): boolean {
  return REPAIR_STATUSES.has(item.currentStatus)
}

export function repairStatusCategory(item: DamageListItem): RepairStatusFilter | null {
  if (item.currentStatus === 'REQUESTED') return 'requested'
  if (item.currentStatus === 'REPAIR_IN_PROGRESS') return 'in_progress'
  if (item.currentStatus === 'REPAIR_COMPLETED') return 'completed'
  return null
}

function detectedAt(item: DamageListItem): number {
  const value = Date.parse(item.capturedAt ?? item.createdAt)
  return Number.isNaN(value) ? 0 : value
}

export function sortRepairItems(
  items: DamageListItem[],
  sort: RepairSort = 'priority',
): DamageListItem[] {
  return [...items].sort((a, b) => {
    if (sort === 'latest') return detectedAt(b) - detectedAt(a) || b.id - a.id
    if (sort === 'oldest') return detectedAt(a) - detectedAt(b) || a.id - b.id

    const aRank = PRIORITY_ORDER[a.processingPriority ?? ''] ?? 4
    const bRank = PRIORITY_ORDER[b.processingPriority ?? ''] ?? 4
    if (aRank !== bRank) return aRank - bRank
    return detectedAt(b) - detectedAt(a) || b.id - a.id
  })
}

// ── URL ↔ 필터 상태 변환 ──────────────────────────────────

const STATUS_TO_FILTER: Record<string, RepairStatusFilter> = {
  REQUESTED: 'requested',
  REPAIR_IN_PROGRESS: 'in_progress',
  REPAIR_COMPLETED: 'completed',
}

const FILTER_TO_STATUS: Record<RepairStatusFilter, string> = {
  requested: 'REQUESTED',
  in_progress: 'REPAIR_IN_PROGRESS',
  completed: 'REPAIR_COMPLETED',
}

export function parseStatusesParam(
  param: string | string[] | null | undefined,
): RepairStatusFilter[] {
  if (!param) return [...REPAIR_STATUS_FILTERS]
  const raw = Array.isArray(param) ? param.join(',') : param
  const parsed = raw
    .split(',')
    .map((s) => STATUS_TO_FILTER[s.trim()])
    .filter((s): s is RepairStatusFilter => s != null)
  return parsed.length > 0 ? parsed : [...REPAIR_STATUS_FILTERS]
}

export function statusesToParam(
  statuses: RepairStatusFilter[],
): string | undefined {
  if (statuses.length === REPAIR_STATUS_FILTERS.length) return undefined
  return statuses.map((s) => FILTER_TO_STATUS[s]).join(',')
}

export function parseSortParam(param: string | string[] | null | undefined): RepairSort {
  const raw = Array.isArray(param) ? param[0] : param
  if (raw === 'latest' || raw === 'oldest') return raw
  return 'priority'
}
