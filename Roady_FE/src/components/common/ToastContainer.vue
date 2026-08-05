<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notification'
import type { Toast, ToastAction, ToastType } from '@/stores/notification'

const store = useNotificationStore()
const router = useRouter()

async function runAction(toast: Toast, action: ToastAction) {
  store.removeToast(toast.id)
  if (action.onClick) {
    await action.onClick()
  } else if (action.to) {
    await router.push(action.to)
  }
}

const icons: Record<ToastType, string> = {
  success: 'M20 6 9 17l-5-5',
  error: 'M18 6 6 18M6 6l12 12',
  warning:
    'M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z',
  info: 'M12 16v-4M12 8h.01M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z',
}
</script>

<template>
  <Teleport to="body">
    <div class="toast-region" role="region" aria-label="알림" aria-live="polite">
      <TransitionGroup name="toast" tag="ul" class="toast-list">
        <li
          v-for="toast in store.toasts"
          :key="toast.id"
          class="toast-item"
          :class="`is-${toast.type}`"
          role="alert"
        >
          <svg
            class="toast-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path :d="icons[toast.type]" />
          </svg>
          <div class="toast-content">
            <span class="toast-message">{{ toast.message }}</span>
            <div v-if="toast.actions?.length" class="toast-actions">
              <button
                v-for="action in toast.actions"
                :key="action.label"
                type="button"
                class="toast-action"
                @click="runAction(toast, action)"
              >
                {{ action.label }}
              </button>
            </div>
          </div>
          <button
            type="button"
            class="toast-close"
            :aria-label="`알림 닫기: ${toast.message}`"
            @click="store.removeToast(toast.id)"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.2"
              stroke-linecap="round"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </li>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-region {
  position: fixed;
  top: 13.6rem;
  right: 2.4rem;
  z-index: 9000;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  pointer-events: none;
}

@media (max-width: 768px) {
  .toast-region {
    top: 11.2rem;
    right: 1.6rem;
    left: 1.6rem;
  }

  .toast-item {
    width: 100%;
  }
}

.toast-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.toast-item {
  display: flex;
  align-items: flex-start;
  gap: 1.2rem;
  width: 36rem;
  padding: 1.4rem 1.6rem;
  border: 0.1rem solid rgb(15 23 42 / 10%);
  border-left-width: 0.4rem;
  border-radius: 0.6rem;
  background: var(--roady-surface-default);
  box-shadow:
    0 0.8rem 2.4rem rgb(15 23 42 / 18%),
    0 0.2rem 0.6rem rgb(15 23 42 / 10%);
  pointer-events: auto;
}

.toast-item.is-success {
  border-left-color: var(--roady-status-success);
}

.toast-item.is-error {
  border-left-color: var(--roady-status-danger);
}

.toast-item.is-warning {
  border-left-color: var(--roady-status-warning);
}

.toast-item.is-info {
  border-left-color: var(--roady-brand-secondary);
}

.toast-icon {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  margin-top: 0.1rem;
}

.is-success .toast-icon {
  color: var(--roady-status-success);
}

.is-error .toast-icon {
  color: var(--roady-status-danger);
}

.is-warning .toast-icon {
  color: var(--roady-status-warning);
}

.is-info .toast-icon {
  color: var(--roady-brand-secondary);
}

.toast-message {
  display: block;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-body-small);
  line-height: 1.6;
  word-break: keep-all;
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-actions {
  display: flex;
  flex-wrap: wrap;
  column-gap: 1.6rem;
  row-gap: 0.8rem;
  margin-top: 0.8rem;
}

.toast-action {
  padding: 0.2rem 0;
  border: 0;
  border-bottom: 1px solid currentColor;
  background: transparent;
  color: var(--roady-brand-secondary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  cursor: pointer;
}

.toast-close {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  border: none;
  border-radius: 0.4rem;
  color: var(--roady-text-tertiary);
  background: transparent;
  cursor: pointer;
  transition:
    color 0.15s,
    background-color 0.15s;
}

.toast-close:hover {
  color: var(--roady-text-primary);
  background: var(--roady-surface-hover);
}

.toast-close:focus-visible {
  outline: 0.3rem solid var(--roady-focus-ring);
  outline-offset: 0.1rem;
}

.toast-close svg {
  width: 1.4rem;
  height: 1.4rem;
}

/* TransitionGroup animations */
.toast-enter-active {
  transition:
    transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1),
    opacity 0.2s ease;
}

.toast-leave-active {
  transition:
    transform 0.2s ease,
    opacity 0.2s ease;
  position: absolute;
}

.toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.toast-move {
  transition: transform 0.25s ease;
}
</style>
