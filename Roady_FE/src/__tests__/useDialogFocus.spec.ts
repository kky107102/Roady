import { defineComponent, nextTick, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { useDialogFocus } from '@/composables/useDialogFocus'

const DialogHarness = defineComponent({
  setup() {
    const open = ref(false)
    const dialog = ref<HTMLElement | null>(null)
    useDialogFocus(dialog, open)
    return { dialog, open }
  },
  template: `
    <div>
      <button id="opener" type="button" @click="open = true">열기</button>
      <div v-if="open" ref="dialog" role="dialog" tabindex="-1">
        <button id="first" type="button">처음</button>
        <button id="last" type="button">마지막</button>
      </div>
    </div>
  `,
})

afterEach(() => {
  document.body.innerHTML = ''
  document.body.style.overflow = ''
})

describe('useDialogFocus', () => {
  it('열릴 때 첫 컨트롤로 이동하고 닫힐 때 초점을 복원한다', async () => {
    const wrapper = mount(DialogHarness, { attachTo: document.body })
    const opener = wrapper.get('#opener').element as HTMLButtonElement
    opener.focus()

    await wrapper.get('#opener').trigger('click')
    await nextTick()

    expect(document.activeElement).toBe(wrapper.get('#first').element)
    expect(document.body.style.overflow).toBe('hidden')

    wrapper.vm.open = false
    await nextTick()

    expect(document.activeElement).toBe(opener)
    expect(document.body.style.overflow).toBe('')
    wrapper.unmount()
  })

  it('Tab과 Shift+Tab 초점을 대화상자 내부에서 순환시킨다', async () => {
    const wrapper = mount(DialogHarness, { attachTo: document.body })
    await wrapper.get('#opener').trigger('click')
    await nextTick()

    const first = wrapper.get('#first').element as HTMLButtonElement
    const last = wrapper.get('#last').element as HTMLButtonElement
    last.focus()
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true }))
    expect(document.activeElement).toBe(first)

    first.focus()
    document.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true }),
    )
    expect(document.activeElement).toBe(last)
    wrapper.unmount()
  })
})
