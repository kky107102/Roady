import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import KrdsSelect from '@/components/common/KrdsSelect.vue'

const baseProps = {
  id: 'status-filter',
  name: 'status-filter',
  label: '운행 상태',
  modelValue: 'ALL',
  options: [
    { value: 'ALL', label: '전체' },
    { value: 'MOVING', label: '이동 중' },
  ],
}

describe('KrdsSelect', () => {
  it('필터가 적용된 경우에만 선택 상태를 강조한다', async () => {
    const wrapper = mount(KrdsSelect, { props: baseProps })
    const select = wrapper.get('select')

    expect(select.classes()).not.toContain('is-filter-active')

    await wrapper.setProps({ modelValue: 'MOVING', filterActive: true })

    expect(select.classes()).toContain('is-filter-active')
  })

  it('선택값 변경을 공통 이벤트로 전달한다', async () => {
    const wrapper = mount(KrdsSelect, { props: baseProps })

    await wrapper.get('select').setValue('MOVING')

    expect(wrapper.emitted('update:modelValue')).toEqual([['MOVING']])
    expect(wrapper.emitted('change')).toEqual([['MOVING']])
  })
})
