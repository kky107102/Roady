import { describe, it, expect } from 'vitest'
import type { DamageListItem } from '@/types/damage'
import {
  isRepairItem,
  repairStatusCategory,
  sortRepairItems,
  parseStatusesParam,
  statusesToParam,
  parseSortParam,
  REPAIR_STATUS_FILTERS,
} from './repairManagement'

function makeItem(overrides: Partial<DamageListItem>): DamageListItem {
  return {
    id: 1,
    robotId: null,
    assignedTo: null,
    description: null,
    latitude: null,
    longitude: null,
    capturedAt: null,
    currentStatus: 'REQUESTED',
    processingPriority: null,
    imageCount: 0,
    damageScore: null,
    repairRequired: null,
    repairPriority: null,
    confidenceScore: null,
    createdAt: '2025-01-01T00:00:00Z',
    ...overrides,
  }
}

// ── isRepairItem ──────────────────────────────────────────

describe('isRepairItem', () => {
  it.each(['REQUESTED', 'REPAIR_IN_PROGRESS', 'REPAIR_COMPLETED'] as const)(
    'returns true for %s',
    (status) => {
      expect(isRepairItem(makeItem({ currentStatus: status }))).toBe(true)
    },
  )

  it.each(['COLLECTED', 'AI_ANALYZING', 'AI_ANALYZED', 'CANCELED'] as const)(
    'returns false for %s',
    (status) => {
      expect(isRepairItem(makeItem({ currentStatus: status }))).toBe(false)
    },
  )
})

// ── repairStatusCategory ──────────────────────────────────

describe('repairStatusCategory', () => {
  it('maps REQUESTED → requested', () => {
    expect(repairStatusCategory(makeItem({ currentStatus: 'REQUESTED' }))).toBe('requested')
  })

  it('maps REPAIR_IN_PROGRESS → in_progress', () => {
    expect(repairStatusCategory(makeItem({ currentStatus: 'REPAIR_IN_PROGRESS' }))).toBe(
      'in_progress',
    )
  })

  it('maps REPAIR_COMPLETED → completed', () => {
    expect(repairStatusCategory(makeItem({ currentStatus: 'REPAIR_COMPLETED' }))).toBe('completed')
  })

  it('returns null for non-repair statuses', () => {
    expect(repairStatusCategory(makeItem({ currentStatus: 'AI_ANALYZED' }))).toBeNull()
    expect(repairStatusCategory(makeItem({ currentStatus: 'CANCELED' }))).toBeNull()
  })
})

// ── sortRepairItems ───────────────────────────────────────

describe('sortRepairItems', () => {
  it('sorts by priority: URGENT → HIGH → NORMAL → LOW → 미지정 (default)', () => {
    const items = [
      makeItem({ id: 5, processingPriority: null }),
      makeItem({ id: 4, processingPriority: 'LOW' }),
      makeItem({ id: 3, processingPriority: 'NORMAL' }),
      makeItem({ id: 2, processingPriority: 'HIGH' }),
      makeItem({ id: 1, processingPriority: 'URGENT' }),
    ]

    const sorted = sortRepairItems(items, 'priority')
    expect(sorted.map((i) => i.id)).toEqual([1, 2, 3, 4, 5])
  })

  it('places null/undefined priority last', () => {
    const items = [
      makeItem({ id: 1, processingPriority: null }),
      makeItem({ id: 2, processingPriority: 'URGENT' }),
    ]
    const sorted = sortRepairItems(items, 'priority')
    expect(sorted[0]!.id).toBe(2)
    expect(sorted[1]!.id).toBe(1)
  })

  it('breaks ties within same priority by capturedAt descending', () => {
    const items = [
      makeItem({ id: 1, processingPriority: 'HIGH', capturedAt: '2025-01-01T00:00:00Z' }),
      makeItem({ id: 2, processingPriority: 'HIGH', capturedAt: '2025-06-01T00:00:00Z' }),
    ]
    const sorted = sortRepairItems(items, 'priority')
    expect(sorted[0]!.id).toBe(2)
    expect(sorted[1]!.id).toBe(1)
  })

  it('breaks ties by id descending when capturedAt is equal', () => {
    const items = [
      makeItem({ id: 1, processingPriority: 'NORMAL', capturedAt: '2025-01-01T00:00:00Z' }),
      makeItem({ id: 2, processingPriority: 'NORMAL', capturedAt: '2025-01-01T00:00:00Z' }),
    ]
    const sorted = sortRepairItems(items, 'priority')
    expect(sorted[0]!.id).toBe(2)
    expect(sorted[1]!.id).toBe(1)
  })

  it('does not mutate the original array', () => {
    const items = [
      makeItem({ id: 2, processingPriority: 'HIGH' }),
      makeItem({ id: 1, processingPriority: 'URGENT' }),
    ]
    const original = [...items]
    sortRepairItems(items, 'priority')
    expect(items[0]!.id).toBe(original[0]!.id)
    expect(items[1]!.id).toBe(original[1]!.id)
  })

  it('treats MEDIUM priority same as NORMAL', () => {
    const items = [
      makeItem({ id: 1, processingPriority: 'MEDIUM' }),
      makeItem({ id: 2, processingPriority: 'HIGH' }),
      makeItem({ id: 3, processingPriority: 'LOW' }),
    ]
    const sorted = sortRepairItems(items, 'priority')
    expect(sorted[0]!.id).toBe(2)
    expect(sorted[2]!.id).toBe(3)
  })

  it('latest: sorts by capturedAt descending', () => {
    const items = [
      makeItem({ id: 1, capturedAt: '2025-01-01T00:00:00Z' }),
      makeItem({ id: 2, capturedAt: '2025-06-01T00:00:00Z' }),
      makeItem({ id: 3, capturedAt: '2025-03-01T00:00:00Z' }),
    ]
    const sorted = sortRepairItems(items, 'latest')
    expect(sorted.map((i) => i.id)).toEqual([2, 3, 1])
  })

  it('oldest: sorts by capturedAt ascending', () => {
    const items = [
      makeItem({ id: 1, capturedAt: '2025-01-01T00:00:00Z' }),
      makeItem({ id: 2, capturedAt: '2025-06-01T00:00:00Z' }),
      makeItem({ id: 3, capturedAt: '2025-03-01T00:00:00Z' }),
    ]
    const sorted = sortRepairItems(items, 'oldest')
    expect(sorted.map((i) => i.id)).toEqual([1, 3, 2])
  })

  it('latest/oldest: falls back to createdAt when capturedAt is null', () => {
    const items = [
      makeItem({ id: 1, capturedAt: null, createdAt: '2025-01-01T00:00:00Z' }),
      makeItem({ id: 2, capturedAt: null, createdAt: '2025-06-01T00:00:00Z' }),
    ]
    expect(sortRepairItems(items, 'latest')[0]!.id).toBe(2)
    expect(sortRepairItems(items, 'oldest')[0]!.id).toBe(1)
  })
})

// ── parseStatusesParam ────────────────────────────────────

describe('parseStatusesParam', () => {
  it('returns all statuses when param is undefined', () => {
    expect(parseStatusesParam(undefined)).toEqual([...REPAIR_STATUS_FILTERS])
  })

  it('parses a comma-separated string of backend status codes', () => {
    const result = parseStatusesParam('REQUESTED,REPAIR_COMPLETED')
    expect(result).toEqual(['requested', 'completed'])
  })

  it('parses a single status code', () => {
    expect(parseStatusesParam('REPAIR_IN_PROGRESS')).toEqual(['in_progress'])
  })

  it('ignores unknown status codes', () => {
    const result = parseStatusesParam('REQUESTED,UNKNOWN_STATUS')
    expect(result).toEqual(['requested'])
  })

  it('returns all statuses when all codes are unrecognised', () => {
    expect(parseStatusesParam('GARBAGE')).toEqual([...REPAIR_STATUS_FILTERS])
  })

  it('accepts an array (multiple query params)', () => {
    const result = parseStatusesParam(['REQUESTED,REPAIR_IN_PROGRESS'])
    expect(result).toEqual(['requested', 'in_progress'])
  })
})

// ── statusesToParam ───────────────────────────────────────

describe('statusesToParam', () => {
  it('returns undefined when all statuses are selected', () => {
    expect(statusesToParam([...REPAIR_STATUS_FILTERS])).toBeUndefined()
  })

  it('returns comma-separated backend codes for a subset', () => {
    expect(statusesToParam(['requested', 'completed'])).toBe('REQUESTED,REPAIR_COMPLETED')
  })

  it('returns a single code for one status', () => {
    expect(statusesToParam(['in_progress'])).toBe('REPAIR_IN_PROGRESS')
  })
})

// ── parseSortParam ────────────────────────────────────────

describe('parseSortParam', () => {
  it('defaults to priority for undefined', () => {
    expect(parseSortParam(undefined)).toBe('priority')
  })

  it('parses latest', () => {
    expect(parseSortParam('latest')).toBe('latest')
  })

  it('parses oldest', () => {
    expect(parseSortParam('oldest')).toBe('oldest')
  })

  it('defaults to priority for unknown values', () => {
    expect(parseSortParam('unknown')).toBe('priority')
  })

  it('picks first element of an array', () => {
    expect(parseSortParam(['latest', 'oldest'])).toBe('latest')
  })
})
