import { describe, expect, it } from 'vitest'
import {
  connectionBadge,
  formatBattery,
  formatCoordinate,
  formatDateTime,
  isMovingAndConnected,
  matchesRobotStatus,
  operationBadge,
} from '@/utils/robotDisplay'
import type { Robot } from '@/types/robot'

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

  it('대시보드와 목록에서 동일한 최신 연결·운행 상태를 사용한다', () => {
    const robot = {
      latestStatus: { operationStatus: 'MOVING', connectionStatus: 'CONNECTED' },
    } as Robot

    expect(isMovingAndConnected(robot)).toBe(true)
    expect(matchesRobotStatus(robot, 'MOVING', 'CONNECTED')).toBe(true)

    robot.latestStatus!.connectionStatus = 'DISCONNECTED'
    expect(isMovingAndConnected(robot)).toBe(false)
    expect(matchesRobotStatus(robot, 'MOVING', 'CONNECTED')).toBe(false)
  })
})
