import { describe, it, expect, vi, beforeEach, beforeAll, afterAll } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia } from 'pinia'
import type { DamageDetail } from '@/types/damage'
import type { UserSummary } from '@/types/auth'
import type {
  RepairCompletePayload,
  RepairRequestPayload,
  RepairTransitionResult,
} from '@/types/repair'

// ── API mock ─────────────────────────────────────────────────

const mockDamagesApi = vi.hoisted(() => ({
  getDetail: vi.fn<(id: number) => Promise<DamageDetail>>(),
  getImageContent: vi.fn<(damageId: number, imageId: number) => Promise<Blob>>(),
  clearDetailCache: vi.fn<(id?: number) => void>(),
  updateReview: vi.fn<() => Promise<void>>(),
}))

const mockRepairsApi = vi.hoisted(() => ({
  submitRequest:
    vi.fn<(id: number, payload?: RepairRequestPayload) => Promise<RepairTransitionResult>>(),
  cancelRequest:
    vi.fn<(id: number, payload?: RepairRequestPayload) => Promise<RepairTransitionResult>>(),
  updateRequest:
    vi.fn<(id: number, payload: RepairRequestPayload) => Promise<RepairTransitionResult>>(),
  completeRepair:
    vi.fn<(id: number, payload?: RepairCompletePayload) => Promise<RepairTransitionResult>>(),
}))

const mockUsersApi = vi.hoisted(() => ({ list: vi.fn<() => Promise<UserSummary[]>>() }))

vi.mock('@/api/damages', () => ({ damagesApi: mockDamagesApi }))
vi.mock('@/api/repairs', () => ({ repairsApi: mockRepairsApi }))
vi.mock('@/api/users', () => ({ usersApi: mockUsersApi }))

// ── navigator.clipboard mock ──────────────────────────────────

const mockClipboard = { writeText: vi.fn<(text: string) => Promise<void>>() }

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
const detailCanceled: DamageDetail = { ...baseDetail, currentStatus: 'CANCELED' }

// ── 마운트 헬퍼 ──────────────────────────────────────────────

async function mountView(damageId = 6, query: Record<string, string> = {}) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/repairs/:damageId', name: 'repair-detail', component: RepairDetailView },
      { path: '/repairs', name: 'repairs', component: { template: '<div />' } },
    ],
  })
  await router.push({ name: 'repair-detail', params: { damageId }, query })

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
            '<button v-if="editing" data-testid="modal-cancel-edit" @click="$emit(\'cancelEdit\')">취소</button>' +
            "<button v-if=\"!readonly\" data-testid=\"modal-confirm\" @click=\"$emit('confirm', { note: null, processingPriority: 'URGENT', reviewDamageType: 'CRACK', repairerId: null })\">{{ editing ? '저장' : '보수 요청하기' }}</button>" +
            "<button v-if=\"readonly\" data-testid=\"modal-copy\" @click=\"$emit('copy')\">{{ copyState === 'success' ? '복사 완료' : '요청 복사' }}</button>" +
            '<button v-if="readonly && editable" data-testid="modal-edit" @click="$emit(\'edit\')">수정하기</button>' +
            '</div>',
          props: [
            'detail',
            'imageBlobUrls',
            'imagesLoading',
            'readonly',
            'editing',
            'submitting',
            'officialName',
            'repairers',
            'copyState',
            'editable',
          ],
          emits: ['close', 'cancelEdit', 'confirm', 'copy', 'edit'],
        },
        RepairCompletionModal: {
          template:
            '<div data-testid="completion-modal">' +
            '<button data-testid="completion-close" @click="$emit(\'close\')">닫기</button>' +
            "<button v-if=\"readonly\" data-testid=\"completion-copy\" @click=\"$emit('copy')\">{{ copyState === 'success' ? '복사 완료' : '내용 복사' }}</button>" +
            "<button data-testid=\"completion-confirm\" @click=\"$emit('confirm', { completedAt: '2026-08-01', note: '완료 처리' })\">확인</button>" +
            '</div>',
          props: [
            'submitting',
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
          emits: ['close', 'confirm', 'copy'],
        },
      },
    },
  })
}

// ── 테스트 ───────────────────────────────────────────────────

describe('RepairDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUsersApi.list.mockResolvedValue([])
    mockDamagesApi.updateReview.mockResolvedValue(undefined)
    mockClipboard.writeText.mockResolvedValue(undefined)
  })

  // ── 로딩/에러 상태 ────────────────────────────────────────

  it('중복 본문 제목 없이 사건 목록 이동 링크를 표시한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.get('[aria-label="사건 목록으로 돌아가기"]').text()).toContain('사건 목록')
    expect(wrapper.find('.page-title').exists()).toBe(false)
  })

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
    expect(wrapper.findAll('.action-section .filled.primary')).toHaveLength(1)
  })

  it('REQUESTED 상태에서는 최종 요청 정보 복사 버튼을 표시하지 않는다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.text()).not.toContain('요청 복사')
  })

  it('REQUESTED 상태에서 보수 불필요 처리 버튼을 표시하고 판정 API를 호출한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    const noRepairBtn = wrapper.findAll('button').find((b) => b.text() === '보수 불필요 처리')
    await noRepairBtn!.trigger('click')
    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === '확인')
    await confirmBtn!.trigger('click')
    await flushPromises()

    expect(mockDamagesApi.updateReview).toHaveBeenCalledWith(6, 'CANCELED')
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

  it('요청서 작성 바로가기 쿼리로 진입하면 해당 사건의 요청서 모달을 연다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)

    const wrapper = await mountView(6, { action: 'create-request' })
    await flushPromises()

    expect(wrapper.find('[data-testid="request-modal"]').exists()).toBe(true)
  })

  it('요청서 확인 쿼리로 진입하면 요청서 조회 모달을 연다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)

    const wrapper = await mountView(6, { action: 'view-request' })
    await flushPromises()

    expect(wrapper.get('[data-testid="request-modal"]').text()).toContain('요청 복사')
  })

  it('보고서 확인 쿼리로 진입하면 완료 보고서 모달을 연다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailCompleted)

    const wrapper = await mountView(6, { action: 'view-completion-report' })
    await flushPromises()

    expect(wrapper.get('[data-testid="completion-modal"]').text()).toContain('내용 복사')
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

    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === '요청 전송')
    await confirmBtn!.trigger('click')
    await flushPromises()

    expect(mockRepairsApi.submitRequest).toHaveBeenCalledWith(6, {
      note: null,
      processingPriority: 'URGENT',
      reviewDamageType: 'CRACK',
      repairerId: null,
    })
    expect(mockDamagesApi.updateReview).not.toHaveBeenCalled()
  })

  it('요청 성공 시 상태가 REPAIR_IN_PROGRESS로 갱신된다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(baseDetail)
    mockRepairsApi.submitRequest.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    const requestBtn = wrapper.findAll('button').find((b) => b.text().includes('보수 요청'))
    await requestBtn!.trigger('click')
    await wrapper.find('[data-testid="modal-confirm"]').trigger('click')

    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === '요청 전송')
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

    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === '요청 전송')
    await confirmBtn!.trigger('click')
    await flushPromises()

    const badges = wrapper.findAll('[data-testid="status-badge"]')
    expect(badges.some((b) => b.text() === '요청 전')).toBe(true)
  })

  // ── 요청 정보 복사 ────────────────────────────────────────

  it('요청 정보 복사 버튼 클릭 시 navigator.clipboard.writeText를 호출한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    const viewButton = wrapper.findAll('button').find((b) => b.text() === '요청서 확인')
    await viewButton!.trigger('click')
    await wrapper.get('[data-testid="modal-copy"]').trigger('click')
    await flushPromises()

    expect(mockClipboard.writeText).toHaveBeenCalledOnce()
    const copied = mockClipboard.writeText.mock.calls[0]![0] as string
    expect(copied).toContain('[Roady 보수 요청]')
    expect(copied).toContain('RD-2026-000006')
    expect(copied).toContain('개포로 점자블록 침하 탐지')
  })

  it('복사 성공 시 버튼 텍스트가 "복사 완료"로 바뀐다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)
    mockClipboard.writeText.mockResolvedValue(undefined)

    const wrapper = await mountView()
    await flushPromises()

    const viewButton = wrapper.findAll('button').find((b) => b.text() === '요청서 확인')
    await viewButton!.trigger('click')
    await wrapper.get('[data-testid="modal-copy"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('복사 완료')
  })

  it('복사 실패 시 버튼 텍스트가 변경되지 않는다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)
    mockClipboard.writeText.mockRejectedValue(new Error('permission denied'))

    const wrapper = await mountView()
    await flushPromises()

    const viewButton = wrapper.findAll('button').find((b) => b.text() === '요청서 확인')
    await viewButton!.trigger('click')
    await wrapper.get('[data-testid="modal-copy"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).not.toContain('복사 완료')
    expect(wrapper.text()).toContain('요청 복사')
  })

  // ── REPAIR_IN_PROGRESS 상태 ───────────────────────────────

  it('REPAIR_IN_PROGRESS 상태에서 보수 요청 버튼을 표시하지 않는다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.text()).not.toContain('보수 요청외부')
    expect(wrapper.findAll('button').find((b) => b.text() === '보수 요청')).toBeUndefined()
    expect(wrapper.findAll('.action-section .filled.primary')).toHaveLength(1)
  })

  it('REPAIR_IN_PROGRESS 상태에서 요청서 확인, 요청 취소, 보수 완료 버튼을 표시한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('요청서 확인')
    expect(text).not.toContain('요청서 내용 수정')
    expect(text).toContain('요청 취소')
    expect(text).toContain('보수 완료')
  })

  it('요청서 저장 시 수정 API를 호출하고 갱신된 확인 모달로 돌아온다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)
    mockRepairsApi.updateRequest.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    const viewBtn = wrapper.findAll('button').find((b) => b.text() === '요청서 확인')
    await viewBtn!.trigger('click')
    await wrapper.find('[data-testid="modal-edit"]').trigger('click')
    await wrapper.find('[data-testid="modal-confirm"]').trigger('click')
    await flushPromises()

    expect(mockRepairsApi.updateRequest).toHaveBeenCalledWith(6, {
      note: null,
      processingPriority: 'URGENT',
      reviewDamageType: 'CRACK',
      repairerId: null,
    })
    expect(wrapper.find('[data-testid="modal-edit"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="modal-copy"]').exists()).toBe(true)
  })

  it('요청서 수정 취소 시 저장하지 않고 요청서 확인 모달로 돌아온다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)

    const wrapper = await mountView()
    await flushPromises()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '요청서 확인')!
      .trigger('click')
    await wrapper.find('[data-testid="modal-edit"]').trigger('click')
    await wrapper.find('[data-testid="modal-cancel-edit"]').trigger('click')

    expect(mockRepairsApi.updateRequest).not.toHaveBeenCalled()
    expect(wrapper.find('[data-testid="modal-edit"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="modal-copy"]').exists()).toBe(true)
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

    expect(mockRepairsApi.completeRepair).toHaveBeenCalledWith(6, {
      completedAt: '2026-08-01',
      note: '완료 처리',
    })
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
    mockRepairsApi.cancelRequest.mockResolvedValue(detailCanceled)

    const wrapper = await mountView()
    await flushPromises()

    const cancelBtn = wrapper.findAll('button').find((b) => b.text() === '요청 취소')
    await cancelBtn!.trigger('click')

    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === '확인')
    await confirmBtn!.trigger('click')
    await flushPromises()

    expect(mockRepairsApi.cancelRequest).toHaveBeenCalledWith(6, { note: null })
  })

  it('취소 성공 시 REQUESTED 상태로 복귀하고 보수 요청 버튼을 표시한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue(detailInProgress)
    mockRepairsApi.cancelRequest.mockResolvedValue(baseDetail)

    const wrapper = await mountView()
    await flushPromises()

    const cancelBtn = wrapper.findAll('button').find((b) => b.text() === '요청 취소')
    await cancelBtn!.trigger('click')

    const confirmBtn = wrapper.findAll('button').find((b) => b.text() === '확인')
    await confirmBtn!.trigger('click')
    await flushPromises()

    const badges = wrapper.findAll('[data-testid="status-badge"]')
    expect(badges.some((b) => b.text() === '요청 전')).toBe(true)
    expect(wrapper.findAll('button').find((b) => b.text() === '보수 요청')).toBeDefined()
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

  it('완료 보고서 내용을 클립보드에 복사한다', async () => {
    mockDamagesApi.getDetail.mockResolvedValue({
      ...detailCompleted,
      assignedToName: '박주무관',
      repairerName: '김보수',
      repairRequestedAt: '2026-08-04T14:30:00',
      repairCompletedAt: '2026-08-05',
      repairCompletionNote: '점자블록 교체 완료',
    })
    mockClipboard.writeText.mockResolvedValue(undefined)

    const wrapper = await mountView()
    await flushPromises()
    await wrapper
      .findAll('button')
      .find((button) => button.text() === '완료 보고서 확인')!
      .trigger('click')
    await wrapper.get('[data-testid="completion-copy"]').trigger('click')
    await flushPromises()

    const calls = mockClipboard.writeText.mock.calls
    const copied = calls[calls.length - 1]?.[0] ?? ''
    expect(copied).toContain('[Roady 보수 완료 보고서]')
    expect(copied).toContain('담당 주무관: 박주무관')
    expect(copied).toContain('보수 담당자: 김보수')
    expect(copied).toContain('보수 완료 사진: 이미지 없음')
    expect(copied).toContain('완료 메모: 점자블록 교체 완료')
    expect(wrapper.text()).toContain('복사 완료')
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
