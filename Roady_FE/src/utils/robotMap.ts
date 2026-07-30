import type { MapMarkerItem } from '@/types/map'
import type { Robot } from '@/types/robot'
import { connectionBadge, operationBadge } from '@/utils/robotDisplay'

function isValidCoordinate(latitude: number | null, longitude: number | null): boolean {
  return (
    latitude != null &&
    longitude != null &&
    Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    latitude >= -90 &&
    latitude <= 90 &&
    longitude >= -180 &&
    longitude <= 180
  )
}

export function toRobotMapMarkers(robots: Robot[]): MapMarkerItem[] {
  return robots.flatMap((robot) => {
    const status = robot.latestStatus
    if (!status || !isValidCoordinate(status.latitude, status.longitude)) return []

    const operation = operationBadge(status.operationStatus)
    const connection = connectionBadge(status.connectionStatus)
    const tone: MapMarkerItem['tone'] =
      status.operationStatus === 'ERROR' || status.connectionStatus === 'DISCONNECTED'
        ? 'danger'
        : status.connectionStatus === 'CONNECTED'
          ? 'success'
          : 'neutral'

    return [
      {
        id: robot.id,
        latitude: status.latitude as number,
        longitude: status.longitude as number,
        title: robot.name,
        tone,
        details: [
          { label: '운행 상태', value: operation.label },
          { label: '연결 상태', value: connection.label },
          {
            label: '배터리',
            value: status.batteryLevel == null ? '-' : `${status.batteryLevel}%`,
          },
        ],
      },
    ]
  })
}
