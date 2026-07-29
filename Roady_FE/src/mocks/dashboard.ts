import type { TimeSeriesResponse } from '@/types/statistics'

/**
 * 통계 API(설계안) 구현 전까지 사용하는 mock 데이터.
 * 실제 API 연동 시 statisticsApi.timeSeries() 호출로 교체한다.
 */
export const MOCK_TIME_SERIES: TimeSeriesResponse = {
  unit: 'DAY',
  items: [
    { period: '10/18', totalCount: 8,  highSeverityCount: 1, repairCompletedCount: 3,  repairCompletionRate: 37.5 },
    { period: '10/19', totalCount: 12, highSeverityCount: 2, repairCompletedCount: 5,  repairCompletionRate: 41.7 },
    { period: '10/20', totalCount: 15, highSeverityCount: 4, repairCompletedCount: 7,  repairCompletionRate: 46.7 },
    { period: '오늘',  totalCount: 22, highSeverityCount: 6, repairCompletedCount: 8,  repairCompletionRate: 36.4 },
    { period: '10/22', totalCount: 9,  highSeverityCount: 1, repairCompletedCount: 3,  repairCompletionRate: 33.3 },
    { period: '10/23', totalCount: 7,  highSeverityCount: 0, repairCompletedCount: 2,  repairCompletionRate: 28.6 },
    { period: '10/24', totalCount: 4,  highSeverityCount: 0, repairCompletedCount: 0,  repairCompletionRate: 0 },
  ],
}

/** 고위험 카운트 - severity API 또는 damages.severity 필드 확인 전 사용 */
export const MOCK_HIGH_SEVERITY_COUNT = 3

/** 백엔드 미연결 시 dev 환경에서 사용하는 통계 카드 mock 값 */
export const MOCK_STAT_COUNTS = {
  total: 12,
  highSeverity: 3,
  reviewRequired: 8,
  repairing: 24,
  activeRobots: 2,
} as const
