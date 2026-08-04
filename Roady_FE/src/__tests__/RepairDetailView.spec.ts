import { describe, it, expect, vi, beforeEach, beforeAll, afterAll } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia } from 'pinia'
import type { DamageDetail } from '@/types/damage'

// ── API mock ─────────────────────────────────────────────────

const mockDamagesApi = vi.hoisted(() => ({
  getDetail: vi.fn<(id: number) => Promise<DamageDetail>>(),
  getImageContent: vi.fn<(damageId: number, imageId: number) => Promise<Blob>>(),
  clearDetailCache: vi.fn(),
}))

const mockRepairsApi = vi.hoisted(() => ({
  submitRequest: vi.fn(),
  cancelRequest: vi.fn(),
  completeRepair: vi.fn(),
}))

vi.mock('@/api/damages', () => ({ damagesApi: mockDamagesApi }))
vi.mock('@/api/repairs', () => ({ repairsApi: mockRepairsApi }))

// ── navigator.clipboard mock ──────────────────────────────────

const mockClipboard = { writeText: vi.fn() }

beforeAll(() => {
  vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock')
  vi.spyOn(URL, 'revokeObjectURL').mockReturnValue(undefined)
  Object.defineProperty(navigator, 'clipboard', {
    value: mockClipboard,
    writable: true,
    configurable: true,
  })
})

afterAll(() => {
  vi.restoreAllMocks()
})

// ── 컴포넌트 지연 임포트 ─────────────────────────────────────

const { default: RepairDetailView } = await import('@/views/RepairDetailView.vue')

// ── 테스트 픽스처 ────────────────────────────────────────────

const baseDetail: DamageDetail = {
  id: 6,
  robotId: 1,
  reportedBy: null,
  assignedTo: null,
  description: '개포로 점자블록 침하 탐지',
  roadAddressName: '서울특별시 강남구 개포로 123',
  addressName: null,
  latitude: 37.123456,
  longitude: 127.654321,
  capturedAt: '2026-08-03T11:20:00',
  currentStatus: 'REQUESTED',
  processingPriority: 'URGENT',
  reviewDamageType: 'CRACK',
  reviewNote: '현장 확인 필요',
  imageCount: 0,
  images: [],
  createdAt: '2026-01-01T00:00:00',
  updatedAt: '2026-08-03T12:00:00',
}

const detailInProgress: DamageDetail = { ...baseDetail, currentStatus: 'REPAIR_IN_PROGRESS' }
const detailCompleted: DamageDetail = { ...baseDetail, currentStatus: 'REPAIR_COMPLETED' }

// ── 마운트 헬퍼 ──────────────────────────────────────────────

async function mountView(damageId = 6) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/repairs/:damageId', name: 'repair-detail', component: RepairDetailView },
      { path: '/repairs', name: 'repairs', component: { template: '<div />' } },
    ],
  })
  await router.push(`/repairs/${damageId}`)

  return mount(RepairDetailView, {
    global: {
      plugins: [router, createPinia()],
      stubs: {
        // Teleport をインライン化してラッパー内で検索可能にする
        Teleport: { template: '<div><slot /></div>' },
        LoadingSpinner: {
          template: '<div data-testid="loading-spinner">{{ label }}</div>',
          props: ['label'],
        },
        ErrorState: {
          template:
            '<div data-testid="error-state"><button type="button" @click="$emit(\'retry\')">재시도</button></div>',
          emits: ['retry'],
        },
        StatusBadge: {
          template: '<span data-testid="status-badge" :data-type="type">{{ label }}</span>',
          props: ['type', 'label'],
        },
        RepairRequestModal: {
          template:
            '<div data-testid="request-modal">' +
            '<button data-testid="modal-close" @click="$emit(\'close\')">닫기</button>' +
            '<button data-testid="modal-confirm" @click="$emit(\'confirm\', null)">확인</button>' +
            '</div>',
          props: ['detail', 'imageBlobUrls', 'imagesLoading', 'readonly', 'submitting'],
          emits: ['close', 'confirm'],
        },
        RepairCompletionModal: {
          template:
            '<div data-testid="completion-modal">' +
            '<button data-testid="completion-close" @click="$emit(\'close\')">닫기</button>' +
            '<button data-testid="completion-confirm" @click="$emit(\'confirm\', \'2026-08-01\')">확인</button>' +
            '</div>',
          props: ['submitting'],
          emits: ['close', 'confirm'],
        },
      },
    },
  })
}

// ── 테스트 ───────────────────────────────────────────────────

describe('RepairDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockClipboard.writeText.mockResolvedValue(undefined)
  })

  // ── 로딩/에러 상태 ────────────────────────────────────────

  it('로딩 중 스피너를 표시한다', async () => {
    mockDamagesApi.getDetail.mockReturnValue(new Promise(() => {}))

    const wrapper = await mountView()
    expect(wrapper.find('[data-testid="loading-spinner"]').exists()).toBe(true)
  })

  it('getDetail 실패 시 에러 상태를 표시한다', async () => {
    mockDamagesApi.getDetail.mockRejectedValue(new Error('network'))

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.find('[data-testid="error-state"]').exists()).toBe(true)
  })

  // ── REQUESTED 상태 ────────────────────────────────────────

  it('REQUESTED 상태에서 보수 요청 버튼을 표시한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('보수 요청')
  })

  it('REQUESTED 상태에서 요청 정보 복사 버튼을 표시한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('요청 정보 복사')
  })

  it('REQUESTED 상태에서 보수 완료 버튼을 표시하지 않는다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.text()).not.toContain('보수 완료')
    expect(wrapper.text()).not.toContain('요청 취소')
  })

  it('REQUESTED 상태에서 보수 요청 클릭 시 요청서 모달을 연다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    const requestBtn = wrapper.findAll('button').find((b) => b.text().includes('보수 요청'))
    await requestBtn!.trigger('click')

    expect(wrapper.find('[data-testid="request-modal"]').exists()).toBe(true)
  })

  it('요청서 모달에서 닫기 클릭 시 모달이 닫힌다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    const requestBtn = wrapper.findAll('button').find((b) => b.text().includes('보수 요청'))
    await requestBtn!.trigger('click')
    expect(wrapper.find('[data-testid="request-modal"]').exists()).toBe(true)

    await wrapper.find('[data-testid="modal-close"]').trigger('click')
    expect(wrapper.find('[data-testid="request-modal"]').exists()).toBe(false)
  })

  it('요청서 모달에서 확인 클릭 시 2차 확인 다이얼로그가 열린다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    const requestBtn = wrapper.findAll('button').find((b) => b.text().includes('보수 요청'))
    await requestBtn!.trigger('click')
    await wrapper.find('[data-testid="modal-confirm"]').trigger('click')

    expect(wrapper.find('[data-testid="request-modal"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('해당 사건을 보수 요청 처리하시겠습니까?')
  })

  it('2차 확인 취소 시 다이얼로그가 닫힌다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    const requestBtn = wrapper.findAll('button').find((b) => b.text().includes('보수 요청'))
    await requestBtn!.trigger('click')
    await wrapper.find('[data-testid="modal-confirm"]').trigger('click')

    // 2차 확인 다이얼로그의 취소 버튼
    const allBtns = wrapper.findAll('button')
    const cancelBtn = allBtns.find((b) => b.text() === '취소')
    await cancelBtn!.trigger('click')

    expect(wrapper.text()).not.toContain('해당 사건을 보수 요청 처리하시겠습니까?')
  })

  it('2차 확인에서 확인 클릭 시 repairsApi.submitRequest를 호출한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)
    mockRepairsApi.submitRequest.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    const requestBtn = wrapper.findAll('button').find((b) => b.text().includes('보수 요청'))
    await requestBtn!.trigger('click')
    await wrapper.find('[data-testid="modal-confirm"]').trigger('click')

    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === '확인')
    await confirmBtn!.trigger('click')
    await flushPromises()

    expect(mockRepairsApi.submitRequest).toHaveBeenCalledWith(6, { note: null })
  })

  it('요청 성공 시 상태가 REPAIR_IN_PROGRESS로 갱신된다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)
    mockRepairsApi.submitRequest.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    const requestBtn = wrapper.findAll('button').find((b) => b.text().includes('보수 요청'))
    await requestBtn!.trigger('click')
    await wrapper.find('[data-testid="modal-confirm"]').trigger('click')

    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === '확인')
    await confirmBtn!.trigger('click')
    await flushPromises()

    const badges = wrapper.findAll('[data-testid="status-badge"]')
    expect(badges.some((b) => b.text() === '요청 완료')).toBe(true)
  })

  it('요청 실패 시 기존 REQUESTED 상태를 유지한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)
    mockRepairsApi.submitRequest.mockRejectedValue(new Error('404'))

    const wrapper = await mountView()
    await flushPromises()

    const requestBtn = wrapper.findAll('button').find((b) => b.text().includes('보수 요청'))
    await requestBtn!.trigger('click')
    await wrapper.find('[data-testid="modal-confirm"]').trigger('click')

    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === '확인')
    await confirmBtn!.trigger('click')
    await flushPromises()

    const badges = wrapper.findAll('[data-testid="status-badge"]')
    expect(badges.some((b) => b.text() === '요청 전')).toBe(true)
  })

  // ── 요청 정보 복사 ────────────────────────────────────────

  it('요청 정보 복사 버튼 클릭 시 navigator.clipboard.writeText를 호출한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    const copyBtn = wrapper.findAll('button').find((b) => b.text().includes('요청 정보 복사'))
    await copyBtn!.trigger('click')
    await flushPromises()

    expect(mockClipboard.writeText).toHaveBeenCalledOnce()
    const copied = mockClipboard.writeText.mock.calls[0]![0] as string
    expect(copied).toContain('[Roady 보수 요청]')
    expect(copied).toContain('RD-2026-000006')
    expect(copied).toContain('개포로 점자블록 침하 탐지')
  })

  it('복사 성공 시 버튼 텍스트가 "복사 완료"로 바뀐다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)
    mockClipboard.writeText.mockResolvedValue(undefined)

    const wrapper = await mountView()
    await flushPromises()

    const copyBtn = wrapper.findAll('button').find((b) => b.text().includes('요청 정보 복사'))
    await copyBtn!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('복사 완료')
  })

  it('복사 실패 시 버튼 텍스트가 변경되지 않는다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)
    mockClipboard.writeText.mockRejectedValue(new Error('permission denied'))

    const wrapper = await mountView()
    await flushPromises()

    const copyBtn = wrapper.findAll('button').find((b) => b.text().includes('요청 정보 복사'))
    await copyBtn!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).not.toContain('복사 완료')
    expect(wrapper.text()).toContain('요청 정보 복사')
  })

  // ── REPAIR_IN_PROGRESS 상태 ───────────────────────────────

  it('REPAIR_IN_PROGRESS 상태에서 보수 요청 버튼을 표시하지 않는다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.text()).not.toContain('보수 요청외부')
    expect(wrapper.findAll('button').find((b) => b.text() === '보수 요청')).toBeUndefined()
  })

  it('REPAIR_IN_PROGRESS 상태에서 요청서 확인, 요청서 내용 수정, 요청 취소, 보수 완료 버튼을 표시한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('요청서 확인')
    expect(text).toContain('요청서 내용 수정')
    expect(text).toContain('요청 취소')
    expect(text).toContain('보수 완료')
  })

  it('보수 완료 버튼 클릭 시 완료 모달을 연다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    const completeBtn = wrapper.findAll('button').find((b) => b.text() === '보수 완료')
    await completeBtn!.trigger('click')

    expect(wrapper.find('[data-testid="completion-modal"]').exists()).toBe(true)
  })

  it('보수 완료 확인 시 repairsApi.completeRepair를 호출한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)
    mockRepairsApi.completeRepair.mockResolvedValue(detailCompleted)

    const wrapper = await mountView()
    await flushPromises()

    const completeBtn = wrapper.findAll('button').find((b) => b.text() === '보수 완료')
    await completeBtn!.trigger('click')
    await wrapper.find('[data-testid="completion-confirm"]').trigger('click')
    await flushPromises()

    expect(mockRepairsApi.completeRepair).toHaveBeenCalledWith(6, { completedAt: '2026-08-01' })
  })

  it('보수 완료 성공 시 상태가 REPAIR_COMPLETED로 갱신된다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)
    mockRepairsApi.completeRepair.mockResolvedValue(detailCompleted)

    const wrapper = await mountView()
    await flushPromises()

    const completeBtn = wrapper.findAll('button').find((b) => b.text() === '보수 완료')
    await completeBtn!.trigger('click')
    await wrapper.find('[data-testid="completion-confirm"]').trigger('click')
    await flushPromises()

    const badges = wrapper.findAll('[data-testid="status-badge"]')
    expect(badges.some((b) => b.text() === '보수 완료')).toBe(true)
  })

  it('보수 완료 실패 시 기존 REPAIR_IN_PROGRESS 상태를 유지한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)
    mockRepairsApi.completeRepair.mockRejectedValue(new Error('500'))

    const wrapper = await mountView()
    await flushPromises()

    const completeBtn = wrapper.findAll('button').find((b) => b.text() === '보수 완료')
    await completeBtn!.trigger('click')
    await wrapper.find('[data-testid="completion-confirm"]').trigger('click')
    await flushPromises()

    const badges = wrapper.findAll('[data-testid="status-badge"]')
    expect(badges.some((b) => b.text() === '요청 완료')).toBe(true)
  })

  // ── 요청 취소 ─────────────────────────────────────────────

  it('요청 취소 버튼 클릭 시 취소 확인 다이얼로그를 연다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    const cancelBtn = wrapper.findAll('button').find((b) => b.text() === '요청 취소')
    await cancelBtn!.trigger('click')

    expect(wrapper.text()).toContain('보수 요청을 취소하시겠습니까?')
  })

  it('취소 확인 시 repairsApi.cancelRequest를 호출한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)
    mockRepairsApi.cancelRequest.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    const cancelBtn = wrapper.findAll('button').find((b) => b.text() === '요청 취소')
    await cancelBtn!.trigger('click')

    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === '확인')
    await confirmBtn!.trigger('click')
    await flushPromises()

    expect(mockRepairsApi.cancelRequest).toHaveBeenCalledWith(6)
  })

  it('취소 성공 시 REQUESTED 상태로 되돌아가 보수 요청 버튼이 표시된다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)
    mockRepairsApi.cancelRequest.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    const cancelBtn = wrapper.findAll('button').find((b) => b.text() === '요청 취소')
    await cancelBtn!.trigger('click')

    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === '확인')
    await confirmBtn!.trigger('click')
    await flushPromises()

    expect(wrapper.findAll('button').find((b) => b.text().includes('보수 요청'))).toBeDefined()
  })

  // ── REPAIR_COMPLETED 상태 ─────────────────────────────────

  it('REPAIR_COMPLETED 상태에서 보수 요청·완료·취소 버튼을 표시하지 않는다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailCompleted)

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.findAll('button').find((b) => b.text() === '보수 요청')).toBeUndefined()
    expect(wrapper.findAll('button').find((b) => b.text() === '보수 완료')).toBeUndefined()
    expect(wrapper.findAll('button').find((b) => b.text() === '요청 취소')).toBeUndefined()
  })

  it('REPAIR_COMPLETED 상태에서 요청서 확인 버튼을 표시한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailCompleted)

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('요청서 확인')
  })

  it('요청서 확인 버튼 클릭 시 요청서 모달을 연다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailCompleted)

    const wrapper = await mountView()
    await flushPromises()

    const viewBtn = wrapper.findAll('button').find((b) => b.text() === '요청서 확인')
    await viewBtn!.trigger('click')

    expect(wrapper.find('[data-testid="request-modal"]').exists()).toBe(true)
  })
})
