import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PageFilterActions from '@/components/common/PageFilterActions.vue'

describe('PageFilterActions', () => {
  it('모든 조회 바에 동일한 KRDS 버튼 크기와 위계를 제공한다', async () => {
    const wrapper = mount(PageFilterActions)
    const buttons = wrapper.findAll('button')

    expect(buttons).toHaveLength(2)
    expect(buttons[0]!.attributes('type')).toBe('button')
    expect(buttons[0]!.classes()).toEqual(
      expect.arrayContaining(['krds-btn', 'small', 'secondary']),
    )
    expect(buttons[1]!.attributes('type')).toBe('submit')
    expect(buttons[1]!.classes()).toEqual(
      expect.arrayContaining(['krds-btn', 'small', 'filled', 'primary']),
    )

    await buttons[0]!.trigger('click')
    expect(wrapper.emitted('reset')).toHaveLength(1)
  })

  it('처리 중에는 초기화와 조회를 모두 비활성화한다', () => {
    const wrapper = mount(PageFilterActions, { props: { busy: true } })
    const buttons = wrapper.findAll('button')

    expect(buttons.every((button) => button.attributes('disabled') !== undefined)).toBe(true)
    expect(buttons[1]!.attributes('aria-busy')).toBe('true')
  })
})
