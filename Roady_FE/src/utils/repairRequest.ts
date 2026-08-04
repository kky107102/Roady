import type { DamageDetail } from '@/types/damage'

const PRIORITY_LABELS: Record<string, string> = {
  URGENT: '긴급',
  HIGH: '높음',
  NORMAL: '보통',
  MEDIUM: '보통',
  LOW: '낮음',
}

const DAMAGE_TYPE_LABELS: Record<string, string> = {
  LARGE_MISSING: '큰 결손',
  SMALL_MISSING: '작은 결손',
  MISSING: '큰 결손',
  WEAR: '마모',
  BREAKAGE: '작은 결손',
  CRACK: '균열',
  OTHER: '기타',
}

export function formatCaseId(id: number, createdAt: string): string {
  const year = new Date(createdAt).getFullYear()
  return `RD-${year}-${String(id).padStart(6, '0')}`
}

export function formatRepairLocation(
  detail: Pick<DamageDetail, 'roadAddressName' | 'addressName' | 'latitude' | 'longitude'>,
): string {
  const address = detail.roadAddressName?.trim() || detail.addressName?.trim()
  if (address) return address
  if (detail.latitude != null && detail.longitude != null)
    return `위도 ${detail.latitude.toFixed(6)}, 경도 ${detail.longitude.toFixed(6)}`
  return '-'
}

export function formatPriorityLabel(priority: string | null | undefined): string {
  if (!priority) return '-'
  return PRIORITY_LABELS[priority] ?? priority
}

export function formatDamageTypeLabel(damageType: string | null | undefined): string {
  if (!damageType) return '-'
  return DAMAGE_TYPE_LABELS[damageType] ?? damageType
}

export function buildRepairRequestText(detail: DamageDetail, detailUrl: string): string {
  const caseId = formatCaseId(detail.id, detail.createdAt)
  const title = detail.description?.trim() || '미확인'
  const priority = formatPriorityLabel(detail.processingPriority)
  const damageType = formatDamageTypeLabel(detail.reviewDamageType)
  const location = formatRepairLocation(detail)

  return [
    '[Roady 보수 요청]',
    '',
    `사건번호: ${caseId}`,
    `사건명: ${title}`,
    `관리자 판정 우선순위: ${priority}`,
    `관리자 판정 파손 유형: ${damageType}`,
    `위치: ${location}`,
    `보수 관리 상세 URL: ${detailUrl}`,
  ].join('\n')
}
