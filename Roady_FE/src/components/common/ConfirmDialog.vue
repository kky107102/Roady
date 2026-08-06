<script setup lang="ts">
import { ref, useId } from 'vue'
import { useDialogFocus } from '@/composables/useDialogFocus'

const props = withDefaults(
  defineProps<{
    title: string
    description?: string
    confirmLabel?: string
    cancelLabel?: string
    processingLabel?: string
    busy?: boolean
    tone?: 'primary' | 'danger'
  }>(),
  {
    description: '',
    confirmLabel: '확인',
    cancelLabel: '취소',
    processingLabel: '처리 중...',
    busy: false,
    tone: 'primary',
  },
)

const emit = defineEmits<{ cancel: []; confirm: [] }>()
const dialogRef = ref<HTMLElement | null>(null)
const titleId = useId()
const descriptionId = useId()

function cancel() {
  if (!props.busy) emit('cancel')
}

useDialogFocus(dialogRef, true, { onEscape: cancel })
</script>

<template>
  <Teleport to="body">
    <div
      ref="dialogRef"
      class="confirm-dialog__backdrop"
      role="alertdialog"
      aria-modal="true"
      tabindex="-1"
      :aria-labelledby="titleId"
      :aria-describedby="description ? descriptionId : undefined"
      @click.self="cancel"
    >
      <section class="confirm-dialog__panel">
        <span class="confirm-dialog__icon" aria-hidden="true">!</span>
        <div class="confirm-dialog__content">
          <h2 :id="titleId">{{ title }}</h2>
          <p v-if="description" :id="descriptionId">{{ description }}</p>
        </div>
        <div class="confirm-dialog__actions">
          <button
            type="button"
            class="krds-btn medium secondary"
            :disabled="busy"
            @click="cancel"
          >
            {{ cancelLabel }}
          </button>
          <button
            type="button"
            class="krds-btn medium filled"
            :class="tone"
            :disabled="busy"
            :aria-busy="busy || undefined"
            @click="emit('confirm')"
          >
            {{ busy ? processingLabel : confirmLabel }}
          </button>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.confirm-dialog__backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--roady-z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: var(--roady-overlay);
}

.confirm-dialog__panel {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 1.6rem;
  width: min(48rem, 100%);
  padding: 2.4rem;
  border-radius: var(--roady-radius-dialog);
  background: var(--roady-surface-default);
  box-shadow: var(--roady-shadow-dialog);
}

.confirm-dialog__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 4.4rem;
  height: 4.4rem;
  border-radius: 50%;
  color: var(--roady-status-warning-text);
  background: color-mix(in srgb, var(--roady-status-warning) 15%, var(--roady-surface-default));
  font-size: 2.2rem;
  font-weight: var(--krds-font-weight-bold);
}

.confirm-dialog__content h2 {
  margin: 0;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-heading-xsmall);
}

.confirm-dialog__content p {
  margin: 0.8rem 0 0;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-small);
  line-height: 1.6;
}

.confirm-dialog__actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.confirm-dialog__actions .krds-btn.danger {
  border-color: var(--roady-status-danger);
  color: var(--roady-surface-default);
  background: var(--roady-status-danger);
}

.confirm-dialog__actions .krds-btn.danger:hover:not(:disabled) {
  border-color: var(--roady-status-danger-hover);
  background: var(--roady-status-danger-hover);
}

@media (max-width: 36rem) {
  .confirm-dialog__panel {
    grid-template-columns: 1fr;
  }

  .confirm-dialog__actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}
</style>
