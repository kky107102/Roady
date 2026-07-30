import { describe, expect, it } from 'vitest'
import type { Robot } from '@/types/robot'
import { toRobotMapMarkers } from '@/utils/robotMap'

function robot(overrides: Partial<Robot> = {}): Robot {
  return {
    id: 1,
    userId: 10,
    name: '로디1호',
    serialNumber: 'RD-001',
    status: 'MOVING',
    active: true,
    latestStatus: {
      id: 1,
      latitude: 37.5665,
      longitude: 126.978,
      batteryLevel: 72,
      operationStatus: 'MOVING',
      connectionStatus: 'CONNECTED',
      errorCode: null,
      errorMessage: null,
      recordedAt: '2026-07-30T10:00:00',
    },
    createdAt: '2026-07-30T09:00:00',
    updatedAt: '2026-07-30T10:00:00',
    ...overrides,
  }
}

describe('toRobotMapMarkers', () => {
  it('maps a located robot to a marker with user-facing status details', () => {
    expect(toRobotMapMarkers([robot()])).toEqual([
      {
        id: 1,
        latitude: 37.5665,
        longitude: 126.978,
        title: '로디1호',
        tone: 'success',
        details: [
          { label: '운행 상태', value: '이동 중' },
          { label: '연결 상태', value: '연결됨' },
          { label: '배터리', value: '72%' },
        ],
      },
    ])
  })

  it('excludes robots with missing or invalid coordinates', () => {
    const missing = robot({ id: 2, latestStatus: null })
    const invalid = robot({
      id: 3,
      latestStatus: {
        ...robot().latestStatus!,
        latitude: 100,
      },
    })

    expect(toRobotMapMarkers([missing, invalid])).toEqual([])
  })

  it('uses a danger marker for errors or disconnected robots', () => {
    const disconnected = robot({
      latestStatus: {
        ...robot().latestStatus!,
        connectionStatus: 'DISCONNECTED',
      },
    })

    expect(toRobotMapMarkers([disconnected])[0]?.tone).toBe('danger')
  })
})
