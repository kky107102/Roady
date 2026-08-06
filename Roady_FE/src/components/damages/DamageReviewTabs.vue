<script setup lang="ts">
import type { ReviewTab } from '@/utils/damageReview'

defineProps<{ modelValue: ReviewTab }>()
const emit = defineEmits<{ 'update:modelValue': [ReviewTab] }>()

const tabs: Array<{ value: ReviewTab; label: string }> = [
  { value: 'pending', label: '미확인' },
  { value: 'confirmed', label: '확인' },
]

function select(value: ReviewTab) {
  emit('update:modelValue', value)
}

function handleKeydown(event: KeyboardEvent, index: number) {
  let nextIndex: number | null = null
  if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length
  if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length
  if (event.key === 'Home') nextIndex = 0
  if (event.key === 'End') nextIndex = tabs.length - 1
  if (nextIndex == null) return

  event.preventDefault()
  const tabElements = (event.currentTarget as HTMLElement).parentElement?.querySelectorAll<HTMLElement>(
    '[role="tab"]',
  )
  tabElements?.[nextIndex]?.focus()
  select(tabs[nextIndex]!.value)
}
</script>

<template>
  <div class="damage-review-tabs" role="tablist" aria-label="관리자 확인 여부">
    <button
      v-for="(tab, index) in tabs"
      :key="tab.value"
      type="button"
      role="tab"
      class="damage-review-tab"
      :class="{ 'is-active': modelValue === tab.value }"
      :aria-selected="modelValue === tab.value"
      :tabindex="modelValue === tab.value ? 0 : -1"
      @click="select(tab.value)"
      @keydown="handleKeydown($event, index)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<style scoped>
.damage-review-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--krds-number-3);
  padding: 0 var(--krds-number-8) var(--krds-number-5);
  background: var(--roady-surface-default);
}

.damage-review-tab {
  min-height: var(--krds-number-15);
  padding: 0 var(--krds-number-7);
  border: 0;
  border-bottom: var(--krds-number-2) solid transparent;
  border-radius: var(--roady-radius-control) var(--roady-radius-control) 0 0;
  color: var(--roady-text-tertiary);
  background: transparent;
  appearance: none;
  font: inherit;
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  cursor: pointer;
  transition:
    color var(--roady-transition-fast),
    background-color var(--roady-transition-fast),
    border-color var(--roady-transition-fast);
}

.damage-review-tab:hover:not(.is-active) {
  color: var(--roady-text-secondary);
  background: var(--roady-surface-subtle);
}

.damage-review-tab.is-active {
  border-bottom-color: var(--roady-brand-primary);
  color: var(--roady-brand-primary);
  background: var(--roady-brand-primary-subtle);
}

.damage-review-tab:focus {
  outline: none;
  box-shadow: none;
}

.damage-review-tab:focus-visible {
  position: relative;
  z-index: 1;
  outline: none;
  box-shadow: none;
  text-decoration: underline;
  text-decoration-thickness: var(--krds-number-1);
  text-underline-offset: var(--krds-number-2);
}
</style>
