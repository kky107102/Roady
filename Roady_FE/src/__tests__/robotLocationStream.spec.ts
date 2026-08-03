import { describe, expect, it } from 'vitest'
import {
  appendLocationPoint,
  parseRobotLocationMessage,
} from '@/composables/useRobotLocationStream'

describe('robot location stream helpers', () => {
  it('parses a valid robot location message', () => {
    expect(parseRobotLocationMessage(JSON.stringify({
      robotId: 3,
      latitude: 37.5665,
      longitude: 126.978,
      batteryLevel: 72,
      operationStatus: 'MOVING',
      connectionStatus: 'CONNECTED',
      errorCode: null,
      errorMessage: null,
      recordedAt: '2026-08-03T10:00:00',
      receivedAt: '2026-08-03T10:00:01',
    }))).toEqual(expect.objectContaining({
      robotId: 3,
      latitude: 37.5665,
      longitude: 126.978,
      operationStatus: 'MOVING',
    }))
  })

  it('rejects malformed JSON and invalid coordinates', () => {
    expect(parseRobotLocationMessage('{')).toBeNull()
    expect(parseRobotLocationMessage(JSON.stringify({
      robotId: 3,
      latitude: 100,
      longitude: 126.978,
    }))).toBeNull()
  })

  it('deduplicates consecutive points and keeps the configured limit', () => {
    const first = { latitude: 37.5, longitude: 127 }
    expect(appendLocationPoint([first], first)).toEqual([first])
    expect(appendLocationPoint(
      [first, { latitude: 37.6, longitude: 127.1 }],
      { latitude: 37.7, longitude: 127.2 },
      2,
    )).toEqual([
      { latitude: 37.6, longitude: 127.1 },
      { latitude: 37.7, longitude: 127.2 },
    ])
  })
})
