import http from './http'
import type { UserSummary } from '@/types/auth'

interface UserListQuery {
  role?: UserSummary['role']
  active?: boolean
}

export const usersApi = {
  async list(query?: UserListQuery): Promise<UserSummary[]> {
    const { data } = await http.get<UserSummary[]>('/users', { params: query })
    return data
  },
}
