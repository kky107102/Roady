<script setup lang="ts">
import type { BadgeType } from './StatusBadge.vue'
import StatusBadge from './StatusBadge.vue'

withDefaults(
  defineProps<{
    type: BadgeType
    label: string
    size?: 'small' | 'medium' | 'large'
  }>(),
  {
    size: 'small',
  },
)
</script>

<template>
  <span class="ai-result-badge-pair" :aria-label="`AI 판독 결과: ${label}`">
    <span class="ai-result-source">AI 판독</span>
    <StatusBadge :type="type" :label="label" :size="size" />
  </span>
</template>

<style scoped>
.ai-result-badge-pair {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
  white-space: nowrap;
}

.ai-result-source {
  padding-right: 0.7rem;
  border-right: 1px solid var(--roady-border-default);
  color: var(--roady-brand-secondary);
  font-size: var(--krds-pc-font-size-label-xsmall);
  font-weight: var(--krds-font-weight-bold);
  line-height: 1.4;
}
</style>
