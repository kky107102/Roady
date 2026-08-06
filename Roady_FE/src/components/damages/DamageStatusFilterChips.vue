<script setup lang="ts">
import type { ConfirmedStatusFilter } from '@/utils/damageReview'

const props = defineProps<{
  selected: ConfirmedStatusFilter[]
  counts: Record<ConfirmedStatusFilter, number>
}>()

const emit = defineEmits<{
  'update:selected': [ConfirmedStatusFilter[]]
}>()

const statuses: Array<{ value: ConfirmedStatusFilter; label: string }> = [
  { value: 'requested', label: '요청 전' },
  { value: 'in_progress', label: '요청 완료' },
  { value: 'completed', label: '보수 완료' },
]

function toggle(value: ConfirmedStatusFilter) {
  const selected = props.selected.includes(value)
    ? props.selected.filter((status) => status !== value)
    : statuses
        .map((status) => status.value)
        .filter((status) => status === value || props.selected.includes(status))

  emit('update:selected', selected.length === statuses.length ? [] : selected)
}
</script>

<template>
  <section class="status-filter" aria-label="처리 상태 필터">
    <div class="status-filter-chips" role="group">
      <button
        v-for="status in statuses"
        :key="status.value"
        type="button"
        class="status-filter-chip"
        :class="{ 'is-active': selected.includes(status.value) }"
        :aria-pressed="selected.includes(status.value)"
        @click="toggle(status.value)"
      >
        <span>{{ status.label }} ({{ counts[status.value] }})</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.status-filter {
  display: flex;
  align-items: center;
  padding: var(--krds-number-5) var(--krds-number-8);
  border-bottom: var(--krds-number-1) solid var(--roady-border-default);
  background: var(--roady-surface-background);
}

.status-filter-chips {
  display: flex;
  flex: 1;
  flex-wrap: wrap;
  gap: var(--krds-number-3);
  min-width: 0;
}

.status-filter-chip {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  block-size: var(--krds-number-11);
  min-block-size: var(--krds-number-11);
  max-block-size: var(--krds-number-11);
  padding: var(--krds-number-2) var(--krds-number-5);
  border: var(--krds-number-1) solid transparent;
  border-radius: var(--roady-radius-control);
  overflow: hidden;
  color: var(--roady-text-secondary);
  background: var(--roady-surface-default);
  appearance: none;
  font: inherit;
  font-size: var(--krds-pc-font-size-label-xsmall);
  font-weight: var(--krds-font-weight-bold);
  white-space: nowrap;
  box-shadow: none;
  transform: none;
  cursor: pointer;
  transition:
    color var(--roady-transition-fast),
    background-color var(--roady-transition-fast);
}

.status-filter-chip:hover:not(.is-active) {
  background: var(--roady-surface-subtle);
}

.status-filter-chip.is-active {
  border-color: transparent;
  color: var(--krds-light-color-button-primary-text);
  background: var(--roady-brand-primary);
}

.status-filter-chip:focus {
  outline: none;
}

.status-filter-chip:active {
  box-shadow: none;
  transform: none;
}

.status-filter-chip:focus-visible {
  outline: none;
  box-shadow: none;
  text-decoration: underline;
  text-decoration-thickness: var(--krds-number-1);
  text-underline-offset: var(--krds-number-2);
}

</style>
