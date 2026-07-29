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
  /** 고위험 탐지 수 - API 확장 시 추가될 예정 */
  highSeverityCount?: number
  repairCompletedCount: number
  repairCompletionRate: number
}

export interface TimeSeriesResponse {
  unit: StatUnit
  items: TimeSeriesItem[]
}

export interface StatusStatItem {
  status: string
  count: number
}

export interface StatusStatResponse {
  items: StatusStatItem[]
}

export interface SeverityStatItem {
  severity: string
  count: number
}

export interface SeverityStatResponse {
  items: SeverityStatItem[]
}
