import { describe, it, expect, vi, beforeEach, beforeAll, afterAll } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia } from 'pinia'
import type { DamageDetail, DamageAnalysis, DamageListItem } from '@/types/damage'

// ── API mock ─────────────────────────────────────────────────────────────────

const mockApi = vi.hoisted(() => ({
  getDetail: vi.fn<(id: number) => Promise<DamageDetail>>(),
  getAnalysisJobs: vi.fn<(id: number) => Promise<DamageAnalysis[]>>(),
  getImageContent: vi.fn<(damageId: number, imageId: number) => Promise<Blob>>(),
}))

const mockRobotsApi = vi.hoisted(() => ({
  get: vi.fn(),
}))

vi.mock('@/api/damages', () => ({ damagesApi: mockApi }))
vi.mock('@/api/robots', () => ({ robotsApi: mockRobotsApi }))

// ── URL mock (jsdom에서 지원하지 않음) ───────────────────────────────────────

beforeAll(() => {
  vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock')
  vi.spyOn(URL, 'revokeObjectURL').mockReturnValue(undefined)
  vi.spyOn(window, 'confirm').mockReturnValue(true)
})

afterAll(() => {
  vi.restoreAllMocks()
})

// ── 컴포넌트 지연 임포트 (mock 등록 후) ─────────────────────────────────────

const { default: DamageDetailPanel } = await import('@/components/damages/DamageDetailPanel.vue')

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
  currentStatus: 'AI_ANALYZED',
  imageCount: 0,
  images: [],
  createdAt: '2026-07-01T09:00:00',
  updatedAt: '2026-07-01T09:00:00',
}

const detailWithImages: DamageDetail = {
  ...baseDetail,
  imageCount: 2,
  images: [
    {
      id: 1,
      damageId: 42,
      sortOrder: 1,
      originalFilename: 'a.jpg',
      contentType: 'image/jpeg',
      sizeBytes: 1024,
      createdAt: '2026-07-01T10:00:00',
    },
    {
      id: 2,
      damageId: 42,
      sortOrder: 2,
      originalFilename: 'b.jpg',
      contentType: 'image/jpeg',
      sizeBytes: 1024,
      createdAt: '2026-07-01T10:00:00',
    },
  ],
}

const successAnalysis: DamageAnalysis = {
  id: 1,
  damageId: 42,
  damaged: true,
  damageScore: 85,
  damageType: 'CRACK',
  repairRequired: true,
  repairPriority: 'HIGH',
  confidenceScore: 0.92,
  analysisStatus: 'SUCCESS',
  analyzedAt: '2026-07-01T10:05:00',
  createdAt: '2026-07-01T10:05:00',
}

// ── 마운트 헬퍼 ──────────────────────────────────────────────────────────────

function mountPanel(
  damageId: number | null = 42,
  summary: DamageListItem | null = null,
  backTo = '/damages',
) {
  return mount(DamageDetailPanel, {
    props: { damageId, summary, backTo },
    global: {
      plugins: [createPinia()],
      stubs: {
        LoadingSpinner: {
          template: '<div role="status" data-testid="loading-spinner">{{ label }}</div>',
          props: ['label'],
        },
        ErrorState: {
          template:
            '<div data-testid="error-state"><button type="button" @click="$emit(\'retry\')">재시도</button></div>',
          emits: ['retry'],
        },
        StatusBadge: {
          template:
            '<span data-testid="status-badge" :data-type="type" :data-size="size">{{ label }}</span>',
          props: ['type', 'label', 'size'],
        },
        AiResultBadge: {
          template:
            '<span data-testid="ai-result-badge" :data-type="type" :data-size="size"><span>AI 판독</span><span>{{ label }}</span></span>',
          props: ['type', 'label', 'size'],
        },
        RepairRequestModal: {
          template: '<div data-testid="request-view-modal">요청서 조회 모달</div>',
          props: [
            'detail',
            'imageBlobUrls',
            'imagesLoading',
            'readonly',
            'officialName',
            'copyState',
          ],
        },
        RepairCompletionModal: {
          template: '<div data-testid="completion-report-modal">완료 보고서 모달</div>',
          props: [
            'readonly',
            'completedAt',
            'requestedAt',
            'note',
            'officialName',
            'repairerName',
            'beforeImages',
            'imageBlobUrls',
            'copyState',
          ],
        },
        RouterLink: {
          template:
            '<a data-testid="router-link" :data-route-name="to.name" :data-damage-id="to.params && to.params.damageId" :data-back-to="to.query && to.query.backTo"><slot /></a>',
          props: ['to'],
        },
      },
    },
  })
}

// ── 테스트 ───────────────────────────────────────────────────────────────────

describe('DamageDetailPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRobotsApi.get.mockResolvedValue({
      id: 7,
      name: 'Roady-Unit-07',
    })
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
    mockApi.getImageContent.mockReturnValue(new Promise(() => {}))

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('도로 균열 발생')

    const spinners = wrapper.findAll('[data-testid="loading-spinner"]')

    expect(spinners.some((s) => s.text().includes('사건 정보 불러오는 중'))).toBe(false)
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
    mockApi.getDetail.mockRejectedValueOnce(new Error('fail')).mockResolvedValueOnce(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    await wrapper.find('[data-testid="error-state"] button').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="error-state"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('도로 균열 발생')
  })

  // ── 헤더 및 사건 기본 정보 렌더링 ────────────────────────────────────────

  it('헤더 제목 "사건 상세 정보"를 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('사건 상세 정보')
  })

  it('사건 기본 정보를 올바르게 렌더링한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('도로 균열 발생')
    expect(wrapper.text()).toContain('RD-2026-000042')
    expect(wrapper.text()).toContain('37.5665')
  })

  it('도로명 주소가 있으면 좌표 대신 주소와 "주변"을 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue({
      ...baseDetail,
      addressName: '서울특별시 강남구 역삼동 123',
      roadAddressName: '서울특별시 강남구 역삼대로13길 23',
    })
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('서울특별시 강남구 역삼대로13길 23 주변')
    expect(wrapper.text()).not.toContain('위도 37.5665')
  })

  it('robotId로 조회한 탐지 로봇 이름을 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(mockRobotsApi.get).toHaveBeenCalledWith(7)
    expect(wrapper.text()).toContain('탐지 로봇: Roady-Unit-07')
  })

  it('탐지 일시를 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('2026')
  })

  // ── 이미지 상태 ────────────────────────────────────────────────────────────

  it('imageCount가 0이면 고정 이미지 영역에 빈 상태를 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.find('.image-frame').exists()).toBe(true)
    expect(wrapper.text()).toContain('등록된 탐지 이미지가 없습니다.')
  })

  it('일부 이미지 실패 시 성공한 이미지만 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(detailWithImages)
    mockApi.getAnalysisJobs.mockResolvedValue([])
    mockApi.getImageContent
      .mockResolvedValueOnce(new Blob(['img1']))
      .mockRejectedValueOnce(new Error('img2 failed'))

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).not.toContain('이미지를 불러올 수 없습니다')
    const images = wrapper
      .findAll('img.detail-img')
      .filter((img) => img.attributes('src') === 'blob:mock')
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

    expect(wrapper.text()).toContain('도로 균열 발생')
    expect(wrapper.text()).toContain('AI 분석 결과를 불러오지 못했습니다')
    expect(wrapper.find('[data-testid="analysis-retry-btn"]').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('분석 결과가 없습니다')
  })

  it('AI API 조회가 실패해도 목록의 AI 요약 정보가 있으면 판독 결과를 표시한다', async () => {
    const summary: DamageListItem = {
      id: 42,
      robotId: 7,
      assignedTo: null,
      description: '도로 균열 발생',
      latitude: 37.5665,
      longitude: 126.978,
      capturedAt: '2026-07-01T10:00:00',
      currentStatus: 'AI_ANALYZED',
      processingPriority: null,
      imageCount: 0,
      damageScore: 85,
      damageType: 'CRACK',
      repairRequired: true,
      repairPriority: 'HIGH',
      confidenceScore: 0.92,
      createdAt: '2026-07-01T09:00:00',
    }
    mockApi.getDetail.mockResolvedValue({ ...baseDetail, currentStatus: 'AI_ANALYZED' })
    mockApi.getAnalysisJobs.mockRejectedValue(new Error('analysis api error'))

    const wrapper = mountPanel(42, summary)
    await flushPromises()

    expect(wrapper.find('[data-testid="analysis-retry-btn"]').exists()).toBe(false)
    expect(wrapper.find('.ai-card-body').text()).toContain('85%')
    expect(wrapper.find('.ai-card-body').text()).toContain('균열')
    expect(wrapper.get('[data-testid="ai-result-badge"]').text()).toContain('AI 판독')
  })

  it('AI API가 빈 배열을 반환해도 요약 영역을 유지하고 빈 값을 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('AI 판독 요약')
    expect(wrapper.find('.ai-card-body').exists()).toBe(true)
    expect(wrapper.find('.ai-card-body').text()).toContain('-')
    expect(wrapper.find('.ai-card-body').text()).not.toContain('보류')
    expect(wrapper.text()).not.toContain('분석 결과가 없습니다')
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
    expect(wrapper.text()).toContain('85%')
    expect(wrapper.text()).toContain('92%')
  })

  it('사건 변경 시 이전 AI 분석 오류 상태를 초기화한다', async () => {
    const detail2: DamageDetail = { ...baseDetail, id: 2, description: '두 번째 사건' }

    mockApi.getDetail.mockResolvedValueOnce(baseDetail).mockResolvedValueOnce(detail2)
    mockApi.getAnalysisJobs
      .mockRejectedValueOnce(new Error('analysis error'))
      .mockResolvedValueOnce([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('AI 분석 결과를 불러오지 못했습니다')

    await wrapper.setProps({ damageId: 2 })
    await flushPromises()

    expect(wrapper.text()).not.toContain('AI 분석 결과를 불러오지 못했습니다')
    expect(wrapper.find('.ai-card-body').text()).toContain('-')
  })

  it('AI API 조회가 실패해도 요약 항목과 빈 값을 계속 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockRejectedValue(new Error('analysis error'))

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('AI 분석 결과를 불러오지 못했습니다')
    expect(wrapper.find('[data-testid="analysis-retry-btn"]').exists()).toBe(true)
    expect(wrapper.find('.ai-card-body').exists()).toBe(true)
    expect(wrapper.find('.ai-card-body').text()).toContain('-')
  })

  // ── AI 판독 요약 카드 ─────────────────────────────────────────────────────

  it('파손률을 % 단위로 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([successAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    const scoreRow = wrapper.get('.score-value-row')
    expect(scoreRow.text()).toContain('85%')
    expect(scoreRow.find('.score-bar').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('탐지 영역 내 파손 비율')
  })

  it('신뢰도를 %로 변환해 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([successAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('92%')
  })

  it('파손 유형 코드를 한글로 변환해 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([successAnalysis]) // damageType: 'CRACK'

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('균열')
  })

  it('AI 우선순위와 파손 유형은 출처와 결과를 분리한 공통 태그로 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([successAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    const resultBadges = wrapper.findAll('.ai-result-badge')
    expect(resultBadges).toHaveLength(2)
    expect(resultBadges[0]!.findAll('span')[0]!.text()).toBe('AI 판독')
    expect(resultBadges[0]!.findAll('span')[1]!.text()).toBe('높음')
    expect(resultBadges[0]!.attributes('data-type')).toBe('warning')
    expect(resultBadges[0]!.attributes('data-size')).toBe('medium')
    expect(resultBadges[1]!.findAll('span')[0]!.text()).toBe('AI 판독')
    expect(resultBadges[1]!.findAll('span')[1]!.text()).toBe('균열')
    expect(resultBadges[1]!.attributes('data-type')).toBe('neutral')
    expect(resultBadges[1]!.attributes('data-size')).toBe('medium')
  })

  it('HIGH 우선순위 코드를 "높음"으로 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([successAnalysis]) // repairPriority: 'HIGH'

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('높음')
  })

  it('URGENT 우선순위를 "긴급"으로 표시한다', async () => {
    const urgentAnalysis: DamageAnalysis = { ...successAnalysis, repairPriority: 'URGENT' }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([urgentAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('긴급')
  })

  it('NORMAL 우선순위를 "보통"으로 표시한다', async () => {
    const normalAnalysis: DamageAnalysis = { ...successAnalysis, repairPriority: 'NORMAL' }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([normalAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('보통')
  })

  it('LOW 우선순위를 "낮음"으로 표시한다', async () => {
    const lowAnalysis: DamageAnalysis = { ...successAnalysis, repairPriority: 'LOW' }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([lowAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('낮음')
  })

  it('우선순위 값이 없으면 "보류"로 표시한다', async () => {
    const pendingPriorityAnalysis: DamageAnalysis = {
      ...successAnalysis,
      repairPriority: null,
    }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([pendingPriorityAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(
      wrapper
        .findAll('[data-testid="ai-result-badge"]')
        .some((badge) => badge.text() === 'AI 판독보류'),
    ).toBe(true)
    expect(wrapper.find('.ai-card-body').text()).toContain('보류')
  })

  it('레거시 MISSING 파손 유형을 "큰 결손"으로 표시한다', async () => {
    const missingAnalysis: DamageAnalysis = { ...successAnalysis, damageType: 'MISSING' }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([missingAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('큰 결손')
  })

  it('WEAR 파손 유형을 "마모"로 표시한다', async () => {
    const wearAnalysis: DamageAnalysis = { ...successAnalysis, damageType: 'WEAR' }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([wearAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('마모')
  })

  it('레거시 BREAKAGE 파손 유형을 "작은 결손"으로 표시한다', async () => {
    const breakageAnalysis: DamageAnalysis = { ...successAnalysis, damageType: 'BREAKAGE' }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([breakageAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('작은 결손')
  })

  it('분석값이 없을 때 우선순위는 "보류", 나머지 값은 "-"로 표시한다', async () => {
    const emptyAnalysis: DamageAnalysis = {
      ...successAnalysis,
      damageScore: null,
      damageType: null,
      repairPriority: null,
      confidenceScore: null,
    }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([emptyAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.find('.ai-card-body').text()).toContain('보류')
    expect(wrapper.find('.ai-card-body').text()).toContain('-')
  })

  it('PENDING 상태에서 데이터가 없으면 "-"를 표시한다', async () => {
    const pendingAnalysis: DamageAnalysis = {
      ...successAnalysis,
      analysisStatus: 'PENDING',
      damageScore: null,
      damageType: null,
      confidenceScore: null,
      repairPriority: null,
      repairRequired: null,
    }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([pendingAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    const text = wrapper.text()
    const dashCount = (text.match(/-/g) ?? []).length
    expect(dashCount).toBeGreaterThanOrEqual(4)
  })

  it('IN_PROGRESS 상태에서 데이터가 없으면 "-"를 표시한다', async () => {
    const inProgressAnalysis: DamageAnalysis = {
      ...successAnalysis,
      analysisStatus: 'IN_PROGRESS',
      damageScore: null,
      damageType: null,
      confidenceScore: null,
    }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([inProgressAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    const text = wrapper.text()
    expect((text.match(/-/g) ?? []).length).toBeGreaterThanOrEqual(2)
  })

  it('FAILED 상태에서 데이터가 없으면 "-"를 표시한다', async () => {
    const failedAnalysis: DamageAnalysis = {
      ...successAnalysis,
      analysisStatus: 'FAILED',
      damageScore: null,
      damageType: null,
      confidenceScore: null,
    }
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([failedAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    const text = wrapper.text()
    expect((text.match(/-/g) ?? []).length).toBeGreaterThanOrEqual(2)
  })

  // ── 판정 버튼 ──────────────────────────────────────────────────────────────

  it('"보수 불필요"와 "보수 필요" 버튼을 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    const labels = wrapper.findAll('button').map((b) => b.text())
    expect(labels).toContain('보수 불필요')
    expect(labels).toContain('보수 필요')
  })

  it('"보수 불필요" 클릭 시 확인 모달을 열고 확인 후 이벤트를 발생시킨다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    const btn = wrapper.findAll('button').find((b) => b.text() === '보수 불필요')
    await btn!.trigger('click')

    const modal = document.body.querySelector('[role="alertdialog"]') as HTMLElement
    expect(modal).not.toBeNull()
    expect(modal.textContent).toContain('보수 불필요로 판정할까요?')
    expect(wrapper.emitted('verdict-no-repair')).toBeFalsy()

    const confirmButton = Array.from(modal.querySelectorAll('button')).find((button) =>
      button.textContent?.includes('보수 불필요로 판정'),
    )
    confirmButton?.click()
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('verdict-no-repair')).toBeTruthy()
  })

  it('"보수 필요" 클릭 시 관리자 판정 모달을 열고 입력값을 저장한다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    const btn = wrapper.findAll('button').find((b) => b.text() === '보수 필요')
    await btn!.trigger('click')

    const modal = document.body.querySelector('.review-modal') as HTMLFormElement
    expect(modal).not.toBeNull()

    const selects = modal.querySelectorAll('select')
    ;(selects[0] as HTMLSelectElement).value = 'HIGH'
    selects[0]!.dispatchEvent(new Event('change'))
    ;(selects[1] as HTMLSelectElement).value = 'CRACK'
    selects[1]!.dispatchEvent(new Event('change'))
    const note = modal.querySelector('textarea') as HTMLTextAreaElement
    note.value = '균열 범위 확인 필요'
    note.dispatchEvent(new Event('input'))
    modal.dispatchEvent(new Event('submit'))
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('verdict-repair')?.[0]).toEqual([
      {
        processingPriority: 'HIGH',
        reviewDamageType: 'CRACK',
        reviewNote: '균열 범위 확인 필요',
      },
    ])
  })

  it('관리자 판정 모달에서 취소하면 상태 변경 이벤트를 발생시키지 않는다', async () => {
    mockApi.getDetail.mockResolvedValue(baseDetail)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    const btn = wrapper.findAll('button').find((button) => button.text() === '보수 필요')
    await btn!.trigger('click')
    const cancelButton = Array.from(document.body.querySelectorAll('button')).find(
      (button) => button.textContent === '취소',
    )
    cancelButton?.click()
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('verdict-repair')).toBeFalsy()
  })

  it('AI 분석 중에도 판정 영역과 비활성 버튼을 유지한다', async () => {
    mockApi.getDetail.mockResolvedValue({ ...baseDetail, currentStatus: 'AI_ANALYZING' })
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    const actions = wrapper.get('.detail-actions')
    expect(actions.attributes('data-action-mode')).toBe('waiting')
    expect(actions.text()).toContain('AI 분석 중입니다. 분석 완료 후 판정할 수 있습니다.')
    expect(actions.findAll('button')).toHaveLength(2)
    expect(
      actions.findAll('button').every((button) => button.attributes('disabled') !== undefined),
    ).toBe(true)
  })

  it('요청 전 사건은 관리자 판정 수정과 되돌리기·요청 작성 버튼을 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue({
      ...baseDetail,
      currentStatus: 'REQUESTED',
      processingPriority: 'HIGH',
      reviewDamageType: 'CRACK',
      reviewNote: '현장 확인 필요',
    })
    mockApi.getAnalysisJobs.mockResolvedValue([successAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    const actions = wrapper.get('.detail-actions')
    expect(actions.attributes('data-action-mode')).toBe('completed')
    expect(actions.text()).toContain('요청 전 · 관리자 확인 완료')
    expect(actions.text()).not.toContain('수정하기')
    expect(actions.text()).toContain('판정 되돌리기')
    expect(actions.text()).toContain('요청서 작성하기')
    expect(actions.text()).not.toContain('보수 관리 상세보기')
    expect(actions.find('.request-create-btn').attributes('disabled')).toBeUndefined()
    const managerReview = wrapper.get('.manager-review-card')
    expect(managerReview.text()).toContain('현장 확인 필요')
    expect(managerReview.get('.manager-review-edit-btn').text()).toContain('수정하기')
  })

  it('요청 완료 사건은 요청서 확인 버튼을 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue({ ...baseDetail, currentStatus: 'REPAIR_IN_PROGRESS' })
    mockApi.getAnalysisJobs.mockResolvedValue([successAnalysis])

    const wrapper = mountPanel(42, null, '/damages?review=confirmed&damageId=42')
    await flushPromises()

    const actions = wrapper.get('.detail-actions')
    expect(actions.text()).toContain('요청 완료 · 관리자 확인 완료')
    const button = actions.get('button.review-followup-btn')
    expect(button.text()).toBe('요청서 확인')
    await button.trigger('click')
    expect(wrapper.get('[data-testid="request-view-modal"]').text()).toContain('요청서 조회 모달')

    const repairLink = actions.get('a.repair-detail-link')
    expect(repairLink.text()).toBe('보수 관리 상세보기')
    expect(repairLink.attributes('data-route-name')).toBe('repair-detail')
    expect(repairLink.attributes('data-damage-id')).toBe('42')
    expect(repairLink.attributes('data-back-to')).toBe('/damages?review=confirmed&damageId=42')
  })

  it('보수 완료 사건은 보고서 확인 버튼을 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue({ ...baseDetail, currentStatus: 'REPAIR_COMPLETED' })
    mockApi.getAnalysisJobs.mockResolvedValue([successAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    const button = wrapper.get('button.review-followup-btn')
    expect(button.text()).toBe('보고서 확인')
    await button.trigger('click')
    expect(wrapper.get('[data-testid="completion-report-modal"]').text()).toContain(
      '완료 보고서 모달',
    )
    expect(wrapper.get('a.repair-detail-link').text()).toBe('보수 관리 상세보기')
  })

  it('판정 되돌리기 전용 확인 모달에서 확인하면 미확인 상태 복귀 이벤트를 발생시킨다', async () => {
    mockApi.getDetail.mockResolvedValue({ ...baseDetail, currentStatus: 'REQUESTED' })
    mockApi.getAnalysisJobs.mockResolvedValue([successAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    await wrapper.get('.pending-reset-btn').trigger('click')

    const modal = document.body.querySelector('[aria-labelledby="reset-verdict-title"]')
    expect(modal).not.toBeNull()
    expect(modal?.textContent).toContain('판정을 되돌릴까요?')
    expect(wrapper.emitted('verdict-reset')).toBeFalsy()

    const confirmButton = Array.from(modal?.querySelectorAll('button') ?? []).find((button) =>
      button.textContent?.includes('판정 되돌리기'),
    )
    confirmButton?.click()
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('verdict-reset')).toBeTruthy()
  })

  it('레거시 보수 예정 상태에서도 판정 되돌리기를 표시한다', async () => {
    mockApi.getDetail.mockResolvedValue({ ...baseDetail, currentStatus: 'REQUESTED' })
    mockApi.getAnalysisJobs.mockResolvedValue([successAnalysis])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.get('.pending-reset-btn').text()).toBe('판정 되돌리기')
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
    const firstPromise = new Promise<DamageDetail>((res) => {
      resolveFirst = res
    })

    mockApi.getDetail.mockReturnValueOnce(firstPromise).mockResolvedValueOnce(detail2)
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(1)

    await wrapper.setProps({ damageId: 2 })
    await flushPromises()

    resolveFirst(detail1)
    await flushPromises()

    expect(wrapper.text()).toContain('두 번째 사건')
    expect(wrapper.text()).not.toContain('첫 번째 사건')
  })

  it('사건 전환 시 이전 상세 데이터가 즉시 제거된다', async () => {
    mockApi.getDetail.mockResolvedValueOnce(baseDetail).mockReturnValueOnce(new Promise(() => {}))
    mockApi.getAnalysisJobs.mockResolvedValue([])

    const wrapper = mountPanel(42)
    await flushPromises()

    expect(wrapper.text()).toContain('도로 균열 발생')

    await wrapper.setProps({ damageId: 99 })

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
    const imagePromise = new Promise<Blob>((res) => {
      resolveImage = res
    })
    mockApi.getImageContent.mockReturnValue(imagePromise)

    const wrapper = mountPanel(42)
    await flushPromises()

    const callCountBeforeUnmount = vi.mocked(URL.createObjectURL).mock.calls.length

    wrapper.unmount()

    resolveImage(new Blob(['img']))
    await flushPromises()

    expect(vi.mocked(URL.createObjectURL).mock.calls.length).toBe(callCountBeforeUnmount)
  })
})
