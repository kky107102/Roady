import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, reactive } from 'vue'
import { administrativeRegionsApi } from '@/api/administrativeRegions'
import { useAssignedMapRegion } from '@/composables/useAssignedMapRegion'

const route = reactive({ path: '/damages', query: {} as Record<string, string> })
const replace = vi.fn(async ({ query }: { query: Record<string, string> }) => {
  route.query = query
})

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({ replace }),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    user: {
      id: 1,
      username: 'inspector',
      role: 'INSPECTOR',
      assignedRegionCode: '11680',
      assignedRegionName: '서울특별시 강남구',
    },
  }),
}))

vi.mock('@/api/administrativeRegions', () => ({
  administrativeRegionsApi: { getEmds: vi.fn() },
}))

const response = {
  regionCode: '11680',
  regionName: '서울특별시 강남구',
  bounds: { south: 37.46, north: 37.54, west: 127.01, east: 127.12 },
  emds: [
    {
      code: '1168010300',
      name: '청담동',
      bounds: { south: 37.51, north: 37.54, west: 127.03, east: 127.07 },
    },
    {
      code: '1168010100',
      name: '역삼동',
      bounds: { south: 37.48, north: 37.51, west: 127.02, east: 127.05 },
    },
  ],
}

const Harness = defineComponent({
  setup() {
    return useAssignedMapRegion()
  },
  template: '<div />',
})

describe('useAssignedMapRegion', () => {
  beforeEach(() => {
    route.query = {}
    replace.mockClear()
    vi.mocked(administrativeRegionsApi.getEmds).mockResolvedValue(response)
  })

  it('URL의 담당 읍면동 선택을 복원하고 해당 경계를 제공한다', async () => {
    route.query = { emd: '1168010100' }
    const wrapper = mount(Harness)
    await flushPromises()

    expect(administrativeRegionsApi.getEmds).toHaveBeenCalledWith('11680')
    expect(wrapper.vm.selectedCode).toBe('1168010100')
    expect(wrapper.vm.selectedBounds).toEqual(response.emds[1]?.bounds)
    expect(wrapper.vm.options.map((option) => option.name)).toEqual(['역삼동', '청담동'])
  })

  it('담당 구에 속하지 않은 URL 읍면동 코드를 제거한다', async () => {
    route.query = { emd: '2611010100' }
    mount(Harness)
    await flushPromises()

    expect(replace).toHaveBeenCalledWith({ path: '/damages', query: {} })
  })

  it('전체와 읍면동 선택을 URL 쿼리에 동기화한다', async () => {
    const wrapper = mount(Harness)
    await flushPromises()

    wrapper.vm.select('1168010300')
    await flushPromises()
    expect(route.query).toEqual({ emd: '1168010300' })

    wrapper.vm.select('')
    await flushPromises()
    expect(route.query).toEqual({})
  })
})
