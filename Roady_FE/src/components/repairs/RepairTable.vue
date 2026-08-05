<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import type { DamageListItem } from '@/types/damage'
import StatusBadge from '@/components/common/StatusBadge.vue'
import RepairStatusBadge from './RepairStatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { formatCaseId, formatPriorityLabel, priorityBadgeType } from '@/utils/repairRequest'

const props = defineProps<{
  items: DamageListItem[]
  loading?: boolean
  error?: string | null
  emptyTitle?: string
  emptyDescription?: string
}>()

const emit = defineEmits<{ retry: [] }>()

const route = useRoute()

function formatDateTime(str: string | null | undefined): string {
  if (!str) return '-'
  const d = new Date(str)
  if (isNaN(d.getTime())) return '-'
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(d)
}

function detailLinkTo(item: DamageListItem) {
  return {
    name: 'repair-detail',
    params: { damageId: item.id },
    query: { backTo: route.fullPath },
  }
}

const showEmpty = computed(() => !props.loading && !props.error && props.items.length === 0)
</script>

<template>
  <div class="repair-table-wrap">
    <table class="repair-table" aria-label="보수 관리 사건 목록">
      <thead>
        <tr>
          <th class="col-priority" scope="col">우선순위</th>
          <th class="col-case-id" scope="col">사건번호</th>
          <th class="col-name" scope="col">사건명</th>
          <th class="col-status" scope="col">현재 상태</th>
          <th class="col-date" scope="col">최근 변경일</th>
        </tr>
      </thead>
      <tbody>
        <!-- 로딩 -->
        <tr v-if="loading" class="state-row">
          <td colspan="5">
            <div class="state-cell">
              <LoadingSpinner label="목록 불러오는 중" />
            </div>
          </td>
        </tr>

        <!-- 오류 -->
        <tr v-else-if="error" class="state-row">
          <td colspan="5">
            <div class="state-cell">
              <ErrorState :message="error" @retry="emit('retry')" />
            </div>
          </td>
        </tr>

        <!-- 빈 결과 -->
        <tr v-else-if="showEmpty" class="state-row">
          <td colspan="5">
            <div class="state-cell">
              <EmptyState
                :title="emptyTitle ?? '조회된 사건이 없습니다'"
                :description="emptyDescription ?? '조회 조건을 변경해 보세요.'"
              />
            </div>
          </td>
        </tr>

        <!-- 데이터 행 -->
        <tr v-else v-for="item in items" :key="item.id" class="data-row">
          <td class="col-priority">
            <StatusBadge
              :type="priorityBadgeType(item.processingPriority)"
              :label="formatPriorityLabel(item.processingPriority, '미지정')"
            />
          </td>
          <td class="col-case-id">
            <span class="case-id-text">{{ formatCaseId(item.id, item.createdAt) }}</span>
          </td>
          <td class="col-name">
            <RouterLink
              :to="detailLinkTo(item)"
              class="case-link"
              :aria-label="`${item.description ?? '설명 없음'} 상세 보기`"
            >
              {{ item.description ?? '설명 없음' }}
            </RouterLink>
          </td>
          <td class="col-status">
            <RepairStatusBadge :status="item.currentStatus" />
          </td>
          <td class="col-date">
            {{ formatDateTime(item.updatedAt ?? item.createdAt) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.repair-table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--roady-border-default);
  border-radius: 8px;
  background: var(--roady-surface-default);
}

.repair-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  color: var(--roady-text-primary);
}

/* ── 헤더 ── */
.repair-table thead tr {
  border-bottom: 2px solid var(--roady-border-default);
  background: var(--roady-surface-background);
}

.repair-table th {
  padding: 12px 16px;
  font-weight: var(--krds-font-weight-bold);
  font-size: 13px;
  color: var(--roady-text-secondary);
  text-align: left;
  white-space: nowrap;
}

/* ── 데이터 행 ── */
.data-row {
  border-bottom: 1px solid var(--roady-border-default);
  transition: background-color 0.1s;
}

.data-row:last-child {
  border-bottom: none;
}

.data-row:hover {
  background: var(--roady-surface-background);
}

.repair-table td {
  padding: 12px 16px;
  vertical-align: middle;
}

/* ── 컬럼 너비 ── */
.col-priority {
  width: 96px;
  flex-shrink: 0;
}

.col-case-id {
  width: 160px;
  flex-shrink: 0;
}

.col-name {
  min-width: 200px;
}

.col-status {
  width: 110px;
  flex-shrink: 0;
}

.col-date {
  width: 160px;
  flex-shrink: 0;
  color: var(--roady-text-tertiary);
  white-space: nowrap;
}

/* ── 셀 내용 ── */
.case-id-text {
  font-size: 12px;
  font-family: monospace;
  color: var(--roady-brand-secondary);
  font-weight: var(--krds-font-weight-bold);
  white-space: nowrap;
}

.case-link {
  color: var(--roady-text-primary);
  font-weight: var(--krds-font-weight-bold);
  text-decoration: underline;
  text-decoration-color: transparent;
  text-underline-offset: 2px;
  transition: color 0.1s, text-decoration-color 0.1s;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.case-link:hover {
  color: var(--roady-brand-primary);
  text-decoration-color: var(--roady-brand-primary);
}

.case-link:focus-visible {
  outline: 2px solid var(--roady-focus-ring);
  outline-offset: 2px;
  border-radius: 2px;
}

/* ── 상태 행 (로딩/오류/빈 결과) ── */
.state-row td {
  padding: 0;
}

.state-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 4rem 2rem;
  min-height: 200px;
}

/* ── 반응형 ── */
@media (max-width: 768px) {
  .col-date {
    display: none;
  }
}

@media (max-width: 560px) {
  .col-case-id {
    display: none;
  }

  .repair-table th,
  .repair-table td {
    padding: 10px 12px;
  }
}
</style>
