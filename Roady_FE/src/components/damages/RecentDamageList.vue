<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { damagesApi } from '@/api/damages'
import type { DamageListItem } from '@/types/damage'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { reviewTabForDamage } from '@/utils/damageReview'
import { formatPriorityLabel, priorityBadgeType } from '@/utils/repairRequest'
import { toApiFromDateTime, toApiToDateTime } from '@/utils/localDate'

const props = defineProps<{
  from?: string
  to?: string
  regionCode?: string
}>()

function formatDateTime(str: string | null): string {
  if (!str) return '-'
  const d = new Date(str)
  if (isNaN(d.getTime())) return str
  return d.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

const items = ref<DamageListItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
let loadSequence = 0

async function load() {
  const sequence = ++loadSequence
  loading.value = true
  error.value = null
  try {
    const res = await damagesApi.list({
      status: 'AI_ANALYZED',
      size: 5,
      ...(props.from ? { from: toApiFromDateTime(props.from) } : {}),
      ...(props.to ? { to: toApiToDateTime(props.to) } : {}),
      ...(props.regionCode ? { regionCode: props.regionCode } : {}),
    })
    if (sequence === loadSequence) items.value = res.content
  } catch {
    if (sequence === loadSequence) error.value = '목록을 불러오지 못했습니다.'
  } finally {
    if (sequence === loadSequence) loading.value = false
  }
}

watch(() => [props.from, props.to, props.regionCode], load, { immediate: true })
</script>

<template>
  <div class="recent-damage-list">
    <div class="rdl-content">
      <div v-if="loading" class="rdl-loading">
        <LoadingSpinner label="최근 탐지 불러오는 중" />
      </div>

      <div v-else-if="error" class="rdl-error" role="alert">
        {{ error }}
      </div>

      <EmptyState
        v-else-if="items.length === 0"
        class="rdl-empty"
        title="탐지된 사건이 없습니다"
      />

      <template v-else>
        <ul class="rdl-items" role="list">
          <li v-for="item in items" :key="item.id">
            <RouterLink
              :to="{
                name: 'damages',
                query: { review: reviewTabForDamage(item), damageId: String(item.id) },
              }"
              class="rdl-item"
              :aria-label="`탐지 사건 ${item.id} 상세보기`"
            >
              <div class="rdl-item-content">
                <p class="rdl-item-desc">{{ item.description ?? '설명 없음' }}</p>
                <time class="rdl-item-time" :datetime="item.capturedAt ?? item.createdAt">
                  {{ formatDateTime(item.capturedAt ?? item.createdAt) }}
                </time>
              </div>
              <StatusBadge
                :type="priorityBadgeType(item.repairPriority)"
                :label="formatPriorityLabel(item.repairPriority, '판단 보류')"
              />
            </RouterLink>
          </li>
        </ul>
      </template>
    </div>

    <div class="rdl-footer">
      <RouterLink :to="{ name: 'damages', query: { review: 'pending' } }" class="rdl-view-all">
        모두 보기 →
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.recent-damage-list {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  flex: 1;
  min-height: 0;
}

.rdl-content {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.rdl-loading {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  padding: 2rem 0;
}

.rdl-error {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  color: var(--roady-status-danger);
  font-size: var(--krds-pc-font-size-body-small);
  padding: 1rem 0;
}

.rdl-empty {
  flex: 1;
  justify-content: center;
  padding-block: 2rem;
}

.rdl-items {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
}

.rdl-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 1.2rem;
  padding: 1rem 1.2rem;
  color: inherit;
  text-decoration: none;
  transition: background-color 0.15s;
}

.rdl-items > li + li {
  border-top: 1px solid var(--roady-border-default);
}

.rdl-item:hover {
  background: var(--roady-surface-background);
}

.rdl-item:focus-visible {
  border-radius: 0.4rem;
  outline: 0.3rem solid var(--roady-brand-secondary);
  outline-offset: 0.2rem;
}

.rdl-item-content {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  min-width: 0;
}

.rdl-item-desc {
  margin: 0;
  font-size: var(--krds-pc-font-size-body-small);
  color: var(--roady-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rdl-item-time {
  font-size: var(--krds-pc-font-size-label-xsmall);
  color: var(--roady-text-tertiary);
}

.rdl-footer {
  padding-top: 1.2rem;
  text-align: center;
  border-top: 1px solid var(--roady-border-default);
}

.rdl-view-all {
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-brand-secondary);
  text-decoration: none;
}

.rdl-view-all:hover {
  text-decoration: underline;
}
</style>
