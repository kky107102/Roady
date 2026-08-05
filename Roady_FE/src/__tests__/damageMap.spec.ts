import { describe, expect, it } from 'vitest'
import type { DamageListItem } from '@/types/damage'
import { toDamageMapCenter, toDamageMapMarkers } from '@/utils/damageMap'

function damage(overrides: Partial<DamageListItem> = {}): DamageListItem {
  return {
    id: 10,
    robotId: 3,
    assignedTo: null,
    description: '포트홀 탐지',
    latitude: 37.5665,
    longitude: 126.978,
    capturedAt: '2026-07-30T10:00:00',
    currentStatus: 'AI_ANALYZED',
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

describe('toDamageMapCenter', () => {
  it('선택 사건의 유효한 좌표를 지도 중심 좌표로 반환한다', () => {
    expect(toDamageMapCenter(damage())).toEqual([37.5665, 126.978])
  })

  it('선택 사건이 없거나 좌표가 유효하지 않으면 지도 중심을 변경하지 않는다', () => {
    expect(toDamageMapCenter(null)).toBeNull()
    expect(toDamageMapCenter(damage({ latitude: null }))).toBeNull()
    expect(toDamageMapCenter(damage({ longitude: 181 }))).toBeNull()
  })
})
