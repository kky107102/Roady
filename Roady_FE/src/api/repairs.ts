import http from './http'
import type {
  RepairRequestPayload,
  RepairCompletePayload,
  RepairTransitionResult,
} from '@/types/repair'
import { damagesApi } from './damages'

export const repairsApi = {
  async submitRequest(
    damageId: number,
    payload?: RepairRequestPayload,
  ): Promise<RepairTransitionResult> {
    const { data } = await http.post<RepairTransitionResult>(
      `/damages/${damageId}/repair-request`,
      payload ?? {},
    )
    damagesApi.clearDetailCache(damageId)
    return data
  },

  async cancelRequest(
    damageId: number,
    payload?: RepairRequestPayload,
  ): Promise<RepairTransitionResult> {
    const { data } = await http.patch<RepairTransitionResult>(
      `/damages/${damageId}/repair-cancel`,
      payload ?? {},
    )
    damagesApi.clearDetailCache(damageId)
    return data
  },

  async updateRequest(
    damageId: number,
    payload: RepairRequestPayload,
  ): Promise<RepairTransitionResult> {
    const { data } = await http.patch<RepairTransitionResult>(
      `/damages/${damageId}/repair-request`,
      payload,
    )
    damagesApi.clearDetailCache(damageId)
    return data
  },

  async completeRepair(
    damageId: number,
    payload?: RepairCompletePayload,
  ): Promise<RepairTransitionResult> {
    const { data } = await http.patch<RepairTransitionResult>(
      `/damages/${damageId}/repair-complete`,
      payload ?? {},
    )
    damagesApi.clearDetailCache(damageId)
    return data
  },
}
