<script setup lang="ts">
import { computed } from 'vue'
import type { ConfirmedStatusFilter } from '@/utils/damageReview'

const props = withDefaults(
  defineProps<{
    selected: ConfirmedStatusFilter[]
    counts: Partial<Record<ConfirmedStatusFilter, number>>
    ariaLabel?: string
    includeNoRepair?: boolean
  }>(),
  {
    ariaLabel: '처리 상태 필터',
    includeNoRepair: false,
  },
)

const emit = defineEmits<{
  'update:selected': [ConfirmedStatusFilter[]]
}>()

const repairStatuses: Array<{ value: ConfirmedStatusFilter; label: string }> = [
  { value: 'requested', label: '요청 전' },
  { value: 'in_progress', label: '요청 완료' },
  { value: 'completed', label: '보수 완료' },
]

const statuses = computed(() =>
  props.includeNoRepair
    ? [...repairStatuses, { value: 'not_required' as const, label: '보수 불필요' }]
    : repairStatuses,
)

function toggle(value: ConfirmedStatusFilter) {
  const selected = props.selected.includes(value)
    ? props.selected.filter((status) => status !== value)
    : statuses.value
        .map((status) => status.value)
        .filter((status) => status === value || props.selected.includes(status))

  emit('update:selected', selected.length === statuses.value.length ? [] : selected)
}
</script>

<template>
  <section class="status-filter" :aria-label="ariaLabel">
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
        <span>{{ status.label }} ({{ counts[status.value] ?? 0 }})</span>
      </button>
    </div>
    <div v-if="$slots.actions" class="status-filter-actions">
      <slot name="actions" />
    </div>
  </section>
</template>

<style scoped>
.status-filter {
  display: flex;
  align-items: center;
  gap: var(--krds-number-6);
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

.status-filter-chip:focus,
.status-filter-chip:active,
.status-filter-chip:focus-visible {
  outline: none;
  box-shadow: none;
  transform: none;
}

.status-filter-chip:focus-visible {
  text-decoration: underline;
  text-decoration-thickness: var(--krds-number-1);
  text-underline-offset: var(--krds-number-2);
}

.status-filter-actions {
  flex: 0 0 auto;
  margin-inline-start: auto;
}

@media (max-width: 48rem) {
  .status-filter {
    align-items: stretch;
    flex-direction: column;
  }

  .status-filter-actions {
    width: 100%;
    margin-inline-start: 0;
  }
}
</style>
