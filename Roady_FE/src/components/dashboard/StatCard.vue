<script setup lang="ts">
interface Props {
  label: string
  count: number | null
  subText?: string
  variant?: 'default' | 'danger' | 'dark'
}

withDefaults(defineProps<Props>(), {
  subText: '',
  variant: 'default',
})
</script>

<template>
  <div class="stat-card" :class="`is-${variant}`">
    <div class="stat-card__header">
      <span class="stat-card__label">{{ label }}</span>
      <span class="stat-card__icon" aria-hidden="true">
        <slot name="icon" />
      </span>
    </div>
    <div class="stat-card__body">
      <span v-if="count !== null" class="stat-card__count">{{ count.toLocaleString() }}</span>
      <span v-else class="stat-card__count is-loading" aria-busy="true">—</span>
      <span v-if="subText" class="stat-card__sub">{{ subText }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  padding: 2rem 2.4rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-default);
}

.stat-card.is-dark {
  border-color: var(--roady-brand-primary);
  background: var(--roady-brand-primary);
}

.stat-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-card__label {
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
}

.is-dark .stat-card__label {
  color: rgb(255 255 255 / 70%);
}

.stat-card__icon {
  display: flex;
  align-items: center;
  color: var(--roady-text-tertiary);
}

.is-dark .stat-card__icon {
  color: rgb(255 255 255 / 50%);
}

.stat-card__body {
  display: flex;
  align-items: baseline;
  gap: 0.8rem;
}

.stat-card__count {
  color: var(--roady-text-primary);
  font-size: 3.6rem;
  font-weight: var(--krds-font-weight-bold);
  line-height: 1;
  letter-spacing: -0.02em;
}

.stat-card__count.is-loading {
  color: var(--roady-text-tertiary);
}

.is-danger .stat-card__count {
  color: var(--roady-status-danger);
}

.is-dark .stat-card__count {
  color: #fff;
}

.stat-card__sub {
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
}

.is-dark .stat-card__sub {
  color: rgb(255 255 255 / 60%);
}
</style>
