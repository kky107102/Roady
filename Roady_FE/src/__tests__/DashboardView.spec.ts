import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'

const dashboardStore = vi.hoisted(() => ({
  filter: {},
  trendFilter: {},
  damages: [] as unknown[],
  timeSeries: { unit: 'DAY', items: [] },
  loading: false,
  error: null,
  trendLoading: false,
  trendError: null,
  totalCount: 0,
  newDetectionCount: 0,
  urgentDamages: [],
  urgentReviewCount: 0,
  requestedCount: 0,
  highSeverityCount: 0,
  reviewRequiredCount: 0,
  repairingCount: 0,
  activeRobotCount: 0,
  fetchAll: vi.fn(),
  fetchTrend: vi.fn(),
  refreshRobots: vi.fn<() => Promise<void>>(),
  applyFilter: vi.fn(),
  applyTrendFilter: vi.fn(),
}))

vi.mock('@/stores/dashboard', () => ({ useDashboardStore: () => dashboardStore }))
vi.mock('@/composables/useAssignedMapRegion', async () => {
  const { computed, ref } = await import('vue')
  return {
    useAssignedMapRegion: () => ({
      assignedRegionCode: computed(() => ''),
      assignedRegionName: computed(() => null),
      options: computed(() => []),
      selectedCode: computed(() => ''),
      selectedBounds: computed(() => null),
      loading: ref(false),
      error: ref(null),
      load: vi.fn(),
      select: vi.fn(),
    }),
  }
})

const { default: DashboardView } = await import('@/views/DashboardView.vue')

describe('DashboardView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    dashboardStore.refreshRobots.mockResolvedValue()
  })

  it('상단 조회 기간을 URL에서 복원하고 조회 시 쿼리를 갱신한다', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', name: 'dashboard', component: DashboardView }],
    })
    await router.push('/?from=2026-08-01&to=2026-08-06')

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router],
        stubs: {
          CommonMap: { template: '<div />' },
          DashboardToolbar: {
            props: ['compact'],
            emits: ['apply'],
            template:
              '<div v-if="!compact"><button data-testid="dashboard-filter-apply" @click="$emit(\'apply\', { from: \'2026-07-01\', to: \'2026-07-31\', regionCode: \'\' })">조회</button><button data-testid="dashboard-filter-clear" @click="$emit(\'apply\', { from: \'\', to: \'\', regionCode: \'\' })">해제</button></div>',
          },
          StatCard: {
            props: ['label', 'to'],
            template:
              '<div :data-testid="`stat-${label}`" :data-operation="to?.query?.operation" :data-connection="to?.query?.connection"><slot /><slot name="icon" /></div>',
          },
          TrendChart: { template: '<div />' },
          LoadingSpinner: { template: '<div />' },
          RecentDamageList: { template: '<div />' },
          UrgentDamageList: { template: '<div />' },
        },
      },
    })

    expect(dashboardStore.filter).toMatchObject({ from: '2026-08-01', to: '2026-08-06' })

    await wrapper.get('[data-testid="dashboard-filter-apply"]').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.query).toMatchObject({
      from: '2026-07-01',
      to: '2026-07-31',
    })
    expect(dashboardStore.applyFilter).toHaveBeenCalledWith({
      from: '2026-07-01',
      to: '2026-07-31',
      regionCode: '',
    })

    await wrapper.get('[data-testid="dashboard-filter-clear"]').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.query.range).toBe('all')
    expect(router.currentRoute.value.query.from).toBeUndefined()
    expect(router.currentRoute.value.query.to).toBeUndefined()
    wrapper.unmount()
  })

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
        { path: '/robots', name: 'robots', component: { template: '<div />' } },
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
          StatCard: {
            props: { label: String, to: Object, action: Boolean },
            emits: ['activate'],
            template:
              '<button v-if="action" :data-testid="`stat-${label}`" @click="$emit(\'activate\')"><slot /><slot name="icon" /></button><div v-else><slot /><slot name="icon" /></div>',
          },
          TrendChart: { template: '<div />' },
          LoadingSpinner: { template: '<div />' },
          RecentDamageList: { template: '<div />' },
          UrgentDamageList: { template: '<div />' },
        },
      },
    })

    expect(wrapper.text()).toContain('선택한 기간에 탐지된 사건이 없습니다.')
    const movingRobotCard = wrapper.get('[data-testid="stat-운행 중 로디"]')
    await movingRobotCard.trigger('click')
    await flushPromises()

    expect(dashboardStore.refreshRobots).toHaveBeenCalledOnce()
    expect(router.currentRoute.value.name).toBe('robots')
    expect(router.currentRoute.value.query).toEqual({
      operation: 'MOVING',
      connection: 'CONNECTED',
    })

    await router.push('/')

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
