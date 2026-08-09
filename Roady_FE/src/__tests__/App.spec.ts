import { describe, it, expect } from 'vitest'

import { mount } from '@vue/test-utils'
import App from '../App.vue'

describe('App', () => {
  it('renders the current route view', () => {
    const wrapper = mount(App, {
      global: {
        stubs: {
          RouterView: {
            template: '<main>current page</main>',
          },
        },
      },
    })

    expect(wrapper.text()).toContain('current page')
  })
})
