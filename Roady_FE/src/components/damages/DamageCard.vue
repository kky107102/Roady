<script setup lang="ts">
import type { DamageListItem, DamageStatus } from '@/types/damage'
import type { BadgeType } from '@/components/common/StatusBadge.vue'
import DamageThumbnail from './DamageThumbnail.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const props = defineProps<{
  item: DamageListItem
  selected?: boolean
}>()

const emit = defineEmits<{ select: [id: number] }>()

const STATUS_LABELS: Record<DamageStatus, string> = {
  COLLECTED: '탐지됨',
  REVIEW_REQUIRED: '검토 필요',
  RECEIVED: '접수됨',
  REPAIR_SCHEDULED: '보수 예정',
  REPAIRING: '보수 중',
  REPAIR_COMPLETED: '보수 완료',
  REPAIR_NOT_REQUIRED: '보수 불필요',
}

const STATUS_BADGE_TYPES: Record<DamageStatus, BadgeType> = {
  COLLECTED: 'neutral',
  REVIEW_REQUIRED: 'warning',
  RECEIVED: 'info',
  REPAIR_SCHEDULED: 'info',
  REPAIRING: 'warning',
  REPAIR_COMPLETED: 'success',
  REPAIR_NOT_REQUIRED: 'neutral',
}

const PRIORITY_LABELS: Record<string, string> = {
  URGENT: '긴급',
  HIGH: '주의',
  MEDIUM: '보통',
  LOW: '낮음',
}

const PRIORITY_BADGE_TYPES: Record<string, BadgeType> = {
  URGENT: 'danger',
  HIGH: 'warning',
  MEDIUM: 'info',
  LOW: 'neutral',
}

function formatCaseId(id: number, createdAt: string): string {
  const year = new Date(createdAt).getFullYear()
  return `RD-${year}-${String(id).padStart(6, '0')}`
}

function formatDate(str: string | null): string {
  if (!str) return '-'
  const d = new Date(str)
  if (isNaN(d.getTime())) return str
  return d.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

function formatCoords(lat: number | null, lng: number | null): string {
  if (lat == null || lng == null) return '위치 정보 없음'
  return `위도 ${lat.toFixed(4)}, 경도 ${lng.toFixed(4)}`
}
</script>

<template>
  <button
    type="button"
    class="damage-card"
    :class="{ 'is-selected': selected }"
    :aria-pressed="selected"
    @click="emit('select', item.id)"
  >
    <DamageThumbnail :damage-id="item.id" :image-count="item.imageCount" />

    <div class="card-body">
      <div class="card-header">
        <span class="card-id">{{ formatCaseId(item.id, item.createdAt) }}</span>
        <StatusBadge
          v-if="item.repairPriority"
          :type="PRIORITY_BADGE_TYPES[item.repairPriority] ?? 'neutral'"
          :label="PRIORITY_LABELS[item.repairPriority] ?? item.repairPriority"
        />
      </div>

      <p class="card-desc">{{ item.description ?? '설명 없음' }}</p>

      <p class="card-location">{{ formatCoords(item.latitude, item.longitude) }}</p>

      <div class="card-footer">
        <time class="card-time" :datetime="(item.capturedAt ?? item.createdAt) || undefined">
          {{ formatDate(item.capturedAt ?? item.createdAt) }} 탐지
        </time>
        <StatusBadge
          :type="STATUS_BADGE_TYPES[item.currentStatus]"
          :label="STATUS_LABELS[item.currentStatus]"
        />
      </div>
    </div>
  </button>
</template>

<style scoped>
.damage-card {
  display: flex;
  gap: 1.2rem;
  width: 100%;
  padding: 1.2rem 1.6rem;
  border: none;
  border-bottom: 1px solid var(--roady-border-default);
  background: var(--roady-surface-default);
  text-align: left;
  cursor: pointer;
  transition: background-color 0.12s;
}

.damage-card:hover {
  background: var(--roady-surface-background);
}

.damage-card.is-selected {
  background: color-mix(in srgb, var(--roady-brand-secondary) 8%, transparent);
  border-left: 3px solid var(--roady-brand-secondary);
  padding-left: calc(1.6rem - 3px);
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  min-width: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
}

.card-id {
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-brand-secondary);
  font-family: monospace;
  flex-shrink: 0;
}

.card-desc {
  margin: 0;
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-location {
  margin: 0;
  font-size: var(--krds-pc-font-size-label-xsmall);
  color: var(--roady-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
}

.card-time {
  font-size: var(--krds-pc-font-size-label-xsmall);
  color: var(--roady-text-tertiary);
}
</style>
