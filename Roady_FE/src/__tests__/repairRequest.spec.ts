import { describe, it, expect } from 'vitest'
import {
  formatCaseId,
  formatRepairLocation,
  formatPriorityLabel,
  formatDamageTypeLabel,
  buildRepairRequestText,
} from '@/utils/repairRequest'
import type { DamageDetail } from '@/types/damage'

// ── 기본 픽스처 ──────────────────────────────────────────────

const baseDetail: DamageDetail = {
  id: 6,
  robotId: 1,
  reportedBy: null,
  assignedTo: null,
  description: '개포로 보행로 점자블록 침하 탐지',
  addressName: '서울특별시 강남구 개포동 100',
  roadAddressName: '서울특별시 강남구 개포로 123',
  latitude: 37.123456,
  longitude: 127.654321,
  capturedAt: '2026-08-03T11:20:00',
  currentStatus: 'REQUESTED',
  processingPriority: 'URGENT',
  reviewDamageType: 'CRACK',
  reviewNote: null,
  imageCount: 0,
  images: [],
  createdAt: '2026-01-01T00:00:00',
  updatedAt: '2026-08-03T12:00:00',
}

// ── formatCaseId ──────────────────────────────────────────────

describe('formatCaseId', () => {
  it('연도와 id를 6자리로 패딩해 사건번호를 생성한다', () => {
    expect(formatCaseId(6, '2026-01-01T00:00:00')).toBe('RD-2026-000006')
  })

  it('id가 6자리 이상이면 패딩 없이 그대로 출력한다', () => {
    expect(formatCaseId(1000000, '2026-01-01T00:00:00')).toBe('RD-2026-1000000')
  })

  it('createdAt 연도를 올바르게 추출한다', () => {
    expect(formatCaseId(1, '2025-12-31T23:59:59')).toBe('RD-2025-000001')
  })
})

// ── formatRepairLocation ──────────────────────────────────────

describe('formatRepairLocation', () => {
  it('도로명 주소를 우선으로 반환한다', () => {
    const result = formatRepairLocation({
      roadAddressName: '서울특별시 강남구 개포로 123',
      addressName: '서울특별시 강남구 개포동 100',
      latitude: 37.123,
      longitude: 127.654,
    })
    expect(result).toBe('서울특별시 강남구 개포로 123')
  })

  it('도로명 주소가 없으면 지번 주소를 반환한다', () => {
    const result = formatRepairLocation({
      roadAddressName: null,
      addressName: '서울특별시 강남구 개포동 100',
      latitude: 37.123,
      longitude: 127.654,
    })
    expect(result).toBe('서울특별시 강남구 개포동 100')
  })

  it('주소가 없으면 좌표를 6자리로 반환한다', () => {
    const result = formatRepairLocation({
      roadAddressName: null,
      addressName: null,
      latitude: 37.123456,
      longitude: 127.654321,
    })
    expect(result).toBe('위도 37.123456, 경도 127.654321')
  })

  it('주소와 좌표 모두 없으면 "-"를 반환한다', () => {
    const result = formatRepairLocation({
      roadAddressName: null,
      addressName: null,
      latitude: null,
      longitude: null,
    })
    expect(result).toBe('-')
  })

  it('공백만 있는 주소는 무시하고 다음 값을 사용한다', () => {
    const result = formatRepairLocation({
      roadAddressName: '   ',
      addressName: '서울특별시 강남구 개포동 100',
      latitude: null,
      longitude: null,
    })
    expect(result).toBe('서울특별시 강남구 개포동 100')
  })
})

// ── formatPriorityLabel ───────────────────────────────────────

describe('formatPriorityLabel', () => {
  it.each([
    ['URGENT', '긴급'],
    ['HIGH', '높음'],
    ['NORMAL', '보통'],
    ['MEDIUM', '보통'],
    ['LOW', '낮음'],
  ])('%s → "%s"', (input, expected) => {
    expect(formatPriorityLabel(input)).toBe(expected)
  })

  it('null이면 "-"를 반환한다', () => {
    expect(formatPriorityLabel(null)).toBe('-')
  })

  it('undefined이면 "-"를 반환한다', () => {
    expect(formatPriorityLabel(undefined)).toBe('-')
  })

  it('알 수 없는 값은 그대로 반환한다', () => {
    expect(formatPriorityLabel('CUSTOM')).toBe('CUSTOM')
  })
})

// ── formatDamageTypeLabel ─────────────────────────────────────

describe('formatDamageTypeLabel', () => {
  it.each([
    ['LARGE_MISSING', '큰 결손'],
    ['SMALL_MISSING', '작은 결손'],
    ['MISSING', '큰 결손'],
    ['WEAR', '마모'],
    ['BREAKAGE', '작은 결손'],
    ['CRACK', '균열'],
    ['OTHER', '기타'],
  ])('%s → "%s"', (input, expected) => {
    expect(formatDamageTypeLabel(input)).toBe(expected)
  })

  it('null이면 "-"를 반환한다', () => {
    expect(formatDamageTypeLabel(null)).toBe('-')
  })

  it('undefined이면 "-"를 반환한다', () => {
    expect(formatDamageTypeLabel(undefined)).toBe('-')
  })
})

// ── buildRepairRequestText ────────────────────────────────────

describe('buildRepairRequestText', () => {
  const detailUrl = 'http://example.com/repairs/6'

  it('[Roady 보수 요청] 헤더를 포함한다', () => {
    const text = buildRepairRequestText(baseDetail, detailUrl)
    expect(text).toContain('[Roady 보수 요청]')
  })

  it('사건번호를 포함한다', () => {
    const text = buildRepairRequestText(baseDetail, detailUrl)
    expect(text).toContain('사건번호: RD-2026-000006')
  })

  it('사건명을 포함한다', () => {
    const text = buildRepairRequestText(baseDetail, detailUrl)
    expect(text).toContain('사건명: 개포로 보행로 점자블록 침하 탐지')
  })

  it('관리자 판정 우선순위를 한글로 포함한다', () => {
    const text = buildRepairRequestText(baseDetail, detailUrl)
    expect(text).toContain('관리자 판정 우선순위: 긴급')
  })

  it('관리자 판정 파손 유형을 한글로 포함한다', () => {
    const text = buildRepairRequestText(baseDetail, detailUrl)
    expect(text).toContain('관리자 판정 파손 유형: 균열')
  })

  it('위치(도로명 주소)를 포함한다', () => {
    const text = buildRepairRequestText(baseDetail, detailUrl)
    expect(text).toContain('위치: 서울특별시 강남구 개포로 123')
  })

  it('보수 관리 상세 URL을 포함한다', () => {
    const text = buildRepairRequestText(baseDetail, detailUrl)
    expect(text).toContain(`보수 관리 상세 URL: ${detailUrl}`)
  })

  it('description이 없으면 사건명을 "미확인"으로 표시한다', () => {
    const detail = { ...baseDetail, description: null }
    const text = buildRepairRequestText(detail, detailUrl)
    expect(text).toContain('사건명: 미확인')
  })

  it('우선순위가 없으면 "-"로 표시한다', () => {
    const detail = { ...baseDetail, processingPriority: null }
    const text = buildRepairRequestText(detail, detailUrl)
    expect(text).toContain('관리자 판정 우선순위: -')
  })

  it('파손 유형이 없으면 "-"로 표시한다', () => {
    const detail = { ...baseDetail, reviewDamageType: null }
    const text = buildRepairRequestText(detail, detailUrl)
    expect(text).toContain('관리자 판정 파손 유형: -')
  })

  it('주소가 없으면 좌표를 위치로 사용한다', () => {
    const detail = { ...baseDetail, roadAddressName: null, addressName: null }
    const text = buildRepairRequestText(detail, detailUrl)
    expect(text).toContain('위도')
    expect(text).toContain('경도')
  })

  it('주소와 좌표 모두 없으면 위치를 "-"로 표시한다', () => {
    const detail = {
      ...baseDetail,
      roadAddressName: null,
      addressName: null,
      latitude: null,
      longitude: null,
    }
    const text = buildRepairRequestText(detail, detailUrl)
    expect(text).toContain('위치: -')
  })

  it('생성된 텍스트가 각 줄을 줄바꿈으로 구분한다', () => {
    const text = buildRepairRequestText(baseDetail, detailUrl)
    const lines = text.split('\n')
    expect(lines.length).toBeGreaterThan(5)
  })
})
