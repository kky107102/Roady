import type { DamageDetail } from '@/types/damage'

export interface RepairRequestPayload {
  note?: string | null
  processingPriority?: string | null
  reviewDamageType?: string | null
  repairerId?: number | null
}

export interface RepairCompletePayload {
  completedAt: string
  note?: string | null
}
export type RepairTransitionResult = Omit<DamageDetail, 'images'>
