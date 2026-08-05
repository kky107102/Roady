import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'

const dashboardStore = vi.hoisted(() => ({
  filter: {},
  damages: [] as unknown[],
  timeSeries: [],
  loading: false,
  error: null,
  totalCount: 0,
  highSeverityCount: 0,
  reviewRequiredCount: 0,
  repairingCount: 0,
  activeRobotCount: 0,
  fetchAll: vi.fn(),
  applyFilter: vi.fn(),
}))

vi.mock('@/stores/dashboard', () => ({ useDashboardStore: () => dashboardStore }))

const { default: DashboardView } = await import('@/views/DashboardView.vue')

describe('DashboardView', () => {
  it('지도 사건의 확인 여부에 맞는 탭과 상세로 이동한다', async () => {
    const damage = {
      id: 10,
      latitude: 37.5,
      longitude: 127,
      currentStatus: 'AI_ANALYZED',
    }
    dashboardStore.damages = [damage]
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', name: 'dashboard', component: DashboardView },
        { path: '/damages', name: 'damages', component: { template: '<div />' } },
      ],
    })
    await router.push('/')

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router],
        stubs: {
          CommonMap: {
            template:
              '<button data-testid="map-marker" @click="$emit(\'markerSelect\', 10)">마커</button>',
            emits: ['markerSelect'],
          },
          DashboardToolbar: { template: '<div />' },
          StatCard: { template: '<div><slot /><slot name="icon" /></div>' },
          TrendChart: { template: '<div />' },
          LoadingSpinner: { template: '<div />' },
          RecentDamageList: { template: '<div />' },
        },
      },
    })

    await wrapper.get('[data-testid="map-marker"]').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('damages')
    expect(router.currentRoute.value.query.review).toBe('pending')
    expect(router.currentRoute.value.query.damageId).toBe('10')

    damage.currentStatus = 'REQUESTED'
    await router.push('/')
    await wrapper.get('[data-testid="map-marker"]').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.query.review).toBe('confirmed')
    expect(router.currentRoute.value.query.damageId).toBe('10')
    wrapper.unmount()
  })
})
