import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import type { DamageListItem } from '@/types/damage'
import RepairTable from '@/components/repairs/RepairTable.vue'

function repairItem(id: number): DamageListItem {
  return {
    id,
    robotId: 1,
    assignedTo: null,
    description: `보수 사건 ${id}`,
    latitude: 37.5665,
    longitude: 126.978,
    capturedAt: '2026-08-05T09:00:00',
    currentStatus: 'REQUESTED',
    imageCount: 1,
    damageScore: 80,
    repairRequired: true,
    repairPriority: 'HIGH',
    processingPriority: 'HIGH',
    confidenceScore: 0.95,
    createdAt: '2026-08-05T09:00:00',
  }
}

describe('RepairTable', () => {
  it('현재 정렬된 목록 순서대로 번호를 표시한다', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/repairs', name: 'repairs', component: { template: '<div />' } },
        {
          path: '/repairs/:damageId',
          name: 'repair-detail',
          component: { template: '<div />' },
        },
      ],
    })
    await router.push('/repairs')

    const wrapper = mount(RepairTable, {
      props: { items: [repairItem(20), repairItem(10)] },
      global: {
        plugins: [router],
        stubs: {
          StatusBadge: { template: '<span />' },
          RepairStatusBadge: { template: '<span />' },
        },
      },
    })

    expect(wrapper.get('th.col-number').text()).toBe('번호')
    expect(wrapper.findAll('td.col-number').map((cell) => cell.text())).toEqual(['1', '2'])
  })
})
