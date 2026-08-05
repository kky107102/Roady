import http from './http'
import type {
  StatQuery,
  TimeSeriesResponse,
  StatusStatResponse,
  RepairPriorityStatResponse,
} from '@/types/statistics'

export const statisticsApi = {
  async timeSeries(query: StatQuery) {
    const { data } = await http.get<TimeSeriesResponse>('/statistics/damages/time-series', {
      params: query,
    })
    return data
  },

  async byStatus(query: Omit<StatQuery, 'unit'>) {
    const { data } = await http.get<StatusStatResponse>('/statistics/damages/by-status', {
      params: query,
    })
    return data
  },

  async byRepairPriority(query: Omit<StatQuery, 'unit'>) {
    const { data } = await http.get<RepairPriorityStatResponse>(
      '/statistics/damages/by-repair-priority',
      { params: query },
    )
    return data
  },
}
