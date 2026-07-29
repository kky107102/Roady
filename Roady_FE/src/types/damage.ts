export type DamageStatus =
  | 'COLLECTED'
  | 'REVIEW_REQUIRED'
  | 'RECEIVED'
  | 'REPAIR_SCHEDULED'
  | 'REPAIRING'
  | 'REPAIR_COMPLETED'
  | 'REPAIR_NOT_REQUIRED'

export type DamageSeverity = 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH'

export interface DamageSummary {
  id: number
  robotId: number | null
  reportedBy: number
  assignedTo: number | null
  description: string | null
  latitude: number | null
  longitude: number | null
  capturedAt: string | null
  currentStatus: DamageStatus
  /** severity 필드는 API 확장 설계안에 있음. 현재 구현 응답에 없을 수 있음 */
  severity?: DamageSeverity
  imageCount: number
  createdAt: string
  updatedAt: string
}
