import { afterEach, describe, expect, it } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

let wrapper: VueWrapper | null = null

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
})

describe('ConfirmDialog', () => {
  it('제목과 설명을 연결하고 확인·취소 동작을 전달한다', async () => {
    wrapper = mount(ConfirmDialog, {
      attachTo: document.body,
      props: {
        title: '요청을 취소할까요?',
        description: '취소한 요청은 다시 요청할 수 있습니다.',
        confirmLabel: '요청 취소',
      },
    })

    await nextTick()
    const dialog = document.body.querySelector<HTMLElement>('[role="alertdialog"]')!
    expect(dialog.getAttribute('aria-labelledby')).toBeTruthy()
    expect(dialog.getAttribute('aria-describedby')).toBeTruthy()
    expect(dialog.textContent).toContain('요청을 취소할까요?')

    const buttons = dialog.querySelectorAll<HTMLButtonElement>('button')
    buttons[0]!.click()
    buttons[1]!.click()
    await nextTick()

    expect(wrapper.emitted('cancel')).toHaveLength(1)
    expect(wrapper.emitted('confirm')).toHaveLength(1)
  })

  it('처리 중에는 닫기와 중복 제출을 막는다', async () => {
    wrapper = mount(ConfirmDialog, {
      attachTo: document.body,
      props: { title: '처리할까요?', busy: true },
    })

    await nextTick()
    const dialog = document.body.querySelector<HTMLElement>('[role="alertdialog"]')!
    const buttons = Array.from(dialog.querySelectorAll<HTMLButtonElement>('button'))
    expect(buttons.every((button) => button.disabled)).toBe(true)
    expect(buttons[1]!.getAttribute('aria-busy')).toBe('true')
    expect(buttons[1]!.textContent?.trim()).toBe('처리 중...')

    dialog.click()
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('cancel')).toBeUndefined()
    expect(wrapper.emitted('confirm')).toBeUndefined()
  })

  it('ESC로 취소하고 위험 동작의 버튼 위계를 표시한다', async () => {
    wrapper = mount(ConfirmDialog, {
      attachTo: document.body,
      props: { title: '삭제할까요?', tone: 'danger' },
    })

    await nextTick()
    expect(document.body.querySelector('.krds-btn.filled')?.classList).toContain('danger')
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('cancel')).toHaveLength(1)
  })
})
