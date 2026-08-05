<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { DamageListItem } from '@/types/damage'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const props = defineProps<{
  items: DamageListItem[]
}>()

const displayedItems = computed(() => props.items.slice(0, 5))

function formatDateTime(value: string | null): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}
</script>

<template>
  <div class="urgent-damage-list">
    <EmptyState
      v-if="displayedItems.length === 0"
      title="긴급 확인이 필요한 사건이 없습니다"
      description="AI가 긴급으로 판단한 미확인 사건이 여기에 표시됩니다."
    />

    <ul v-else class="udl-items" role="list">
      <li v-for="item in displayedItems" :key="item.id">
        <RouterLink
          :to="{
            name: 'damages',
            query: { review: 'pending', sort: 'priority', damageId: String(item.id) },
          }"
          class="udl-item"
          :aria-label="`긴급 사건 ${item.id} 상세보기`"
        >
          <div class="udl-item-content">
            <p class="udl-item-desc">{{ item.description ?? '설명 없음' }}</p>
            <time class="udl-item-time" :datetime="item.capturedAt ?? item.createdAt">
              {{ formatDateTime(item.capturedAt ?? item.createdAt) }}
            </time>
          </div>
          <StatusBadge type="danger" label="긴급" />
        </RouterLink>
      </li>
    </ul>

    <div class="udl-footer">
      <RouterLink
        :to="{ name: 'damages', query: { review: 'pending', sort: 'priority' } }"
        class="udl-view-all"
      >
        우선순위 순으로 모두 보기 →
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.urgent-damage-list {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
}

.udl-items {
  flex: 1;
  margin: 0;
  padding: 0;
  list-style: none;
}

.udl-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 1.2rem;
  padding: 1rem 1.2rem;
  color: inherit;
  text-decoration: none;
  transition: background-color 0.15s;
}

.udl-items > li + li {
  border-top: 1px solid var(--roady-border-default);
}

.udl-item:hover {
  background: var(--roady-surface-background);
}

.udl-item:focus-visible {
  border-radius: 0.4rem;
  outline: 0.3rem solid var(--roady-brand-secondary);
  outline-offset: 0.2rem;
}

.udl-item-content {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  min-width: 0;
}

.udl-item-desc {
  overflow: hidden;
  margin: 0;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-body-small);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.udl-item-time {
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-label-xsmall);
}

.udl-footer {
  padding-top: 1.2rem;
  border-top: 1px solid var(--roady-border-default);
  text-align: center;
}

.udl-view-all {
  color: var(--roady-brand-secondary);
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  text-decoration: none;
}

.udl-view-all:hover {
  text-decoration: underline;
}
</style>
