import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DamageStatusFilterChips from '@/components/damages/DamageStatusFilterChips.vue'

const counts = {
  requested: 1,
  in_progress: 1,
  completed: 2,
}

describe('DamageStatusFilterChips', () => {
  it('처리 상태와 건수를 항상 노출한다', () => {
    const wrapper = mount(DamageStatusFilterChips, {
      props: {
        selected: [],
        counts,
      },
    })

    expect(wrapper.text()).not.toContain('전체')
    expect(wrapper.text()).toContain('요청 전 (1)')
    expect(wrapper.text()).toContain('요청 완료 (1)')
    expect(wrapper.text()).toContain('보수 완료 (2)')
    expect(wrapper.find('details').exists()).toBe(false)
  })

  it('선택 상태를 aria-pressed로 전달한다', () => {
    const wrapper = mount(DamageStatusFilterChips, {
      props: {
        selected: ['requested'],
        counts,
      },
    })
    const chips = wrapper.findAll('button')

    expect(chips[0]!.attributes('aria-pressed')).toBe('true')
    expect(chips[1]!.attributes('aria-pressed')).toBe('false')
    expect(chips[2]!.attributes('aria-pressed')).toBe('false')
  })

  it('필터 칩을 누르면 다중 선택 상태를 갱신한다', async () => {
    const wrapper = mount(DamageStatusFilterChips, {
      props: {
        selected: ['requested'],
        counts,
      },
    })
    const chips = wrapper.findAll('button')

    await chips[1]!.trigger('click')
    await chips[0]!.trigger('click')
    await chips[2]!.trigger('click')

    expect(wrapper.emitted('update:selected')).toEqual([
      [['requested', 'in_progress']],
      [[]],
      [['requested', 'completed']],
    ])
  })

  it('아무 상태도 선택하지 않았을 때 개별 칩을 누르면 해당 상태만 선택한다', async () => {
    const wrapper = mount(DamageStatusFilterChips, {
      props: {
        selected: [],
        counts,
      },
    })

    await wrapper.findAll('button')[0]!.trigger('click')

    expect(wrapper.emitted('update:selected')).toEqual([[['requested']]])
  })

  it('세 상태를 모두 선택하면 필터를 해제한다', async () => {
    const wrapper = mount(DamageStatusFilterChips, {
      props: {
        selected: ['requested', 'in_progress'],
        counts,
      },
    })

    await wrapper.findAll('button')[2]!.trigger('click')

    expect(wrapper.emitted('update:selected')).toEqual([[[]]])
  })
})
