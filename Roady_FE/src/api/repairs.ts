import http from './http'
import type { DamageDetail } from '@/types/damage'
import type { RepairRequestPayload, RepairCompletePayload } from '@/types/repair'
import { damagesApi } from './damages'

// NOTE: Backend state transition APIs are not yet implemented (2026-08-04).
// These calls will result in 404 until the backend implements:
//   POST /api/damages/{id}/repair-request    (REQUESTED → REPAIR_IN_PROGRESS)
//   DELETE /api/damages/{id}/repair-request  (REPAIR_IN_PROGRESS → REQUESTED)
//   POST /api/damages/{id}/repair-completion (REPAIR_IN_PROGRESS → REPAIR_COMPLETED)

export const repairsApi = {
  async submitRequest(damageId: number, payload?: RepairRequestPayload): Promise<DamageDetail> {
    const { data } = await http.post<DamageDetail>(
      `/damages/${damageId}/repair-request`,
      payload ?? {},
    )
    damagesApi.clearDetailCache(damageId)
    return data
  },

  async cancelRequest(damageId: number): Promise<DamageDetail> {
    const { data } = await http.delete<DamageDetail>(`/damages/${damageId}/repair-request`)
    damagesApi.clearDetailCache(damageId)
    return data
  },

  async completeRepair(damageId: number, payload: RepairCompletePayload): Promise<DamageDetail> {
    const { data } = await http.post<DamageDetail>(
      `/damages/${damageId}/repair-completion`,
      payload,
    )
    damagesApi.clearDetailCache(damageId)
    return data
  },
}
