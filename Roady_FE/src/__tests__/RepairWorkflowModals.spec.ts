import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import RepairRequestModal from '@/components/repairs/RepairRequestModal.vue'
import RepairCompletionModal from '@/components/repairs/RepairCompletionModal.vue'
import type { DamageDetail } from '@/types/damage'
import type { UserSummary } from '@/types/auth'

const detail: DamageDetail = {
  id: 6,
  robotId: 1,
  reportedBy: null,
  assignedTo: 2,
  description: '점자블록 파손',
  addressName: '서울특별시 강남구',
  latitude: 37.5,
  longitude: 127,
  capturedAt: '2026-08-01T10:00:00',
  currentStatus: 'REQUESTED',
  processingPriority: 'HIGH',
  reviewDamageType: 'CRACK',
  reviewNote: null,
  imageCount: 0,
  images: [],
  createdAt: '2026-08-01T10:00:00',
  updatedAt: '2026-08-01T10:00:00',
}

const repairer: UserSummary = {
  id: 9,
  username: 'repairer',
  email: 'repairer@example.com',
  name: '김보수',
  assignedRegionCode: null,
  role: 'REPAIRER',
  active: true,
  createdAt: '2026-08-01T10:00:00',
}

const global = {
  stubs: {
    Teleport: { template: '<div><slot /></div>' },
    LoadingSpinner: { template: '<div />' },
    StatusBadge: { template: '<span>{{ label }}</span>', props: ['label'] },
  },
}

describe('RepairRequestModal', () => {
  it('작성·수정 모드에서 우선순위, 파손 유형, 보수 담당자를 선택한다', async () => {
    const wrapper = mount(RepairRequestModal, {
      props: {
        detail,
        imageBlobUrls: new Map(),
        officialName: '박주무관',
        repairers: [repairer],
      },
      global,
    })

    const selects = wrapper.findAll('select')
    expect(selects).toHaveLength(3)
    await selects[0]!.setValue('9')
    await selects[1]!.setValue('URGENT')
    await selects[2]!.setValue('WEAR')
    await wrapper.find('textarea').setValue('교체 요청')
    await wrapper
      .findAll('button')
      .find((button) => button.text() === '보수 요청하기')!
      .trigger('click')

    expect(wrapper.emitted('confirm')?.[0]?.[0]).toEqual({
      note: '교체 요청',
      processingPriority: 'URGENT',
      reviewDamageType: 'WEAR',
      repairerId: 9,
    })
  })

  it('확인 모드에서는 선택 필드를 표시하지 않는다', () => {
    const wrapper = mount(RepairRequestModal, {
      props: {
        detail: { ...detail, repairerId: 9, repairerName: '김보수' },
        imageBlobUrls: new Map(),
        readonly: true,
        officialName: '박주무관',
        repairers: [repairer],
      },
      global,
    })

    expect(wrapper.findAll('select')).toHaveLength(0)
    expect(wrapper.text()).toContain('박주무관')
    expect(wrapper.text()).toContain('김보수')
  })

  it('확인 모드에서만 최종 요청 정보 복사 버튼을 제공한다', async () => {
    const wrapper = mount(RepairRequestModal, {
      props: {
        detail: { ...detail, repairerId: 9, repairerName: '김보수' },
        imageBlobUrls: new Map(),
        readonly: true,
        copyState: 'idle',
      },
      global,
    })

    const copyButton = wrapper.findAll('button').find((button) => button.text() === '요청 복사')
    expect(copyButton).toBeDefined()
    expect(copyButton!.find('svg').exists()).toBe(true)
    expect(copyButton!.classes()).toContain('primary')
    await copyButton!.trigger('click')

    expect(wrapper.emitted('copy')).toHaveLength(1)
  })

  it('수정 가능한 확인 모드에서 수정하기 버튼을 제공한다', async () => {
    const wrapper = mount(RepairRequestModal, {
      props: {
        detail: { ...detail, repairerId: 9, repairerName: '김보수' },
        imageBlobUrls: new Map(),
        readonly: true,
        editable: true,
      },
      global,
    })

    const editButton = wrapper.findAll('button').find((button) => button.text() === '수정하기')
    expect(editButton).toBeDefined()
    await editButton!.trigger('click')

    expect(wrapper.emitted('edit')).toHaveLength(1)
    const headerButtons = wrapper.find('.modal-header-actions').findAll('button')
    expect(headerButtons[0]!.text()).toBe('수정하기')
    expect(headerButtons[1]!.attributes('aria-label')).toBe('닫기')
    expect(wrapper.find('.modal-footer').text()).toContain('닫기')
    expect(wrapper.find('.modal-footer').text()).toContain('요청 복사')
    expect(wrapper.find('.modal-footer .modal-dismiss-btn').text()).toBe('닫기')
  })

  it('수정 모드의 하단 버튼을 취소와 저장으로 구성한다', async () => {
    const wrapper = mount(RepairRequestModal, {
      props: {
        detail: { ...detail, repairerId: 9, repairerName: '김보수' },
        imageBlobUrls: new Map(),
        editing: true,
      },
      global,
    })

    const footerButtons = wrapper.find('.modal-footer').findAll('button')
    expect(footerButtons.map((button) => button.text())).toEqual(['취소', '저장'])
    expect(footerButtons[0]!.classes()).toContain('modal-dismiss-btn')
    expect(footerButtons[1]!.classes()).toContain('primary')
    await footerButtons[0]!.trigger('click')

    expect(wrapper.emitted('cancelEdit')).toHaveLength(1)
  })
})

describe('RepairCompletionModal', () => {
  it('완료 일자를 필수로 검사하고 완료 일자와 메모를 제출한다', async () => {
    const wrapper = mount(RepairCompletionModal, { global })

    await wrapper.find('input[type="date"]').setValue('')
    await wrapper
      .findAll('button')
      .find((button) => button.text() === '다음')!
      .trigger('click')
    expect(wrapper.text()).toContain('보수 완료 일자를 입력해 주세요.')

    await wrapper.find('input[type="date"]').setValue('2026-08-01')
    await wrapper.find('textarea').setValue('교체 완료')
    await wrapper
      .findAll('button')
      .find((button) => button.text() === '다음')!
      .trigger('click')
    await wrapper
      .findAll('button')
      .find((button) => button.text() === '확인')!
      .trigger('click')

    expect(wrapper.emitted('confirm')?.[0]?.[0]).toEqual({
      completedAt: '2026-08-01',
      note: '교체 완료',
    })
  })

  it('완료 보고서 확인 모드에서는 저장된 내용을 읽기 전용으로 표시한다', () => {
    const wrapper = mount(RepairCompletionModal, {
      props: { readonly: true, completedAt: '2026-08-01', note: '교체 완료' },
      global,
    })

    expect(wrapper.text()).toContain('완료 보고서 확인')
    expect(wrapper.text()).toContain('2026-08-01')
    expect(wrapper.text()).toContain('교체 완료')
    expect(wrapper.find('input').exists()).toBe(false)
  })
})
