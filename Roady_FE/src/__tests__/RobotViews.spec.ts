import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { robotsApi } from '@/api/robots'
import RobotDetailView from '@/views/RobotDetailView.vue'
import RobotListView from '@/views/RobotListView.vue'
import type { Robot } from '@/types/robot'

const route = ref({ params: { id: '1' } })

vi.mock('vue-router', () => ({
  useRoute: () => route.value,
}))

vi.mock('@/api/robots', () => ({
  robotsApi: {
    list: vi.fn(),
    get: vi.fn(),
    latestLocation: vi.fn(),
    command: vi.fn(),
    commands: vi.fn(),
  },
}))

vi.mock('@/composables/useRobotLocationStream', async () => {
  const { ref } = await import('vue')
  return {
    useRobotLocationStream: () => ({
      status: ref('idle'),
      latestLocation: ref(null),
      pathPoints: ref([]),
      start: vi.fn(),
      stop: vi.fn(),
    }),
  }
})

const robot: Robot = {
  id: 1,
  userId: 10,
  name: '로디 1호',
  serialNumber: 'RD-001',
  status: 'STANDBY',
  active: true,
  latestStatus: null,
  createdAt: '2026-07-29T10:00:00',
  updatedAt: '2026-07-29T10:00:00',
}

const global = {
  stubs: {
    RouterLink: { template: '<a><slot /></a>' },
    StatusBadge: { props: ['label'], template: '<span>{{ label }}</span>' },
    LoadingSpinner: { template: '<div>로딩</div>' },
  },
}

describe('RobotListView', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows an empty state when no robots are registered', async () => {
    vi.mocked(robotsApi.list).mockResolvedValue([])
    const wrapper = mount(RobotListView, { global })
    await flushPromises()

    expect(wrapper.text()).toContain('등록된 로봇이 없습니다.')
  })

  it('shows safe fallback values when latestStatus is null', async () => {
    vi.mocked(robotsApi.list).mockResolvedValue([robot])
    const wrapper = mount(RobotListView, { global })
    await flushPromises()

    expect(wrapper.text()).toContain('로디 1호')
    expect(wrapper.text()).toContain('상태 없음')
    expect(wrapper.text()).toContain('상세 보기')
  })

  it('sorts robot names naturally and filters by operation and connection status', async () => {
    const robot8: Robot = {
      ...robot,
      id: 8,
      name: '로디8호',
      serialNumber: 'RD-008',
      latestStatus: {
        id: 8,
        latitude: null,
        longitude: null,
        batteryLevel: 80,
        operationStatus: 'MOVING',
        connectionStatus: 'CONNECTED',
        errorCode: null,
        errorMessage: null,
        recordedAt: '2026-07-29T11:00:00',
      },
    }
    const robot2: Robot = {
      ...robot,
      id: 2,
      name: '로디2호',
      serialNumber: 'RD-002',
      latestStatus: {
        id: 2,
        latitude: null,
        longitude: null,
        batteryLevel: 5,
        operationStatus: 'ERROR',
        connectionStatus: 'DISCONNECTED',
        errorCode: 'ROBOT_ERROR',
        errorMessage: null,
        recordedAt: '2026-07-29T10:30:00',
      },
    }
    vi.mocked(robotsApi.list).mockResolvedValue([robot8, robot2])
    const wrapper = mount(RobotListView, { global })
    await flushPromises()

    expect(wrapper.findAll('.robot-name').map((cell) => cell.text())).toEqual([
      '로디2호',
      '로디8호',
    ])
    expect(wrapper.text()).toContain('배터리 부족 5%')
    expect(wrapper.text()).toContain('운행 상태 오류')
    expect(wrapper.text()).toContain('연결 끊김')
    expect(wrapper.get('.low-battery').text()).toBe('5%')

    await wrapper.get('#robot-sort').setValue('battery-desc')
    expect(wrapper.findAll('.robot-name').map((cell) => cell.text())).toEqual([
      '로디8호',
      '로디2호',
    ])

    await wrapper.get('#robot-search').setValue('RD-002')
    expect(wrapper.findAll('.robot-name')).toHaveLength(2)
    await wrapper.get('.search-button').trigger('submit')
    expect(wrapper.findAll('.robot-name').map((cell) => cell.text())).toEqual(['로디2호'])
    await wrapper.get('.filter-reset').trigger('click')

    await wrapper.get('#operation-filter').setValue('MOVING')
    await wrapper.get('#connection-filter').setValue('CONNECTED')

    expect(wrapper.findAll('.robot-name').map((cell) => cell.text())).toEqual(['로디8호'])
    expect(wrapper.text()).toContain('1대 / 총 2대')
  })

  it('retries after a list request failure', async () => {
    vi.mocked(robotsApi.list)
      .mockRejectedValueOnce(new Error('network'))
      .mockResolvedValueOnce([robot])
    const wrapper = mount(RobotListView, { global })
    await flushPromises()

    expect(wrapper.text()).toContain('로봇 목록을 불러오지 못했습니다.')
    await wrapper.get('button').trigger('click')
    await flushPromises()

    expect(robotsApi.list).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('로디 1호')
  })
})

describe('RobotDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    route.value = { params: { id: '1' } }
    vi.mocked(robotsApi.commands).mockResolvedValue([])
    vi.mocked(robotsApi.latestLocation).mockRejectedValue(new Error('no live location'))
  })

  it('reloads detail data by the robot id and handles a missing latest status', async () => {
    vi.mocked(robotsApi.get).mockResolvedValue(robot)
    const wrapper = mount(RobotDetailView, { global })
    await flushPromises()

    expect(robotsApi.get).toHaveBeenCalledWith(1)
    expect(wrapper.text()).toContain('로디 1호')
    expect(wrapper.text()).toContain('실시간 위치 및 이동 경로')
    expect(wrapper.text()).toContain('현재 위치와 이 화면에 접속한 이후 수신된 이동 경로를 표시합니다.')
    expect(wrapper.text()).toContain('기본 정보')
    expect(wrapper.text()).toContain('수집된 최신 상태가 없습니다.')
    expect(wrapper.text()).toContain('운행 시작')
  })

  it('switches to return and emergency controls after starting operation', async () => {
    vi.mocked(robotsApi.get).mockResolvedValue(robot)
    vi.mocked(robotsApi.command).mockResolvedValue({
      id: 1,
      robotId: 1,
      requestedBy: 10,
      commandType: 'START_PATROL',
      commandStatus: 'PENDING',
      resultMessage: null,
      requestedAt: '2026-07-30T10:00:00',
      completedAt: null,
    })
    const wrapper = mount(RobotDetailView, { global })
    await flushPromises()

    await wrapper.get('.start-button').trigger('click')
    await flushPromises()

    expect(robotsApi.command).toHaveBeenCalledWith(1, 'START_PATROL')
    expect(wrapper.text()).toContain('로봇 응답을 기다리는 중입니다.')
    expect(wrapper.text()).toContain('스테이션 복귀')
    expect(wrapper.text()).toContain('긴급 정지')
    expect(wrapper.find('.start-button').exists()).toBe(false)
    expect(wrapper.get('.return-button').attributes('disabled')).toBeDefined()
    expect(wrapper.get('.emergency-button').attributes('disabled')).toBeDefined()
  })

  it('shows return progress feedback while keeping emergency stop available', async () => {
    vi.mocked(robotsApi.get).mockResolvedValue({
      ...robot,
      latestStatus: {
        id: 1,
        latitude: null,
        longitude: null,
        batteryLevel: 60,
        operationStatus: 'MOVING',
        connectionStatus: 'CONNECTED',
        errorCode: null,
        errorMessage: null,
        recordedAt: '2026-07-30T10:00:00',
      },
    })
    vi.mocked(robotsApi.command).mockResolvedValue({
      id: 2,
      robotId: 1,
      requestedBy: 10,
      commandType: 'RETURN_HOME',
      commandStatus: 'PENDING',
      resultMessage: null,
      requestedAt: '2026-07-30T10:01:00',
      completedAt: null,
    })
    const wrapper = mount(RobotDetailView, { global })
    await flushPromises()

    await wrapper.get('.return-button').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('복귀 요청됨…')
    expect(wrapper.text()).toContain('로봇 응답을 기다리는 중입니다.')
    expect(wrapper.get('.return-button').attributes('disabled')).toBeDefined()
    expect(wrapper.get('.emergency-button').attributes('disabled')).toBeUndefined()
  })

  it('enables return and emergency controls after start succeeds', async () => {
    vi.mocked(robotsApi.get).mockResolvedValue(robot)
    vi.mocked(robotsApi.command).mockResolvedValue({
      id: 3,
      robotId: 1,
      requestedBy: 10,
      commandType: 'START_PATROL',
      commandStatus: 'SUCCEEDED',
      resultMessage: null,
      requestedAt: '2026-07-30T10:02:00',
      completedAt: '2026-07-30T10:02:01',
    })
    const wrapper = mount(RobotDetailView, { global })
    await flushPromises()

    await wrapper.get('.start-button').trigger('click')
    await flushPromises()

    expect(wrapper.get('.return-button').attributes('disabled')).toBeUndefined()
    expect(wrapper.get('.emergency-button').attributes('disabled')).toBeUndefined()
    expect(wrapper.text()).toContain('운행 시작 명령 처리가 완료되었습니다.')
  })

  it('shows a resume button after emergency stop succeeds', async () => {
    vi.mocked(robotsApi.get).mockResolvedValue({
      ...robot,
      latestStatus: {
        id: 1,
        latitude: null,
        longitude: null,
        batteryLevel: 60,
        operationStatus: 'MOVING',
        connectionStatus: 'CONNECTED',
        errorCode: null,
        errorMessage: null,
        recordedAt: '2026-07-30T10:00:00',
      },
    })
    vi.mocked(robotsApi.command).mockResolvedValue({
      id: 4,
      robotId: 1,
      requestedBy: 10,
      commandType: 'EMERGENCY_STOP',
      commandStatus: 'SUCCEEDED',
      resultMessage: null,
      requestedAt: '2026-07-30T10:03:00',
      completedAt: '2026-07-30T10:03:01',
    })
    const wrapper = mount(RobotDetailView, { global })
    await flushPromises()

    await wrapper.get('.emergency-button').trigger('click')
    await flushPromises()

    expect(wrapper.get('.start-button').text()).toBe('다시 운행')
    expect(wrapper.find('.return-button').exists()).toBe(false)
    expect(wrapper.find('.emergency-button').exists()).toBe(false)
    expect(wrapper.text()).toContain('긴급 정지 명령 처리가 완료되었습니다.')
  })

  it('shows only an unavailable notice while the robot is inspecting', async () => {
    vi.mocked(robotsApi.get).mockResolvedValue({
      ...robot,
      latestStatus: {
        id: 1,
        latitude: null,
        longitude: null,
        batteryLevel: 60,
        operationStatus: 'INSPECTING',
        connectionStatus: 'CONNECTED',
        errorCode: null,
        errorMessage: null,
        recordedAt: '2026-07-30T10:00:00',
      },
    })
    const wrapper = mount(RobotDetailView, { global })
    await flushPromises()

    expect(wrapper.text()).toContain('현재 점검 중이라 원격 운행이 불가합니다.')
    expect(wrapper.find('.control-button').exists()).toBe(false)
  })

  it('does not request an invalid robot id', async () => {
    route.value = { params: { id: 'invalid' } }
    const wrapper = mount(RobotDetailView, { global })
    await flushPromises()

    expect(robotsApi.get).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('존재하지 않는 로봇입니다.')
  })
})
