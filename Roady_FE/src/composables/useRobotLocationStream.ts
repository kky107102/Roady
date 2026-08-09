import { Client, type IMessage } from '@stomp/stompjs'
import { readonly, ref } from 'vue'
import type { MapCoordinate } from '@/types/map'
import type {
  RobotConnectionStatus,
  RobotLocationMessage,
  RobotOperationStatus,
} from '@/types/robot'

type RobotLocationStreamStatus =
  | 'idle'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'error'

const MAX_PATH_POINTS = 500
const operationStatuses: RobotOperationStatus[] = [
  'STANDBY',
  'MOVING',
  'INSPECTING',
  'CHARGING',
  'STOPPED',
  'ERROR',
]
const connectionStatuses: RobotConnectionStatus[] = ['CONNECTED', 'DISCONNECTED']

function validCoordinate(latitude: unknown, longitude: unknown): boolean {
  return (
    typeof latitude === 'number' &&
    typeof longitude === 'number' &&
    Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    latitude >= -90 &&
    latitude <= 90 &&
    longitude >= -180 &&
    longitude <= 180
  )
}

export function parseRobotLocationMessage(body: string): RobotLocationMessage | null {
  try {
    const value = JSON.parse(body) as Record<string, unknown>
    if (
      typeof value.robotId !== 'number' ||
      !Number.isInteger(value.robotId) ||
      !validCoordinate(value.latitude, value.longitude)
    ) {
      return null
    }

    const operationStatus = operationStatuses.includes(value.operationStatus as RobotOperationStatus)
      ? (value.operationStatus as RobotOperationStatus)
      : null
    const connectionStatus = connectionStatuses.includes(value.connectionStatus as RobotConnectionStatus)
      ? (value.connectionStatus as RobotConnectionStatus)
      : null

    return {
      robotId: value.robotId,
      latitude: value.latitude as number,
      longitude: value.longitude as number,
      batteryLevel: typeof value.batteryLevel === 'number' ? value.batteryLevel : null,
      operationStatus,
      connectionStatus,
      errorCode: typeof value.errorCode === 'string' ? value.errorCode : null,
      errorMessage: typeof value.errorMessage === 'string' ? value.errorMessage : null,
      recordedAt: typeof value.recordedAt === 'string' ? value.recordedAt : null,
      receivedAt: typeof value.receivedAt === 'string' ? value.receivedAt : null,
    }
  } catch {
    return null
  }
}

export function appendLocationPoint(
  points: MapCoordinate[],
  point: MapCoordinate,
  limit = MAX_PATH_POINTS,
): MapCoordinate[] {
  const last = points[points.length - 1]
  if (last?.latitude === point.latitude && last.longitude === point.longitude) return points

  const next = [...points, point]
  return next.length > limit ? next.slice(next.length - limit) : next
}

function webSocketUrl(): string {
  const configured = import.meta.env.VITE_WS_BASE_URL?.trim()
  if (configured) return configured

  const apiBase = (import.meta.env.VITE_API_BASE_URL || window.location.origin).replace(/\/$/, '')
  const serverBase = apiBase.replace(/\/api$/, '')
  return `${serverBase.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:')}/ws`
}

export function useRobotLocationStream() {
  const status = ref<RobotLocationStreamStatus>('idle')
  const latestLocation = ref<RobotLocationMessage | null>(null)
  const pathPoints = ref<MapCoordinate[]>([])
  let client: Client | null = null
  let active = false

  function handleMessage(message: IMessage, robotId: number) {
    const location = parseRobotLocationMessage(message.body)
    if (!location || location.robotId !== robotId) return

    latestLocation.value = location
    pathPoints.value = appendLocationPoint(pathPoints.value, {
      latitude: location.latitude,
      longitude: location.longitude,
    })
  }

  function stop() {
    active = false
    const currentClient = client
    client = null
    if (currentClient) void currentClient.deactivate()
    status.value = 'idle'
  }

  function start(robotId: number, initialLocation?: RobotLocationMessage | null) {
    stop()
    latestLocation.value = initialLocation ?? null
    pathPoints.value = initialLocation
      ? [{ latitude: initialLocation.latitude, longitude: initialLocation.longitude }]
      : []

    if (typeof WebSocket === 'undefined') {
      status.value = 'error'
      return
    }

    active = true
    status.value = 'connecting'
    const nextClient = new Client({
      brokerURL: webSocketUrl(),
      reconnectDelay: 5_000,
      connectionTimeout: 10_000,
      heartbeatIncoming: 10_000,
      heartbeatOutgoing: 10_000,
      onConnect: () => {
        if (client !== nextClient) return
        status.value = 'connected'
        nextClient.subscribe(`/topic/robots/${robotId}/location`, (message) => {
          handleMessage(message, robotId)
        })
      },
      onStompError: () => {
        if (client !== nextClient) return
        status.value = 'error'
      },
      onWebSocketError: () => {
        if (client !== nextClient) return
        status.value = 'error'
      },
      onWebSocketClose: () => {
        if (active && client === nextClient) status.value = 'reconnecting'
      },
    })
    client = nextClient
    nextClient.activate()
  }

  return {
    status: readonly(status),
    latestLocation: readonly(latestLocation),
    pathPoints: readonly(pathPoints),
    start,
    stop,
  }
}
