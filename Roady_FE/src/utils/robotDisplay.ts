import type {
  Robot,
  RobotConnectionStatus,
  RobotOperationStatus,
} from '@/types/robot'
import type { BadgeType } from '@/components/common/StatusBadge.vue'

export const operationLabels: Record<RobotOperationStatus, string> = {
  STANDBY: '대기',
  MOVING: '이동 중',
  INSPECTING: '점검 중',
  CHARGING: '충전 중',
  STOPPED: '정지',
  ERROR: '오류',
}

export const connectionLabels: Record<RobotConnectionStatus, string> = {
  CONNECTED: '연결됨',
  DISCONNECTED: '연결 끊김',
}

export function matchesRobotStatus(
  robot: Robot,
  operation: RobotOperationStatus | 'ALL',
  connection: RobotConnectionStatus | 'ALL',
): boolean {
  const latestStatus = robot.latestStatus
  return (
    (operation === 'ALL' || latestStatus?.operationStatus === operation) &&
    (connection === 'ALL' || latestStatus?.connectionStatus === connection)
  )
}

export function isMovingAndConnected(robot: Robot): boolean {
  return matchesRobotStatus(robot, 'MOVING', 'CONNECTED')
}

export function operationBadge(status: RobotOperationStatus | null | undefined): {
  label: string
  type: BadgeType
} {
  if (!status) return { label: '상태 없음', type: 'neutral' }

  const typeMap: Record<RobotOperationStatus, BadgeType> = {
    STANDBY: 'neutral',
    MOVING: 'info',
    INSPECTING: 'success',
    CHARGING: 'warning',
    STOPPED: 'neutral',
    ERROR: 'danger',
  }

  return { label: operationLabels[status], type: typeMap[status] }
}

export function connectionBadge(status: RobotConnectionStatus | null | undefined): {
  label: string
  type: BadgeType
} {
  if (!status) return { label: '상태 없음', type: 'neutral' }
  return {
    label: connectionLabels[status],
    type: status === 'CONNECTED' ? 'success' : 'danger',
  }
}

export function formatBattery(value: number | null | undefined): string {
  return value == null ? '-' : `${value}%`
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'

  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date)
}

export function formatCoordinate(value: number | null | undefined): string {
  return value == null ? '-' : value.toFixed(6)
}
