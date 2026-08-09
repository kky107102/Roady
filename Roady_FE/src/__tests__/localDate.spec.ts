import { describe, it, expect } from 'vitest'
import {
  dateRangeForPreset,
  dateRangeFromQuery,
  dateRangeToQuery,
  formatKoreanDateTime,
  formatKoreanDateTimeOrDash,
  formatShortKoreanDateTime,
  localDateOffset,
  matchingDateRangePreset,
  todayLocalStr,
  toApiFromDateTime,
  toApiToDateTime,
  validateDateRange,
} from '@/utils/localDate'

describe('localDate', () => {
  describe('화면 날짜·시간 형식', () => {
    const value = '2026-08-06T15:30:00'

    it('전체 형식은 연도를 포함한다', () => {
      expect(formatKoreanDateTime(value)).toBe(
        new Date(value).toLocaleString('ko-KR', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        }),
      )
    })

    it('목록용 축약 형식은 연도를 제외한다', () => {
      expect(formatShortKoreanDateTime(value)).toBe(
        new Date(value).toLocaleString('ko-KR', {
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        }),
      )
    })

    it('빈 값과 잘못된 값의 기존 대체 표시를 유지한다', () => {
      expect(formatKoreanDateTime(null)).toBe('-')
      expect(formatKoreanDateTime('invalid')).toBe('invalid')
      expect(formatKoreanDateTimeOrDash('invalid')).toBe('-')
    })
  })

  it('세 화면에서 같은 날짜 순서 검증 문구를 사용한다', () => {
    expect(validateDateRange('2026-08-06', '2026-08-05')).toBe(
      '시작일은 종료일보다 이전이어야 합니다.',
    )
    expect(validateDateRange('2026-08-05', '2026-08-06')).toBe('')
  })

  it('기간 전체 선택을 URL에서 명시적으로 유지한다', () => {
    expect(dateRangeToQuery('', '')).toEqual({ range: 'all' })
    expect(dateRangeFromQuery({ range: 'all' })).toEqual({ from: '', to: '' })
  })

  it('공통 기본 기간인 최근 7일을 같은 프리셋으로 판별한다', () => {
    const range = dateRangeForPreset(1)
    expect(matchingDateRangePreset(range.from, range.to)).toBe(1)
  })

  describe('todayLocalStr', () => {
    it('YYYY-MM-DD 형식을 반환한다', () => {
      expect(todayLocalStr()).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    })

    it('로컬 타임존 기준 오늘 날짜와 일치한다', () => {
      const d = new Date()
      const expected = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      expect(todayLocalStr()).toBe(expected)
    })
  })

  describe('localDateOffset', () => {
    it('offset=0이면 오늘 날짜를 반환한다', () => {
      expect(localDateOffset(0)).toBe(todayLocalStr())
    })

    it('offset=6이면 6일 전 날짜를 로컬 기준으로 반환한다', () => {
      const d = new Date()
      d.setDate(d.getDate() - 6)
      const expected = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      expect(localDateOffset(6)).toBe(expected)
    })

    it('offset=29이면 29일 전 날짜를 로컬 기준으로 반환한다', () => {
      const d = new Date()
      d.setDate(d.getDate() - 29)
      const expected = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      expect(localDateOffset(29)).toBe(expected)
    })
  })

  describe('toApiFromDateTime', () => {
    it('시작일에 T00:00:00을 붙인다', () => {
      expect(toApiFromDateTime('2026-07-29')).toBe('2026-07-29T00:00:00')
    })

    it('월 초 날짜도 변환한다', () => {
      expect(toApiFromDateTime('2026-07-01')).toBe('2026-07-01T00:00:00')
    })
  })

  describe('toApiToDateTime', () => {
    it('종료일을 다음 날 T00:00:00으로 변환한다', () => {
      expect(toApiToDateTime('2026-07-29')).toBe('2026-07-30T00:00:00')
    })

    it('월말(7월 31일) → 다음 달 1일', () => {
      expect(toApiToDateTime('2026-07-31')).toBe('2026-08-01T00:00:00')
    })

    it('연말(12월 31일) → 다음 해 1월 1일', () => {
      expect(toApiToDateTime('2026-12-31')).toBe('2027-01-01T00:00:00')
    })

    it('윤년 2월 29일 → 3월 1일', () => {
      expect(toApiToDateTime('2024-02-29')).toBe('2024-03-01T00:00:00')
    })

    it('평년 2월 28일 → 3월 1일', () => {
      expect(toApiToDateTime('2026-02-28')).toBe('2026-03-01T00:00:00')
    })

    it('오늘 프리셋(시작=종료=오늘)이면 API 범위가 하루 전체를 커버한다', () => {
      const from = toApiFromDateTime('2026-07-29')
      const to = toApiToDateTime('2026-07-29')
      // from <= createdAt < to  →  2026-07-29T00:00:00 ~ 2026-07-30T00:00:00
      expect(from).toBe('2026-07-29T00:00:00')
      expect(to).toBe('2026-07-30T00:00:00')
      expect(from < to).toBe(true)
    })
  })

  describe('API 쿼리 파라미터 구성', () => {
    it('날짜와 상태 필터가 함께 올바르게 변환된다', () => {
      const from = '2026-07-01'
      const to = '2026-07-29'
      const status = 'AI_ANALYZED'

      const query = {
        from: toApiFromDateTime(from),
        to: toApiToDateTime(to),
        status,
      }

      expect(query.from).toBe('2026-07-01T00:00:00')
      expect(query.to).toBe('2026-07-30T00:00:00')
      expect(query.status).toBe('AI_ANALYZED')
    })

    it('시작일이 종료일보다 뒤이면 변환 후에도 from이 to보다 크거나 같다 (UI 검증으로 막아야 하는 케이스)', () => {
      // from=2026-07-30, to=2026-07-29 → 잘못된 입력
      const from = toApiFromDateTime('2026-07-30')
      const to = toApiToDateTime('2026-07-29')
      // 2026-07-30T00:00:00 >= 2026-07-30T00:00:00
      expect(from >= to).toBe(true)
    })
  })
})
