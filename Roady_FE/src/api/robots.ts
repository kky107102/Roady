import http from './http'
import type { Robot } from '@/types/robot'

export const robotsApi = {
  async list() {
    const { data } = await http.get<Robot[]>('/robots')
    return data
  },
}
