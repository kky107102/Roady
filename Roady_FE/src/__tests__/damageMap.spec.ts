import { describe, expect, it } from 'vitest'
import type { DamageListItem } from '@/types/damage'
import { toDamageMapMarkers } from '@/utils/damageMap'

function damage(overrides: Partial<DamageListItem> = {}): DamageListItem {
  return {
    id: 10,
    robotId: 3,
    assignedTo: null,
    description: '포트홀 탐지',
    latitude: 37.5665,
    longitude: 126.978,
    capturedAt: '2026-07-30T10:00:00',
    currentStatus: 'REVIEW_REQUIRED',
    imageCount: 1,
    damageScore: 0.9,
    repairRequired: true,
    repairPriority: 'HIGH',
    confidenceScore: 0.95,
    createdAt: '2026-07-30T10:00:00',
    ...overrides,
  }
}

describe('toDamageMapMarkers', () => {
  it('탐지 사건 좌표와 상태를 지도 마커로 변환한다', () => {
    expect(toDamageMapMarkers([damage()])).toEqual([
      expect.objectContaining({
        id: 10,
        latitude: 37.5665,
        longitude: 126.978,
        title: '탐지 사건 #10',
        tone: 'danger',
      }),
    ])
  })

  it('좌표가 없거나 유효 범위를 벗어난 사건은 제외한다', () => {
    expect(toDamageMapMarkers([
      damage({ id: 1, latitude: null }),
      damage({ id: 2, longitude: 181 }),
    ])).toEqual([])
  })
})
