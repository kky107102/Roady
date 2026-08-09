import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DamageCard from '@/components/damages/DamageCard.vue'
import type { DamageListItem } from '@/types/damage'

const baseItem: DamageListItem = {
  id: 426,
  robotId: 4,
  assignedTo: null,
  description: '점자블록 균열 및 들뜸',
  addressName: null,
  roadAddressName: '서울특별시 강남구 테헤란로 123',
  latitude: 37.5665,
  longitude: 126.978,
  capturedAt: '2026-07-31T13:08:00',
  currentStatus: 'AI_ANALYZED',
  imageCount: 2,
  damageScore: 38,
  repairRequired: true,
  repairPriority: 'URGENT',
  confidenceScore: 0.94,
  createdAt: '2026-07-31T13:08:00',
}

function mountCard(item: DamageListItem) {
  return mount(DamageCard, {
    props: { item },
    global: {
      stubs: {
        DamageThumbnail: {
          template: '<div data-testid="thumbnail" />',
        },
        StatusBadge: {
          template: '<span data-testid="status-badge">{{ label }}</span>',
          props: ['type', 'label'],
        },
        AiResultBadge: {
          template:
            '<span data-testid="ai-result-badge"><span>AI 판독</span><span>{{ label }}</span></span>',
          props: ['type', 'label'],
        },
      },
    },
  })
}

describe('DamageCard', () => {
  it('미확인 사건은 AI 출처와 우선순위를 분리한 태그로 표시한다', () => {
    const wrapper = mountCard(baseItem)

    expect(wrapper.text()).toContain('서울특별시 강남구 테헤란로 123 주변')
    expect(wrapper.get('[data-testid="ai-result-badge"]').text()).toContain('AI 판독')
    expect(wrapper.get('[data-testid="ai-result-badge"]').text()).toContain('긴급')
    expect(wrapper.text()).not.toContain('AI 제안 ·')
    expect(wrapper.text()).not.toContain('확인 완료')
  })

  it('관리자 확인 사건은 카드 우하단에 실제 처리 상태를 표시한다', () => {
    const wrapper = mountCard({
      ...baseItem,
      currentStatus: 'CANCELED',
      processingPriority: 'NORMAL',
      repairPriority: 'NORMAL',
    })

    expect(wrapper.text()).toContain('보통')
    expect(wrapper.text()).toContain('보수 불필요')
    expect(wrapper.text()).not.toContain('확인 완료')
    expect(wrapper.text()).not.toContain('AI 제안 ·')
  })

  it('요청 전·요청 완료·보수 완료 상태를 구분해 표시한다', () => {
    expect(mountCard({ ...baseItem, currentStatus: 'REQUESTED' }).text()).toContain('요청 전')
    expect(mountCard({ ...baseItem, currentStatus: 'REPAIR_IN_PROGRESS' }).text()).toContain(
      '요청 완료',
    )
    expect(mountCard({ ...baseItem, currentStatus: 'REPAIR_COMPLETED' }).text()).toContain(
      '보수 완료',
    )
  })

  it('관리자 우선순위가 없는 확인 사건은 AI 값 대신 미지정으로 표시한다', () => {
    const wrapper = mountCard({
      ...baseItem,
      currentStatus: 'REQUESTED',
      processingPriority: null,
    })

    expect(wrapper.get('[data-testid="status-badge"]').text()).toBe('미지정')
  })
})
