import http from './http'
import type { UserSummary } from '@/types/auth'

export const usersApi = {
  async list(): Promise<UserSummary[]> {
    const { data } = await http.get<UserSummary[]>('/users')
    return data
  },
}
