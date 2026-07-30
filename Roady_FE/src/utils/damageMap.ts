import type { DamageListItem, DamageStatus } from '@/types/damage'
import type { MapMarkerItem } from '@/types/map'

const statusLabels: Record<DamageStatus, string> = {
  COLLECTED: '수집 완료',
  REVIEW_REQUIRED: '검토 필요',
  RECEIVED: '접수 완료',
  REPAIR_SCHEDULED: '보수 예정',
  REPAIRING: '보수 중',
  REPAIR_COMPLETED: '보수 완료',
  REPAIR_NOT_REQUIRED: '보수 불필요',
}

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

function markerTone(status: DamageStatus): MapMarkerItem['tone'] {
  if (status === 'REVIEW_REQUIRED') return 'danger'
  if (status === 'REPAIRING' || status === 'REPAIR_SCHEDULED') return 'warning'
  if (status === 'REPAIR_COMPLETED' || status === 'REPAIR_NOT_REQUIRED') return 'success'
  return 'primary'
}

export function toDamageMapMarkers(items: DamageListItem[]): MapMarkerItem[] {
  return items.flatMap((item) => {
    if (!isValidCoordinate(item.latitude, item.longitude)) return []

    return [{
      id: item.id,
      latitude: item.latitude as number,
      longitude: item.longitude as number,
      title: `탐지 사건 #${item.id}`,
      tone: markerTone(item.currentStatus),
      details: [
        { label: '처리 상태', value: statusLabels[item.currentStatus] },
        { label: '로봇 ID', value: item.robotId == null ? '-' : String(item.robotId) },
        { label: '설명', value: item.description || '-' },
      ],
    }]
  })
}
