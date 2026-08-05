import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RouteLocationRaw } from 'vue-router'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastAction {
  label: string
  to?: RouteLocationRaw
  onClick?: () => void | Promise<void>
}

export interface Toast {
  id: number
  type: ToastType
  message: string
  duration: number
  actions?: ToastAction[]
}

let nextId = 1

export const useNotificationStore = defineStore('notification', () => {
  const toasts = ref<Toast[]>([])

  function addToast(
    type: ToastType,
    message: string,
    duration = 4000,
    actions?: ToastAction[],
  ) {
    const id = nextId++
    toasts.value.push({ id, type, message, duration, actions })

    if (duration > 0) {
      setTimeout(() => removeToast(id), duration)
    }

    return id
  }

  function removeToast(id: number) {
    const index = toasts.value.findIndex((t) => t.id === id)
    if (index !== -1) toasts.value.splice(index, 1)
  }

  const success = (message: string, duration?: number, actions?: ToastAction[]) =>
    addToast('success', message, duration, actions)
  const error = (message: string, duration?: number) => addToast('error', message, duration)
  const warning = (message: string, duration?: number) => addToast('warning', message, duration)
  const info = (message: string, duration?: number) => addToast('info', message, duration)

  return { toasts, addToast, removeToast, success, error, warning, info }
})
