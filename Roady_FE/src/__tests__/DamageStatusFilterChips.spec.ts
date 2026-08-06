import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import RepairStatusFilterChips from '@/components/common/RepairStatusFilterChips.vue'

const counts = {
  requested: 1,
  in_progress: 1,
  completed: 2,
  not_required: 3,
}

describe('RepairStatusFilterChips', () => {
  it('처리 상태와 건수를 항상 노출한다', () => {
    const wrapper = mount(RepairStatusFilterChips, {
      props: {
        selected: [],
        counts,
      },
    })

    expect(wrapper.text()).not.toContain('전체')
    expect(wrapper.text()).toContain('요청 전 (1)')
    expect(wrapper.text()).toContain('요청 완료 (1)')
    expect(wrapper.text()).toContain('보수 완료 (2)')
    expect(wrapper.text()).not.toContain('보수 불필요')
    expect(wrapper.find('details').exists()).toBe(false)
  })

  it('확인 탭에서는 보수 불필요 상태와 건수를 선택할 수 있다', async () => {
    const wrapper = mount(RepairStatusFilterChips, {
      props: {
        selected: [],
        counts,
        includeNoRepair: true,
      },
    })

    const noRepairChip = wrapper.findAll('button').find((button) =>
      button.text().includes('보수 불필요'),
    )
    expect(noRepairChip?.text()).toBe('보수 불필요 (3)')

    await noRepairChip!.trigger('click')
    expect(wrapper.emitted('update:selected')).toEqual([[['not_required']]])
  })

  it('선택 상태를 aria-pressed로 전달한다', () => {
    const wrapper = mount(RepairStatusFilterChips, {
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
    const wrapper = mount(RepairStatusFilterChips, {
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
    const wrapper = mount(RepairStatusFilterChips, {
      props: {
        selected: [],
        counts,
      },
    })

    await wrapper.findAll('button')[0]!.trigger('click')

    expect(wrapper.emitted('update:selected')).toEqual([[['requested']]])
  })

  it('세 상태를 모두 선택하면 필터를 해제한다', async () => {
    const wrapper = mount(RepairStatusFilterChips, {
      props: {
        selected: ['requested', 'in_progress'],
        counts,
      },
    })

    await wrapper.findAll('button')[2]!.trigger('click')

    expect(wrapper.emitted('update:selected')).toEqual([[[]]])
  })

  it('정렬 같은 부가 조작을 동일한 필터 바에 배치할 수 있다', () => {
    const wrapper = mount(RepairStatusFilterChips, {
      props: { selected: [], counts },
      slots: {
        actions: '<select aria-label="보수 사건 정렬"><option>우선순위 높은 순</option></select>',
      },
    })

    expect(wrapper.get('.status-filter-actions').get('select').attributes('aria-label')).toBe(
      '보수 사건 정렬',
    )
  })
})
