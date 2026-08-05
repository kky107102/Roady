import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import type { DamageListItem } from '@/types/damage'
import UrgentDamageList from '@/components/damages/UrgentDamageList.vue'

const urgentDamage: DamageListItem = {
  id: 15,
  robotId: 1,
  assignedTo: null,
  description: '긴급 포트홀',
  latitude: 37.5,
  longitude: 127,
  capturedAt: '2026-08-05T09:00:00',
  currentStatus: 'AI_ANALYZED',
  imageCount: 1,
  damageScore: 95,
  repairRequired: true,
  repairPriority: 'URGENT',
  confidenceScore: 0.99,
  createdAt: '2026-08-05T09:00:00',
}

describe('UrgentDamageList', () => {
  it('긴급 미확인 사건과 우선순위 정렬 목록으로 연결한다', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', name: 'dashboard', component: { template: '<div />' } },
        { path: '/damages', name: 'damages', component: { template: '<div />' } },
      ],
    })
    await router.push('/')

    const wrapper = mount(UrgentDamageList, {
      props: { items: [urgentDamage] },
      global: {
        plugins: [router],
        stubs: {
          StatusBadge: { template: '<span>{{ label }}</span>', props: ['label'] },
          EmptyState: { template: '<span>{{ title }}</span>', props: ['title'] },
        },
      },
    })

    expect(wrapper.get('a[aria-label="긴급 사건 15 상세보기"]').attributes('href')).toBe(
      '/damages?review=pending&sort=priority&damageId=15',
    )
    expect(wrapper.get('.udl-view-all').attributes('href')).toBe(
      '/damages?review=pending&sort=priority',
    )
    expect(wrapper.text()).toContain('긴급')
    expect(wrapper.text()).not.toContain('AI 판독')
    expect(wrapper.text()).not.toContain('#15')
  })
})
