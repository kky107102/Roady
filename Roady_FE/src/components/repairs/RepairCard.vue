<script setup lang="ts">
import { computed } from 'vue'
import type { DamageListItem } from '@/types/damage'
import type { BadgeType } from '@/components/common/StatusBadge.vue'
import DamageThumbnail from '@/components/damages/DamageThumbnail.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const props = defineProps<{
  item: DamageListItem
  selected?: boolean
}>()

const emit = defineEmits<{ select: [id: number] }>()

const PRIORITY_LABELS: Record<string, string> = {
  URGENT: '긴급',
  HIGH: '높음',
  NORMAL: '보통',
  MEDIUM: '보통',
  LOW: '낮음',
}

const PRIORITY_BADGE_TYPES: Record<string, BadgeType> = {
  URGENT: 'danger',
  HIGH: 'warning',
  NORMAL: 'info',
  MEDIUM: 'info',
  LOW: 'neutral',
}

function formatCaseId(id: number, createdAt: string): string {
  const year = new Date(createdAt).getFullYear()
  return `RD-${year}-${String(id).padStart(6, '0')}`
}

const priorityLabel = computed(() => {
  const p = props.item.processingPriority
  if (!p) return '미지정'
  return PRIORITY_LABELS[p] ?? p
})

const priorityType = computed<BadgeType>(() => {
  const p = props.item.processingPriority
  return p ? (PRIORITY_BADGE_TYPES[p] ?? 'neutral') : 'neutral'
})

const repairStatus = computed<{ label: string; type: BadgeType }>(() => {
  switch (props.item.currentStatus) {
    case 'REQUESTED':
      return { label: '요청 전', type: 'warning' }
    case 'REPAIR_IN_PROGRESS':
      return { label: '요청 완료', type: 'info' }
    case 'REPAIR_COMPLETED':
      return { label: '보수 완료', type: 'success' }
    default:
      return { label: props.item.currentStatus, type: 'neutral' }
  }
})
</script>

<template>
  <button
    type="button"
    class="repair-card"
    :class="{ 'is-selected': selected }"
    :aria-pressed="selected"
    @click="emit('select', item.id)"
  >
    <DamageThumbnail :damage-id="item.id" :image-count="item.imageCount" />

    <div class="card-body">
      <div class="card-header">
        <span class="card-id">{{ formatCaseId(item.id, item.createdAt) }}</span>
        <StatusBadge :type="priorityType" :label="priorityLabel" />
      </div>

      <p class="card-desc">{{ item.description ?? '설명 없음' }}</p>

      <div class="card-footer">
        <StatusBadge :type="repairStatus.type" :label="repairStatus.label" />
      </div>
    </div>
  </button>
</template>

<style scoped>
.repair-card {
  display: flex;
  gap: 16px;
  width: calc(100% - 24px);
  min-height: 100px;
  margin: 0 12px 12px;
  padding: 16px;
  border: 1px solid var(--roady-border-default);
  border-radius: var(--roady-radius-list-card);
  background: var(--roady-surface-default);
  text-align: left;
  cursor: pointer;
  box-shadow: var(--roady-shadow-list-card);
  transition:
    border-color var(--roady-transition-fast),
    box-shadow var(--roady-transition-fast);
}

.repair-card:first-of-type {
  margin-top: 12px;
}

.repair-card:hover {
  border-color: color-mix(in srgb, var(--roady-brand-primary) 45%, var(--roady-border-default));
  box-shadow: var(--roady-shadow-list-card-hover);
}

.repair-card.is-selected {
  border: 2px solid var(--roady-brand-primary);
  padding: 15px;
  box-shadow: var(--roady-shadow-list-card-selected);
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.card-id {
  font-size: 13px;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-brand-secondary);
  font-family: monospace;
  flex-shrink: 0;
}

.card-desc {
  margin: 0;
  font-size: 18px;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: auto;
}

@media (prefers-reduced-motion: reduce) {
  .repair-card {
    transition: none;
  }
}
</style>
