import http from './http'
import type {
  StatQuery,
  TimeSeriesResponse,
  StatusStatResponse,
  SeverityStatResponse,
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

  async bySeverity(query: Omit<StatQuery, 'unit'>) {
    const { data } = await http.get<SeverityStatResponse>('/statistics/damages/by-severity', {
      params: query,
    })
    return data
  },
}
