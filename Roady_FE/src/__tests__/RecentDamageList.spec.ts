import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import type { DamageListItem } from '@/types/damage'

const mockDamagesApi = vi.hoisted(() => ({ list: vi.fn() }))

vi.mock('@/api/damages', () => ({ damagesApi: mockDamagesApi }))

const { default: RecentDamageList } = await import('@/components/damages/RecentDamageList.vue')

const damage: DamageListItem = {
  id: 10,
  robotId: 3,
  assignedTo: null,
  description: '포트홀 탐지',
  latitude: 37.5665,
  longitude: 126.978,
  capturedAt: '2026-08-05T09:00:00',
  currentStatus: 'AI_ANALYZED',
  imageCount: 1,
  damageScore: 82,
  repairRequired: true,
  repairPriority: 'HIGH',
  confidenceScore: 0.95,
  createdAt: '2026-08-05T09:00:00',
}

describe('RecentDamageList', () => {
  it('미확인 신규 탐지만 조회해 사건 상세로 연결한다', async () => {
    mockDamagesApi.list.mockResolvedValue({
      content: [damage],
      page: 0,
      size: 5,
      totalElements: 1,
      totalPages: 1,
    })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', name: 'dashboard', component: { template: '<div />' } },
        { path: '/damages', name: 'damages', component: { template: '<div />' } },
      ],
    })
    await router.push('/')

    const wrapper = mount(RecentDamageList, {
      props: {
        from: '2026-08-01',
        to: '2026-08-05',
      },
      global: {
        plugins: [router],
        stubs: {
          StatusBadge: { template: '<span>{{ label }}</span>', props: ['label'] },
          LoadingSpinner: { template: '<span>{{ label }}</span>', props: ['label'] },
          EmptyState: { template: '<span>{{ title }}</span>', props: ['title'] },
        },
      },
    })
    await flushPromises()

    const detailLink = wrapper.get('a[aria-label="탐지 사건 10 상세보기"]')
    expect(detailLink.attributes('href')).toBe('/damages?review=pending&damageId=10')
    expect(mockDamagesApi.list).toHaveBeenCalledWith({
      status: 'AI_ANALYZED',
      size: 5,
      from: '2026-08-01T00:00:00',
      to: '2026-08-06T00:00:00',
    })

    await wrapper.setProps({ from: '2026-07-01', to: '2026-07-31' })
    await flushPromises()
    expect(mockDamagesApi.list).toHaveBeenLastCalledWith({
      status: 'AI_ANALYZED',
      size: 5,
      from: '2026-07-01T00:00:00',
      to: '2026-08-01T00:00:00',
    })
    expect(wrapper.text()).toContain('높음')
    expect(wrapper.text()).not.toContain('AI 판독')
    expect(wrapper.text()).not.toContain('AI 분석완료')
    expect(wrapper.text()).not.toContain('#10')
  })
})
