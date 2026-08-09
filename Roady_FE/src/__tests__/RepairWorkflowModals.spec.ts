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
  it('문서 내용을 모달 제목 아래의 상위 섹션으로 구분한다', () => {
    const wrapper = mount(RepairRequestModal, {
      props: { detail, imageBlobUrls: new Map(), readonly: true },
      global,
    })

    expect(wrapper.findAll('h3').map((heading) => heading.text())).toEqual([
      '사건 정보',
      '관리자 판정',
      '탐지 이미지',
      '비고',
    ])
    expect(wrapper.findAll('section[aria-labelledby]')).toHaveLength(4)
  })

  it('신규 작성에서는 과거 요청 비고를 비우고 수정에서는 유지한다', () => {
    const detailWithPreviousNote = { ...detail, repairRequestNote: '이전 요청 비고' }
    const createWrapper = mount(RepairRequestModal, {
      props: {
        detail: detailWithPreviousNote,
        imageBlobUrls: new Map(),
      },
      global,
    })
    const editWrapper = mount(RepairRequestModal, {
      props: {
        detail: detailWithPreviousNote,
        imageBlobUrls: new Map(),
        editing: true,
      },
      global,
    })

    expect(createWrapper.get('textarea').element.value).toBe('')
    expect(editWrapper.get('textarea').element.value).toBe('이전 요청 비고')
  })

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
    expect(copyButton!.classes()).toContain('secondary')
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
    expect(wrapper.find('.modal-footer').text()).toContain('확인')
    expect(wrapper.find('.modal-footer').text()).toContain('요청 복사')
    expect(wrapper.find('.modal-footer .primary').text()).toBe('확인')
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
    expect(footerButtons[0]!.classes()).toContain('secondary')
    expect(footerButtons[1]!.classes()).toContain('primary')
    await footerButtons[0]!.trigger('click')

    expect(wrapper.emitted('cancelEdit')).toHaveLength(1)
  })
})

describe('RepairCompletionModal', () => {
  it('완료 보고서에 담당자, 일자, 보수 전 사진과 완료 사진 빈 상태를 표시한다', () => {
    const beforeImage = {
      id: 31,
      damageId: detail.id,
      sortOrder: 1,
      originalFilename: 'before.jpg',
      contentType: 'image/jpeg',
      sizeBytes: 1024,
      createdAt: '2026-08-01T10:00:00',
    }
    const wrapper = mount(RepairCompletionModal, {
      props: {
        readonly: true,
        officialName: '박주무관',
        repairerName: '김보수',
        requestedAt: '2026-08-02T14:30:00',
        completedAt: '2026-08-05',
        note: '점자블록 교체 완료',
        beforeImages: [beforeImage],
        imageBlobUrls: new Map([[beforeImage.id, 'blob:before-image']]),
      },
      global,
    })

    expect(wrapper.text()).toContain('담당 주무관')
    expect(wrapper.text()).toContain('박주무관')
    expect(wrapper.text()).toContain('보수 담당자')
    expect(wrapper.text()).toContain('김보수')
    expect(wrapper.text()).toContain('보수 요청 일자')
    expect(wrapper.text()).toContain('보수 완료 일자')
    expect(wrapper.text()).toContain('보수 전 사진')
    expect(wrapper.get('img[alt="보수 전 사진 1"]').attributes('src')).toBe('blob:before-image')
    expect(wrapper.text()).toContain('보수 완료 사진')
    expect(wrapper.text()).toContain('보수 완료 이미지가 없습니다.')
    expect(wrapper.text()).toContain('점자블록 교체 완료')
    expect(wrapper.text()).toContain('내용 복사')
    expect(wrapper.findAll('h3').map((heading) => heading.text())).toEqual([
      '담당 정보',
      '처리 일정',
      '보수 전 사진',
      '보수 완료 사진',
      '완료 메모',
    ])
  })

  it('완료 보고서 내용 복사 이벤트를 전달한다', async () => {
    const wrapper = mount(RepairCompletionModal, {
      props: { readonly: true },
      global,
    })

    await wrapper
      .findAll('button')
      .find((button) => button.text() === '내용 복사')!
      .trigger('click')

    expect(wrapper.emitted('copy')).toHaveLength(1)
  })

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
