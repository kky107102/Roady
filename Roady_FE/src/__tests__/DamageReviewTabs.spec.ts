import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DamageReviewTabs from '@/components/damages/DamageReviewTabs.vue'

describe('DamageReviewTabs', () => {
  it('선택된 탭에 활성 상태와 키보드 초점을 제공한다', () => {
    const wrapper = mount(DamageReviewTabs, {
      props: { modelValue: 'pending' },
    })

    const tabs = wrapper.findAll('[role="tab"]')

    expect(tabs[0]!.classes()).toContain('is-active')
    expect(tabs[0]!.attributes('aria-selected')).toBe('true')
    expect(tabs[0]!.attributes('tabindex')).toBe('0')
    expect(tabs[1]!.classes()).not.toContain('is-active')
    expect(tabs[1]!.attributes('aria-selected')).toBe('false')
    expect(tabs[1]!.attributes('tabindex')).toBe('-1')
  })

  it('확인 탭을 선택하면 변경 이벤트를 전달한다', async () => {
    const wrapper = mount(DamageReviewTabs, {
      props: { modelValue: 'pending' },
    })

    await wrapper.findAll('[role="tab"]')[1]!.trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([['confirmed']])
  })

  it('방향키로 다음 탭을 선택하고 초점을 이동한다', async () => {
    const wrapper = mount(DamageReviewTabs, {
      attachTo: document.body,
      props: { modelValue: 'pending' },
    })
    const tabs = wrapper.findAll<HTMLButtonElement>('[role="tab"]')

    await tabs[0]!.trigger('keydown', { key: 'ArrowRight' })

    expect(wrapper.emitted('update:modelValue')).toEqual([['confirmed']])
    expect(document.activeElement).toBe(tabs[1]!.element)
    wrapper.unmount()
  })
})
