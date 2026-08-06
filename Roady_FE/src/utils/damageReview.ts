import type { DamageListItem, DamageStatus } from '@/types/damage'

export type ReviewTab = 'pending' | 'confirmed'
export type DamageSort = 'latest' | 'oldest' | 'priority'
export type ConfirmedStatusFilter = 'requested' | 'in_progress' | 'completed'

const REVIEW_CONFIRMED_STATUSES = new Set<DamageStatus>([
  'REQUESTED',
  'REPAIR_IN_PROGRESS',
  'REPAIR_COMPLETED',
  'CANCELED',
])

const PRIORITY_ORDER: Record<string, number> = {
  URGENT: 0,
  HIGH: 1,
  NORMAL: 2,
  MEDIUM: 2,
  LOW: 3,
}

export function isReviewVisible(item: DamageListItem): boolean {
  return !['COLLECTED', 'AI_ANALYZING'].includes(item.currentStatus)
}

export function isReviewConfirmed(item: DamageListItem): boolean {
  return REVIEW_CONFIRMED_STATUSES.has(item.currentStatus)
}

export function reviewTabForDamage(item: DamageListItem): ReviewTab {
  return isReviewConfirmed(item) ? 'confirmed' : 'pending'
}

export function defaultDamageSort(tab: ReviewTab): DamageSort {
  return tab === 'confirmed' ? 'priority' : 'latest'
}

function detectedAt(item: DamageListItem): number {
  const value = Date.parse(item.capturedAt ?? item.createdAt)
  return Number.isNaN(value) ? 0 : value
}

function priorityOf(item: DamageListItem, tab: ReviewTab): string | null {
  return tab === 'confirmed' ? (item.processingPriority ?? null) : item.repairPriority
}

export function sortReviewDamages(
  items: DamageListItem[],
  tab: ReviewTab,
  sort: DamageSort,
): DamageListItem[] {
  return [...items].sort((left, right) => {
    if (sort === 'latest') return detectedAt(right) - detectedAt(left) || right.id - left.id
    if (sort === 'oldest') return detectedAt(left) - detectedAt(right) || left.id - right.id

    const leftRank = PRIORITY_ORDER[priorityOf(left, tab) ?? ''] ?? 4
    const rightRank = PRIORITY_ORDER[priorityOf(right, tab) ?? ''] ?? 4
    return leftRank - rightRank || detectedAt(right) - detectedAt(left) || right.id - left.id
  })
}
