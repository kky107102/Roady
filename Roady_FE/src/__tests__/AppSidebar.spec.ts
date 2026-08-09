import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AppSidebar from '@/components/layout/AppSidebar.vue'

const mocks = vi.hoisted(() => ({
  logout: vi.fn<() => Promise<void>>(),
  replace: vi.fn<() => Promise<void>>(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ name: 'dashboard' }),
  useRouter: () => ({ replace: mocks.replace }),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    user: { id: 1, username: 'admin', role: 'ADMIN' },
    logout: mocks.logout,
  }),
}))

describe('AppSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.logout.mockResolvedValue()
    mocks.replace.mockResolvedValue()
  })

  it('사용자 이름과 권한을 표시하고 설정 톱니바퀴는 노출하지 않는다', () => {
    const wrapper = mount(AppSidebar, {
      global: {
        stubs: { RouterLink: { template: '<a><slot /></a>' } },
      },
    })

    expect(wrapper.get('.profile-name').text()).toBe('admin')
    expect(wrapper.get('.profile-department').text()).toBe('관리자')
    expect(wrapper.find('[aria-label="설정 관리"]').exists()).toBe(false)
    expect(wrapper.get('.logout-button').text()).toBe('로그아웃')
  })

  it('로그아웃 후 로그인 화면으로 이동한다', async () => {
    const wrapper = mount(AppSidebar, {
      global: {
        stubs: { RouterLink: { template: '<a><slot /></a>' } },
      },
    })

    await wrapper.get('.logout-button').trigger('click')

    expect(mocks.logout).toHaveBeenCalledOnce()
    expect(mocks.replace).toHaveBeenCalledWith({ name: 'login' })
  })
})
