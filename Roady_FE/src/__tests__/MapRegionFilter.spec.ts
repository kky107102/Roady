import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import MapRegionFilter from '@/components/common/MapRegionFilter.vue'

const options = [
  {
    code: '1168010100',
    name: '역삼동',
    bounds: { south: 37.48, north: 37.51, west: 127.02, east: 127.05 },
  },
  {
    code: '1168010300',
    name: '청담동',
    bounds: { south: 37.51, north: 37.54, west: 127.03, east: 127.07 },
  },
]

describe('MapRegionFilter', () => {
  it('담당 시군구 전체와 소속 읍면동만 선택지로 제공한다', () => {
    const wrapper = mount(MapRegionFilter, {
      props: {
        id: 'dashboard-region',
        modelValue: '',
        assignedRegionName: '서울특별시 강남구',
        options,
      },
    })

    expect(wrapper.get('label').attributes('for')).toBe('dashboard-region')
    expect(wrapper.findAll('option').map((option) => option.text())).toEqual([
      '읍면동 선택',
      '역삼동',
      '청담동',
    ])
  })

  it('읍면동 선택을 갱신한다', async () => {
    const wrapper = mount(MapRegionFilter, {
      props: {
        id: 'damage-region',
        modelValue: '',
        assignedRegionName: '서울특별시 강남구',
        options,
      },
    })

    await wrapper.get('select').setValue('1168010100')
    expect(wrapper.emitted('update:modelValue')).toEqual([['1168010100']])
  })

  it('담당 지역 누락과 조회 오류를 각각 안내한다', async () => {
    const missing = mount(MapRegionFilter, {
      props: { id: 'missing-region', modelValue: '' },
    })
    expect(missing.get('[role="status"]').text()).toContain('담당 지역 미지정')

    const failed = mount(MapRegionFilter, {
      props: {
        id: 'failed-region',
        modelValue: '',
        assignedRegionName: '서울특별시 강남구',
        error: '읍면동 목록을 불러오지 못했습니다.',
      },
    })
    expect(failed.get('[role="alert"]').text()).toContain('불러오지 못했습니다')
    await failed.get('button').trigger('click')
    expect(failed.emitted('retry')).toHaveLength(1)
  })
})
