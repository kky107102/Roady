import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import AiResultBadge from '@/components/common/AiResultBadge.vue'

describe('AiResultBadge', () => {
  it('AI 출처는 라벨로, 판독 결과는 태그로 분리해 표시한다', () => {
    const wrapper = mount(AiResultBadge, {
      props: { type: 'warning', label: '높음' },
      global: {
        stubs: {
          StatusBadge: {
            template: '<span data-testid="status-badge" :data-type="type">{{ label }}</span>',
            props: ['type', 'label', 'size'],
          },
        },
      },
    })

    expect(wrapper.get('.ai-result-source').text()).toBe('AI 판독')
    const badge = wrapper.get('[data-testid="status-badge"]')
    expect(badge.text()).toBe('높음')
    expect(badge.attributes('data-type')).toBe('warning')
    expect(wrapper.attributes('aria-label')).toBe('AI 판독 결과: 높음')
  })
})
