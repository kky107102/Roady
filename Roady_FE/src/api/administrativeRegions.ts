import http from './http'
import type { AssignedMapRegions } from '@/types/map'

export const administrativeRegionsApi = {
  /**
   * FE/BE contract for S15P11A404-222.
   * Keeping the endpoint in this adapter limits changes when the BE contract is finalized.
   */
  async getEmds(regionCode: string): Promise<AssignedMapRegions> {
    const { data } = await http.get<AssignedMapRegions>(
      `/administrative-regions/${encodeURIComponent(regionCode)}/emds`,
    )
    return data
  },
}
