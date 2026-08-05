<script setup lang="ts">
import { computed } from 'vue'
import type { DamageListItem } from '@/types/damage'
import DamageThumbnail from './DamageThumbnail.vue'
import AiResultBadge from '@/components/common/AiResultBadge.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { isReviewConfirmed } from '@/utils/damageReview'
import { formatCaseId, formatPriorityLabel, priorityBadgeType } from '@/utils/repairRequest'
import { repairStatusInfo } from '@/utils/repairManagement'

const props = defineProps<{
  item: DamageListItem
  selected?: boolean
}>()

const emit = defineEmits<{ select: [id: number] }>()

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

function formatLocation(item: DamageListItem): string {
  const address = item.roadAddressName?.trim() || item.addressName?.trim()
  if (address) return `${address} 주변`
  return formatCoords(item.latitude, item.longitude)
}

const confirmed = computed(() => isReviewConfirmed(props.item))

const displayedPriority = computed(() =>
  confirmed.value ? (props.item.processingPriority ?? null) : (props.item.repairPriority ?? null),
)

const confirmedStatus = computed(() => {
  const status = props.item.currentStatus
  if (status === 'REQUESTED' || status === 'REPAIR_IN_PROGRESS' || status === 'REPAIR_COMPLETED')
    return repairStatusInfo(status)
  return { label: '보수 불필요', type: 'neutral' as const }
})
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
        <AiResultBadge
          v-if="!confirmed"
          :type="priorityBadgeType(displayedPriority)"
          :label="formatPriorityLabel(displayedPriority, confirmed ? '미지정' : '보류')"
        />
        <StatusBadge
          v-else
          :type="priorityBadgeType(displayedPriority)"
          :label="formatPriorityLabel(displayedPriority, confirmed ? '미지정' : '보류')"
        />
      </div>

      <p class="card-desc">{{ item.description ?? '설명 없음' }}</p>

      <p class="card-location">{{ formatLocation(item) }}</p>

      <div class="card-footer">
        <time class="card-time" :datetime="(item.capturedAt ?? item.createdAt) || undefined">
          {{ formatDate(item.capturedAt ?? item.createdAt) }} 탐지
        </time>
        <StatusBadge
          v-if="confirmed"
          class="confirmed-status"
          :type="confirmedStatus.type"
          :label="confirmedStatus.label"
        />
      </div>
    </div>
  </button>
</template>

<style scoped>
.damage-card {
  display: flex;
  gap: 16px;
  width: calc(100% - 24px);
  min-height: 132px;
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

.damage-card:first-of-type {
  margin-top: 12px;
}

.damage-card:hover {
  border-color: color-mix(in srgb, var(--roady-brand-primary) 45%, var(--roady-border-default));
  box-shadow: var(--roady-shadow-list-card-hover);
}

.damage-card.is-selected {
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

.card-location {
  margin: 0;
  font-size: 13px;
  color: var(--roady-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: auto;
}

.card-time {
  font-size: 13px;
  color: var(--roady-text-tertiary);
  font-weight: var(--krds-font-weight-bold);
}

.confirmed-status {
  flex-shrink: 0;
}

@media (prefers-reduced-motion: reduce) {
  .damage-card {
    transition: none;
  }
}
</style>
