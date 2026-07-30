import { describe, it, expect, vi, beforeEach, beforeAll, afterAll } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import type { DamageDetail, DamageAnalysis } from '@/types/damage'

// ── API mock ─────────────────────────────────────────────────────────────────

const mockApi = vi.hoisted(() => ({
  getDetail: vi.fn<(id: number) => Promise<DamageDetail>>(),
  getAnalysisJobs: vi.fn<(id: number) => Promise<DamageAnalysis[]>>(),
  getImageContent: vi.fn<(damageId: number, imageId: number) => Promise<Blob>>(),
}))

vi.mock('@/api/damages', () => ({ damagesApi: mockApi }))

// ── URL mock (jsdom에서 지원하지 않음) ───────────────────────────────────────

beforeAll(() => {
  vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock')
  vi.spyOn(URL, 'revokeObjectURL').mockReturnValue(undefined)
})

afterAll(() => {
  vi.restoreAllMocks()
})

// ── 컴포넌트 지연 임포트 (mock 등록 후) ─────────────────────────────────────

const { default: DamageDetailPanel } = await import(
  '@/components/damages/DamageDetailPanel.vue'
)

// ── 테스트 픽스처 ────────────────────────────────────────────────────────────

const baseDetail: DamageDetail = {
  id: 42,
  robotId: 7,
  reportedBy: null,
  assignedTo: null,
  description: '도로 균열 발생',
  latitude: 37.5665,
  longitude: 126.978,
  capturedAt: '2026-07-01T10:00:00',
  currentStatus: 'REVIEW_REQUIRED',
  imageCount: 0,
  images: [],
  createdAt: '2026-07-01T09:00:00',
  updatedAt: '2026-07-01T09:00:00',
}

const detailWithImages: DamageDetail = {
  ...baseDetail,
  imageCount: 2,
  images: [
    { id: 1, damageId: 42, sortOrder: 1, originalFilename: 'a.jpg', contentType: 'image/jpeg', sizeBytes: 1024, createdAt: '2026-07-01T10:00:00' },
    { id: 2, damageId: 42, sortOrder: 2, originalFilename: 'b.jpg', contentType: 'image/jpeg', sizeBytes: 1024, createdAt: '2026-07-01T10:00:00' },
  ],
}

const successAnalysis: DamageAnalysis = {
  id: 1,
  damageId: 42,
  damaged: true,
  damageScore: 85,
  repairRequired: true,
  repairPriority: 'HIGH',
  confidenceScore: 0.92,
  analysisStatus: 'SUCCESS',
  analyzedAt: '2026-07-01T10:05:00',
  createdAt: '2026-07-01T10:05:00',
}

// ── 마운트 헬퍼 ──────────────────────────────────────────────────────────────

function mountPanel(damageId: number | null = 42) {
  return mount(DamageDetailPanel, {
    props: { damageId },
    global: {
      stubs: {
        LoadingSpinner: {
          // label prop을 텍스트로 렌더링해 전체 로딩과 이미지 로딩을 구분할 수 있게 함
          template: '<div role="status" data-testid="loading-spinner">{{ label }}</div>',
          props: ['label'],
        },
        ErrorState: {
          template: '<div data-testid="error-state"><button type="button" @click="$emit(\'retry\')">재시도</button></div>',
          emits: ['retry'],
        },
        StatusBadge: {
          template: '<span data-testid="status-badge">{{ label }}</span>',
          props: ['type', 'label'],
        },
      },
    },
  })
}

// ── 테스트 ───────────────────────────────────────────────────────────────────

describe('DamageDetailPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── 로딩 상태 ──────────────────────────────────────────────────────────────

  it('API 응답 대기 중 "사건 정보 불러오는 중" 스피너를 표시한다', () => {
    mockApi.getDetail.mockReturnValue(new Promise(() => {}))
    mockApi.getAnalysisJobs.mockReturnValue(new Promise(() => {}))

    const wrapper = mountPanel(42)

    const spinners = wrapper.findAll('[data-testid="loading-spinner"]')
    expect(spinners.some((s) => s.text().includes('사건 정보 불러오는 중'))).toBe(true)
    expect(wrapper.find('[data-testid="error-state"]').exists()).toBe(false)
  })

  // ── 이미지 로딩 상태 분리 ─────────────────────────────────────────────────

  it('이미지 로드 중에는 상세 내용을 표시하며 이미지 로딩 문구만 보여준다', async () => {
    mockApi.getDetail.mockResolvedValue(detailWithImages)
    mockApi.getAnalysisJobs.mockResolvedValue([])
    // getImageContent는 영원히 응답하지 않음 → 이미지만 로딩 중 상태 유지
    mockApi.getImageContent.mockReturnValue(new Promise(() => {}))

    const wrapper = mountPanel(42)
    await flushPromises() // detail + analyses 완료, 이미지 로드 진행 중

    // 전체 로딩 오버레이 없음 → 상세 내용이 보임
    expect(wrapper.text()).toContain('도로 균열 발생')

    const spinners = wrapper.findAll('[data-testid="loading-spinner"]')

    // 전체 로딩 스피너("사건 정보 불러오는 중")는 없음
    expect(spinners.some((s) => s.text().includes('사건 정보 불러오는 중'))).toBe(false)

    // 이미지 로딩 스피너("이미지 불러오는 중")는 있음
    expect(spinners.some((s) => s.text().includes('이미지 불러오는 중'))).toBe(true)
  })

  // ── 오류 상태 ──────────────────────────────────────────────────────────────

  it('getDetail 실패 시 오류 상태를 표시한다', async () => {
    mockApi.getDetail.mockRejectedValue(new Error('network error'))
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.find('[data-testid="error-state"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="loading-spinner"]').exists()).toBe(false)
  })

  it('재시도 버튼 클릭 시 데이터를 다시 조회한다', async () => {
    mockApi.getDetail
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    await wrapper.find('[data-testid="error-state"] button').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="error-state"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('도로 균열 발생')
  })

  // ── 기본 정보 렌더링 ───────────────────────────────────────────────────────

  it('사건 기본 정보를 올바르게 렌더링한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('도로 균열 발생')
    expect(wrapper.text()).toContain('RD-2026-000042')
    expect(wrapper.text()).toContain('37.5665')
    expect(wrapper.text()).toContain('미배정')
  })

  // ── 이미지 상태 ────────────────────────────────────────────────────────────

  it('imageCount가 0이면 "이미지 없음"을 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('이미지 없음')
  })

  it('일부 이미지 실패 시 성공한 이미지만 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(detailWithImages)
    mockApi.getAnalysisJobs.mockResolvedValue([])
    mockApi.getImageContent
      .mockResolvedValueOnce(new Blob(['img1'])) // 이미지 1 성공
      .mockRejectedValueOnce(new Error('img2 failed')) // 이미지 2 실패

    const wrapper = mountPanel(42)
    await flushPromises()

    // "불러올 수 없습니다"는 전체 실패일 때만 표시 → 일부 성공이면 없어야 함
    expect(wrapper.text()).not.toContain('이미지를 불러올 수 없습니다')
    // 성공한 이미지의 src가 blob:mock으로 설정됨
    const images = wrapper.findAll('img.detail-img').filter((img) => img.attributes('src') === 'blob:mock')
    expect(images.length).toBe(1)
  })

  it('모든 이미지 로드에 실패하면 "이미지를 불러올 수 없습니다"를 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(detailWithImages)
    mockApi.getAnalysisJobs.mockResolvedValue([])
    mockApi.getImageContent.mockRejectedValue(new Error('image load failed'))

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('이미지를 불러올 수 없습니다')
  })

  // ── AI 분석 오류 구분 ─────────────────────────────────────────────────────

  it('AI API 실패 시 오류 메시지와 재시도 버튼을 표시하며 상세 정보는 유지한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockRejectedValue(new Error('analysis api error'))

    const wrapper = mountPanel(42)
    await flushPromises()

    // 상세 정보는 계속 표시됨
    expect(wrapper.text()).toContain('도로 균열 발생')
    // AI 오류 메시지 표시
    expect(wrapper.text()).toContain('AI 분석 결과를 불러오지 못했습니다')
    // 재시도 버튼 존재
    expect(wrapper.find('[data-testid="analysis-retry-btn"]').exists()).toBe(true)
    // "분석 결과가 없습니다"는 표시 안 됨
    expect(wrapper.text()).not.toContain('분석 결과가 없습니다')
  })

  it('AI API가 빈 배열을 반환하면 "분석 결과가 없습니다"를 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('분석 결과가 없습니다')
    expect(wrapper.text()).not.toContain('불러오지 못했습니다')
    expect(wrapper.find('[data-testid="analysis-retry-btn"]').exists()).toBe(false)
  })

  it('AI 분석 재시도 성공 시 분석 결과를 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs
      .mockRejectedValueOnce(new Error('first attempt failed'))
      .mockResolvedValueOnce([successAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.find('[data-testid="analysis-retry-btn"]').exists()).toBe(true)

    await wrapper.find('[data-testid="analysis-retry-btn"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="analysis-retry-btn"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('분석 완료')
    expect(wrapper.text()).toContain('85점')
  })

  it('사건 변경 시 이전 AI 분석 오류 상태를 초기화한다', async () => {
    const detail2: DamageDetail = { ...baseDetail, id: 2, description: '두 번째 사건' }

    mockApi.getDetail
      .mockResolvedValueOnce(baseDetail)
      .mockResolvedValueOnce(detail2)
    mockApi.getAnalysisJobs
      .mockRejectedValueOnce(new Error('analysis error'))
      .mockResolvedValueOnce([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('AI 분석 결과를 불러오지 못했습니다')

    await wrapper.setProps({ damageId: 2 })
    await flushPromises()

    expect(wrapper.text()).not.toContain('AI 분석 결과를 불러오지 못했습니다')
    expect(wrapper.text()).toContain('분석 결과가 없습니다')
  })

  // ── AI 분석 상태 라벨 ─────────────────────────────────────────────────────

  it('SUCCESS 분석 상태를 "분석 완료"로 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([successAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('분석 완료')
    expect(wrapper.text()).toContain('85점')
    expect(wrapper.text()).toContain('92%')
  })

  it('PENDING 분석 상태를 "분석 대기"로 표시한다', async () => {
    const pendingAnalysis: DamageAnalysis = { ...successAnalysis, analysisStatus: 'PENDING', damageScore: null, confidenceScore: null, repairRequired: null }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([pendingAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('분석 대기')
  })

  it('IN_PROGRESS 분석 상태를 "분석 중"으로 표시한다', async () => {
    const inProgressAnalysis: DamageAnalysis = { ...successAnalysis, analysisStatus: 'IN_PROGRESS', damageScore: null, confidenceScore: null }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([inProgressAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('분석 중')
  })

  it('FAILED 분석 상태를 "분석 실패"로 표시한다', async () => {
    const failedAnalysis: DamageAnalysis = { ...successAnalysis, analysisStatus: 'FAILED', damageScore: null, confidenceScore: null }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([failedAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('분석 실패')
  })

  // ── 닫기 ───────────────────────────────────────────────────────────────────

  it('닫기 버튼 클릭 시 close 이벤트를 발생시킨다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    await wrapper.find('button[aria-label="닫기"]').trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('Escape 키 입력 시 close 이벤트를 발생시킨다', () => {
    mockApi.getDetail.mockReturnValue(new Promise(() => {}))
    mockApi.getAnalysisJobs.mockReturnValue(new Promise(() => {}))

    const wrapper = mountPanel(42)

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('Escape 이외의 키는 close 이벤트를 발생시키지 않는다', () => {
    mockApi.getDetail.mockReturnValue(new Promise(() => {}))
    mockApi.getAnalysisJobs.mockReturnValue(new Promise(() => {}))

    const wrapper = mountPanel(42)

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))

    expect(wrapper.emitted('close')).toBeFalsy()
  })

  // ── 경쟁 조건 ──────────────────────────────────────────────────────────────

  it('사건 전환 중 이전 응답이 새 데이터를 덮어쓰지 않는다', async () => {
    const detail1: DamageDetail = { ...baseDetail, id: 1, description: '첫 번째 사건' }
    const detail2: DamageDetail = { ...baseDetail, id: 2, description: '두 번째 사건' }

    let resolveFirst!: (d: DamageDetail) => void
    const firstPromise = new Promise<DamageDetail>((res) => { resolveFirst = res })

    mockApi.getDetail
      .mockReturnValueOnce(firstPromise)
      .mockResolvedValueOnce(detail2)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(1)

    // 첫 번째 요청 응답 전에 두 번째 사건으로 전환
    await wrapper.setProps({ damageId: 2 })
    await flushPromises()

    // stale 첫 번째 응답 도착
    resolveFirst(detail1)
    await flushPromises()

    expect(wrapper.text()).toContain('두 번째 사건')
    expect(wrapper.text()).not.toContain('첫 번째 사건')
  })

  it('사건 전환 시 이전 상세 데이터가 즉시 제거된다', async () => {
    mockApi.getDetail
      .mockResolvedValueOnce(baseDetail)
      .mockReturnValueOnce(new Promise(() => {}))
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('도로 균열 발생')

    await wrapper.setProps({ damageId: 99 })

    // 두 번째 로딩 중: 이전 내용이 없고 전체 로딩 스피너가 보여야 함
    expect(wrapper.text()).not.toContain('도로 균열 발생')
    const spinners = wrapper.findAll('[data-testid="loading-spinner"]')
    expect(spinners.some((s) => s.text().includes('사건 정보 불러오는 중'))).toBe(true)
  })

  // ── Object URL 해제 및 언마운트 무효화 ────────────────────────────────────

  it('언마운트 시 blob URL을 해제한다', async () => {
    mockApi.getDetail.mockResolvedValue(detailWithImages)
    mockApi.getAnalysisJobs.mockResolvedValue([])
    mockApi.getImageContent.mockResolvedValue(new Blob(['img']))

    const wrapper = mountPanel(42)
    await flushPromises()

    const beforeCount = vi.mocked(URL.revokeObjectURL).mock.calls.length

    wrapper.unmount()

    expect(vi.mocked(URL.revokeObjectURL).mock.calls.length).toBeGreaterThan(beforeCount)
  })

  it('언마운트 후 지연된 이미지 응답이 도착해도 URL.createObjectURL을 호출하지 않는다', async () => {
    mockApi.getDetail.mockResolvedValue(detailWithImages)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    let resolveImage!: (b: Blob) => void
    const imagePromise = new Promise<Blob>((res) => { resolveImage = res })
    mockApi.getImageContent.mockReturnValue(imagePromise)

    const wrapper = mountPanel(42)
    await flushPromises() // detail/analyses 완료, 이미지 로드 진행 중

    // 언마운트 전 시점의 createObjectURL 호출 횟수 기록
    const callCountBeforeUnmount = vi.mocked(URL.createObjectURL).mock.calls.length

    wrapper.unmount()

    // 언마운트 후 지연된 이미지 응답 도착
    resolveImage(new Blob(['img']))
    await flushPromises()

    // createObjectURL은 추가 호출되지 않아야 함
    expect(vi.mocked(URL.createObjectURL).mock.calls.length).toBe(callCountBeforeUnmount)
  })
})
