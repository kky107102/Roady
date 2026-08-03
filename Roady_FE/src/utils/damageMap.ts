import type { DamageListItem, DamageStatus } from '@/types/damage'
import type { MapMarkerItem } from '@/types/map'

const statusLabels: Record<DamageStatus, string> = {
  COLLECTED: '수집 완료',
  AI_ANALYZING: 'AI 분석중',
  AI_ANALYZED: 'AI 분석완료',
  REQUESTED: '검토 완료',
  REPAIR_IN_PROGRESS: '보수 중',
  CANCELED: '취소',
  REPAIR_COMPLETED: '보수 완료',
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
  if (status === 'AI_ANALYZED') return 'danger'
  if (
    status === 'REQUESTED' ||
    status === 'REPAIR_IN_PROGRESS'
  ) return 'warning'
  if (
    status === 'REPAIR_COMPLETED' ||
    status === 'CANCELED'
  ) return 'success'
  return 'primary'
}

function formatCapturedAt(value: string | null): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return new Intl.DateTimeFormat('ko-KR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
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
        { label: '탐지 시각', value: formatCapturedAt(item.capturedAt) },
        { label: '설명', value: item.description || '-' },
      ],
    }]
  })
}
