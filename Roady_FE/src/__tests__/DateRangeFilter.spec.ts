import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DateRangeFilter from '@/components/common/DateRangeFilter.vue'

describe('DateRangeFilter', () => {
  it('선택된 기간 프리셋을 다시 누르면 기간 선택을 해제한다', async () => {
    const wrapper = mount(DateRangeFilter, {
      props: {
        from: '2026-07-28',
        to: '2026-08-03',
        activePreset: 1,
      },
    })

    const presetButtons = wrapper.findAll('.preset-btn')
    await presetButtons[1]!.trigger('click')

    expect(wrapper.emitted('update:activePreset')).toEqual([[null]])
    expect(wrapper.emitted('update:from')).toEqual([['']])
    expect(wrapper.emitted('update:to')).toEqual([['']])
    expect(wrapper.emitted('preset-apply')).toEqual([[{ from: '', to: '' }]])
  })

  it('다른 기간 프리셋을 누르면 해당 기간으로 변경한다', async () => {
    const wrapper = mount(DateRangeFilter, {
      props: {
        from: '2026-07-28',
        to: '2026-08-03',
        activePreset: 1,
      },
    })

    const presetButtons = wrapper.findAll('.preset-btn')
    await presetButtons[2]!.trigger('click')

    expect(wrapper.emitted('update:activePreset')).toEqual([[2]])
    expect(wrapper.emitted('update:from')?.[0]?.[0]).not.toBe('')
    expect(wrapper.emitted('update:to')?.[0]?.[0]).not.toBe('')
  })
})
