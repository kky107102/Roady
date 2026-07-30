import { describe, expect, it } from 'vitest'
import {
  connectionBadge,
  formatBattery,
  formatCoordinate,
  formatDateTime,
  operationBadge,
} from '@/utils/robotDisplay'

describe('robotDisplay', () => {
  it('formats missing latest-status values safely', () => {
    expect(operationBadge(null)).toEqual({ label: '상태 없음', type: 'neutral' })
    expect(connectionBadge(undefined)).toEqual({ label: '상태 없음', type: 'neutral' })
    expect(formatBattery(null)).toBe('-')
    expect(formatCoordinate(undefined)).toBe('-')
    expect(formatDateTime(null)).toBe('-')
    expect(formatDateTime('invalid')).toBe('-')
  })

  it('maps robot statuses and values to user-facing text', () => {
    expect(operationBadge('INSPECTING')).toEqual({ label: '점검 중', type: 'success' })
    expect(connectionBadge('DISCONNECTED')).toEqual({ label: '연결 끊김', type: 'danger' })
    expect(formatBattery(73)).toBe('73%')
    expect(formatCoordinate(37.1234567)).toBe('37.123457')
  })
})
