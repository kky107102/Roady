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
      },
    },
  })
}

describe('DamageCard', () => {
  it('미확인 사건은 주소와 AI 제안 우선순위를 표시한다', () => {
    const wrapper = mountCard(baseItem)

    expect(wrapper.text()).toContain('서울특별시 강남구 테헤란로 123 주변')
    expect(wrapper.text()).toContain('AI 제안 · 긴급')
    expect(wrapper.text()).not.toContain('확인 완료')
  })

  it('관리자 확인 사건은 카드 우하단에 확인 완료를 표시한다', () => {
    const wrapper = mountCard({
      ...baseItem,
      currentStatus: 'REQUESTED',
      repairPriority: 'NORMAL',
    })

    expect(wrapper.text()).toContain('보통')
    expect(wrapper.text()).toContain('확인 완료')
    expect(wrapper.text()).not.toContain('AI 제안 ·')
  })
})
