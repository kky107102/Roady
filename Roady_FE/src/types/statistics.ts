export type StatUnit = 'DAY' | 'WEEK' | 'MONTH' | 'YEAR'

export interface StatQuery {
  from: string
  to: string
  unit?: StatUnit
  regionCode?: string
}

export interface TimeSeriesItem {
  period: string
  totalCount: number
  repairCompletedCount: number
  repairCompletionRate: number
}

export interface TimeSeriesResponse {
  unit: StatUnit
  items: TimeSeriesItem[]
}

export interface StatusStatResponse {
  totalCount: number
  counts: Record<string, number>
}

export interface RepairPriorityStatResponse {
  totalCount: number
  classifiedCount: number
  unclassifiedCount: number
  counts: Record<string, number>
}
