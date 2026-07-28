import { describe, expect, it } from 'vitest'

import { mount } from '@vue/test-utils'
import KrdsTextInput from '@/components/common/KrdsTextInput.vue'

describe('KrdsTextInput', () => {
  it('connects the label, required state, hint, and autocomplete to the input', () => {
    const wrapper = mount(KrdsTextInput, {
      props: {
        id: 'username',
        name: 'username',
        label: '아이디',
        modelValue: '',
        autocomplete: 'username',
        hint: '등록된 관리자 아이디를 입력해 주세요.',
        required: true,
      },
    })

    const input = wrapper.get('input')

    expect(wrapper.get('label').attributes('for')).toBe('username')
    expect(input.attributes('id')).toBe('username')
    expect(input.attributes('name')).toBe('username')
    expect(input.attributes('required')).toBeDefined()
    expect(input.attributes('autocomplete')).toBe('username')
    expect(input.attributes('aria-describedby')).toBe('username-hint')
    expect(wrapper.get('#username-hint').text()).toContain('등록된 관리자 아이디')
  })

  it('associates an error and toggles password visibility', async () => {
    const wrapper = mount(KrdsTextInput, {
      props: {
        id: 'password',
        name: 'password',
        label: '비밀번호',
        modelValue: 'secret',
        type: 'password',
        error: '비밀번호를 입력해 주세요.',
        required: true,
        showPasswordToggle: true,
      },
    })

    const input = wrapper.get('input')
    const toggle = wrapper.get('button')

    expect(input.attributes('type')).toBe('password')
    expect(input.attributes('aria-invalid')).toBe('true')
    expect(input.attributes('aria-describedby')).toBe('password-error')
    expect(wrapper.get('#password-error').attributes('role')).toBe('alert')

    await toggle.trigger('click')

    expect(input.attributes('type')).toBe('text')
    expect(toggle.attributes('aria-pressed')).toBe('true')
    expect(toggle.attributes('aria-label')).toBe('비밀번호 숨기기')
  })
})
