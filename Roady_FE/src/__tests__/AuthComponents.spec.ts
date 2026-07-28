import { describe, expect, it } from 'vitest'

import { mount } from '@vue/test-utils'
import AuthLayout from '@/layouts/AuthLayout.vue'
import KrdsCheckbox from '@/components/common/KrdsCheckbox.vue'

describe('authentication components', () => {
  it('connects the authentication content to its heading and renders shared branding', () => {
    const wrapper = mount(AuthLayout, {
      props: {
        contentLabelledby: 'login-title',
      },
      slots: {
        default: '<h1 id="login-title">로그인</h1>',
      },
    })

    expect(wrapper.get('.content-panel').attributes('aria-labelledby')).toBe('login-title')
    expect(wrapper.get('.brand-logo').attributes('alt')).toBe('Roady')
    expect(wrapper.text()).toContain('도로 파손을 더 빠르고 정확하게')
    expect(wrapper.text()).toContain('© 2026 Roady')
  })

  it('connects the common checkbox label and model value', async () => {
    const wrapper = mount(KrdsCheckbox, {
      props: {
        id: 'remember-username',
        label: '아이디 저장',
        modelValue: false,
      },
    })
    const input = wrapper.get('input[type="checkbox"]')

    expect(wrapper.get('label').attributes('for')).toBe('remember-username')

    await input.setValue(true)

    expect(wrapper.emitted('update:modelValue')).toEqual([[true]])
  })
})
