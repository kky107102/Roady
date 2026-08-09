/**
 * 로컬 타임존 기준 날짜 유틸리티.
 * toISOString()은 UTC 기준이므로 한국 시간대에서 날짜가 하루 이전으로 계산될 수 있어 사용하지 않는다.
 */

function pad2(n: number): string {
  return String(n).padStart(2, '0')
}

function localYMD(d: Date): string {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

/** 로컬 타임존 기준 오늘 날짜를 YYYY-MM-DD 형식으로 반환 */
export function todayLocalStr(): string {
  return localYMD(new Date())
}

interface DateTimeFormatOptions {
  includeYear?: boolean
  invalidValue?: 'input' | 'empty'
}

/** API 날짜·시간을 화면에서 사용하는 한국어 형식으로 변환한다. */
export function formatKoreanDateTime(
  value: string | null | undefined,
  { includeYear = true, invalidValue = 'input' }: DateTimeFormatOptions = {},
): string {
  if (!value) return '-'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return invalidValue === 'input' ? value : '-'

  return date.toLocaleString('ko-KR', {
    ...(includeYear ? { year: 'numeric' as const } : {}),
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

export function formatShortKoreanDateTime(value: string | null | undefined): string {
  return formatKoreanDateTime(value, { includeYear: false })
}

export function formatKoreanDateTimeOrDash(value: string | null | undefined): string {
  return formatKoreanDateTime(value, { invalidValue: 'empty' })
}

/** 로컬 타임존 기준 오늘로부터 offsetDays일 전 날짜를 YYYY-MM-DD 형식으로 반환 */
export function localDateOffset(offsetDays: number): string {
  const d = new Date()
  d.setDate(d.getDate() - offsetDays)
  return localYMD(d)
}

export const DATE_RANGE_PRESETS = [
  { label: '오늘', offset: 0 },
  { label: '7일', offset: 6 },
  { label: '30일', offset: 29 },
] as const

export const DEFAULT_DATE_RANGE_PRESET = 1
export const DATE_RANGE_ORDER_ERROR = '시작일은 종료일보다 이전이어야 합니다.'
export const ALL_DATE_RANGE_QUERY_VALUE = 'all'

export function validateDateRange(from: string, to: string): string {
  return from && to && from > to ? DATE_RANGE_ORDER_ERROR : ''
}

export function dateRangeForPreset(index: number): { from: string; to: string } {
  const preset = DATE_RANGE_PRESETS[index] ?? DATE_RANGE_PRESETS[DEFAULT_DATE_RANGE_PRESET]
  return { from: localDateOffset(preset.offset), to: todayLocalStr() }
}

function firstQueryString(value: unknown): string {
  const raw = Array.isArray(value) ? value[0] : value
  return typeof raw === 'string' ? raw : ''
}

export function dateRangeFromQuery(
  query: { from?: unknown; to?: unknown; range?: unknown },
  fallback = dateRangeForPreset(DEFAULT_DATE_RANGE_PRESET),
): { from: string; to: string } {
  if (firstQueryString(query.range) === ALL_DATE_RANGE_QUERY_VALUE) return { from: '', to: '' }
  return {
    from: firstQueryString(query.from) || fallback.from,
    to: firstQueryString(query.to) || fallback.to,
  }
}

export function dateRangeToQuery(from: string, to: string): Record<string, string> {
  if (!from && !to) return { range: ALL_DATE_RANGE_QUERY_VALUE }
  return {
    ...(from ? { from } : {}),
    ...(to ? { to } : {}),
  }
}

export function matchingDateRangePreset(from: string, to: string): number | null {
  if (!from || !to || to !== todayLocalStr()) return null
  const index = DATE_RANGE_PRESETS.findIndex((preset) => from === localDateOffset(preset.offset))
  return index >= 0 ? index : null
}

/**
 * UI 시작일(YYYY-MM-DD)을 백엔드 API 날짜시간 문자열로 변환.
 * 백엔드 조건이 from <= createdAt 이므로 해당 날 자정을 그대로 사용한다.
 * 예: '2026-07-29' → '2026-07-29T00:00:00'
 */
export function toApiFromDateTime(dateStr: string): string {
  return `${dateStr}T00:00:00`
}

/**
 * UI 종료일(YYYY-MM-DD)을 백엔드 API 날짜시간 문자열로 변환.
 * 백엔드 조건이 createdAt < to 이므로 다음 날 자정으로 변환한다.
 * Date 생성자에 (year, month-1, day)를 전달해 로컬 타임존 기준으로 계산하며
 * 월말·연말·윤년을 올바르게 처리한다.
 * 예: '2026-07-29' → '2026-07-30T00:00:00'
 *     '2026-07-31' → '2026-08-01T00:00:00'
 *     '2026-12-31' → '2027-01-01T00:00:00'
 *     '2024-02-29' → '2024-03-01T00:00:00'
 */
export function toApiToDateTime(dateStr: string): string {
  const [y, m, d] = dateStr.split('-').map(Number) as [number, number, number]
  const next = new Date(y, m - 1, d)
  next.setDate(next.getDate() + 1)
  return `${localYMD(next)}T00:00:00`
}
