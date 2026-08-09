import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DashboardToolbar from '@/components/dashboard/DashboardToolbar.vue'

describe('DashboardToolbar', () => {
  it('잘못된 날짜 범위는 조회하지 않고 공통 오류를 표시한다', async () => {
    const wrapper = mount(DashboardToolbar, {
      props: {
        modelValue: { from: '2026-08-01', to: '2026-08-06', regionCode: '' },
      },
    })

    const inputs = wrapper.findAll('input[type="date"]')
    await inputs[0]!.setValue('2026-08-07')
    await inputs[1]!.setValue('2026-08-06')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.get('[role="alert"]').text()).toBe('시작일은 종료일보다 이전이어야 합니다.')
    expect(wrapper.emitted('apply')).toBeUndefined()
  })

  it('기간 프리셋을 선택하면 목록 화면과 같이 즉시 조회한다', async () => {
    const wrapper = mount(DashboardToolbar, {
      props: {
        modelValue: { from: '2026-08-01', to: '2026-08-06', regionCode: '' },
      },
    })

    await wrapper.findAll('.preset-btn')[1]!.trigger('click')

    expect(wrapper.emitted('apply')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue')).toHaveLength(1)
  })
})
