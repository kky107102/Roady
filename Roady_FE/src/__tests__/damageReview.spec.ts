import { describe, expect, it } from 'vitest'
import type { DamageListItem } from '@/types/damage'
import {
  defaultDamageSort,
  isReviewConfirmed,
  isReviewVisible,
  sortReviewDamages,
} from '@/utils/damageReview'

function damage(overrides: Partial<DamageListItem>): DamageListItem {
  return {
    id: 1,
    robotId: null,
    assignedTo: null,
    description: null,
    latitude: null,
    longitude: null,
    capturedAt: '2026-08-01T10:00:00',
    currentStatus: 'AI_ANALYZED',
    processingPriority: null,
    imageCount: 0,
    damageScore: null,
    damageType: null,
    repairRequired: null,
    repairPriority: null,
    confidenceScore: null,
    createdAt: '2026-08-01T10:00:00',
    ...overrides,
  }
}

describe('damageReview', () => {
  it('수집 완료와 AI 분석 중 사건은 탐지 검토에서 숨긴다', () => {
    expect(isReviewVisible(damage({ currentStatus: 'COLLECTED' }))).toBe(false)
    expect(isReviewVisible(damage({ currentStatus: 'AI_ANALYZING' }))).toBe(false)
    expect(isReviewVisible(damage({ currentStatus: 'AI_ANALYZED' }))).toBe(true)
  })

  it('AI 분석 완료 사건은 미확인, 관리자 판정 이후 사건은 확인으로 분류한다', () => {
    expect(isReviewConfirmed(damage({ currentStatus: 'AI_ANALYZED' }))).toBe(false)
    expect(isReviewConfirmed(damage({ currentStatus: 'REQUESTED' }))).toBe(true)
    expect(isReviewConfirmed(damage({ currentStatus: 'CANCELED' }))).toBe(true)
  })

  it('미확인은 최신순, 확인은 우선순위순을 기본값으로 사용한다', () => {
    expect(defaultDamageSort('pending')).toBe('latest')
    expect(defaultDamageSort('confirmed')).toBe('priority')
  })

  it('확인 탭 우선순위 정렬은 관리자 우선순위를 사용하고 미지정은 뒤로 보낸다', () => {
    const items = [
      damage({ id: 1, currentStatus: 'REQUESTED', processingPriority: null }),
      damage({ id: 2, currentStatus: 'REQUESTED', processingPriority: 'LOW' }),
      damage({ id: 3, currentStatus: 'REQUESTED', processingPriority: 'URGENT' }),
    ]

    expect(sortReviewDamages(items, 'confirmed', 'priority').map((item) => item.id)).toEqual([
      3, 2, 1,
    ])
  })

  it('오래된 순과 최신 순은 탐지 일자를 기준으로 정렬한다', () => {
    const items = [
      damage({ id: 1, capturedAt: '2026-08-02T10:00:00' }),
      damage({ id: 2, capturedAt: '2026-08-01T10:00:00' }),
    ]

    expect(sortReviewDamages(items, 'pending', 'latest').map((item) => item.id)).toEqual([1, 2])
    expect(sortReviewDamages(items, 'pending', 'oldest').map((item) => item.id)).toEqual([2, 1])
  })
})
