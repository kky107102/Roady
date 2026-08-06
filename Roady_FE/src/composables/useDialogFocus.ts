import {
  nextTick,
  onBeforeUnmount,
  onMounted,
  toValue,
  watch,
  type MaybeRefOrGetter,
  type Ref,
} from 'vue'

const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

let scrollLockCount = 0
let originalBodyOverflow = ''

function lockBackgroundScroll() {
  if (scrollLockCount === 0) {
    originalBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
  }
  scrollLockCount += 1
}

function unlockBackgroundScroll() {
  scrollLockCount = Math.max(0, scrollLockCount - 1)
  if (scrollLockCount === 0) document.body.style.overflow = originalBodyOverflow
}

/** Applies the KRDS dialog keyboard loop and restores focus to the opener. */
export function useDialogFocus(
  dialogRef: Ref<HTMLElement | null>,
  active: MaybeRefOrGetter<boolean> = true,
  options: { onEscape?: () => void } = {},
) {
  let opener: HTMLElement | null = null
  let engaged = false

  function focusableElements(): HTMLElement[] {
    return dialogRef.value
      ? Array.from(dialogRef.value.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR))
      : []
  }

  async function engage() {
    if (engaged) return
    engaged = true
    opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
    lockBackgroundScroll()
    await nextTick()
    const dialog = dialogRef.value
    if (!dialog || !toValue(active)) return
    ;(focusableElements()[0] ?? dialog).focus()
  }

  function disengage() {
    if (!engaged) return
    engaged = false
    unlockBackgroundScroll()
    if (opener?.isConnected) opener.focus()
    opener = null
  }

  function handleKeydown(event: KeyboardEvent) {
    if (!engaged) return
    if (event.key === 'Escape' && options.onEscape) {
      event.preventDefault()
      options.onEscape()
      return
    }
    if (event.key !== 'Tab') return
    const elements = focusableElements()
    if (elements.length === 0) {
      event.preventDefault()
      dialogRef.value?.focus()
      return
    }

    const first = elements[0]!
    const last = elements[elements.length - 1]!
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  watch(
    () => toValue(active),
    (enabled) => {
      if (enabled) void engage()
      else disengage()
    },
    { immediate: true, flush: 'post' },
  )
  onMounted(() => document.addEventListener('keydown', handleKeydown))
  onBeforeUnmount(() => {
    document.removeEventListener('keydown', handleKeydown)
    disengage()
  })
}
