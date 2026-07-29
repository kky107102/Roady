import http from './http'
import type { DamageSummary } from '@/types/damage'

export interface DamageListQuery {
  from?: string
  to?: string
  regionCode?: string
  status?: string
  severity?: string
}

export const damagesApi = {
  async list(query?: DamageListQuery) {
    const { data } = await http.get<DamageSummary[]>('/damages', { params: query })
    return data
  },
}
