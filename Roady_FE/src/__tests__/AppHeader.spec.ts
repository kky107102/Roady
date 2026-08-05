import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

vi.mock('vue-router', () => ({
  useRoute: () => ({ matched: [{ meta: { title: '탐지 검토' } }] }),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    user: {
      assignedRegionName: '서울특별시 강남구',
    },
  }),
}))

const { default: AppHeader } = await import('@/components/layout/AppHeader.vue')

describe('AppHeader', () => {
  it('화면 제목 우측에 로그인 사용자의 담당 시군구를 표시한다', () => {
    const wrapper = mount(AppHeader)

    expect(wrapper.get('h1').text()).toBe('탐지 검토')
    expect(wrapper.get('.assigned-region').text()).toContain('서울특별시 강남구')
    expect(wrapper.get('.assigned-region__icon').attributes('aria-hidden')).toBe('true')
  })
})
