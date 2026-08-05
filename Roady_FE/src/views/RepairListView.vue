<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { damagesApi } from '@/api/damages'
import type { DamageListQuery } from '@/api/damages'
import type { DamageListItem } from '@/types/damage'
import PageFilterToolbar from '@/components/common/PageFilterToolbar.vue'
import DateRangeFilter from '@/components/common/DateRangeFilter.vue'
import KrdsCheckbox from '@/components/common/KrdsCheckbox.vue'
import RepairTable from '@/components/repairs/RepairTable.vue'
import {
  dateRangeForPreset,
  matchingDateRangePreset,
  toApiFromDateTime,
  toApiToDateTime,
} from '@/utils/localDate'
import {
  repairStatusCategory,
  sortRepairItems,
  parseStatusesParam,
  statusesToParam,
  parseSortParam,
  REPAIR_STATUS_FILTERS,
  REPAIR_FILTER_LABELS,
  REPAIR_SORT_OPTIONS,
} from '@/utils/repairManagement'
import type { RepairStatusFilter, RepairSort } from '@/utils/repairManagement'

// ── 라우터 ──────────────────────────────────────────────────
const route = useRoute()
const router = useRouter()

// ── URL → 적용 필터 (단일 진실 소스) ──────────────────────
const defaultDateRange = dateRangeForPreset(1)
const appliedFrom = computed(() => String(route.query.from || defaultDateRange.from))
const appliedTo = computed(() => String(route.query.to || defaultDateRange.to))

function normalizeQueryValue(v: unknown): string | string[] | undefined {
  if (v == null) return undefined
  if (typeof v === 'string') return v
  if (Array.isArray(v)) return (v as (string | null)[]).filter((s): s is string => s != null)
  return undefined
}

const activeStatuses = computed(() => parseStatusesParam(normalizeQueryValue(route.query.statuses)))
const activeSort = computed(() => parseSortParam(normalizeQueryValue(route.query.sort)))

// ── 폼 상태 (미적용 날짜 입력값) ─────────────────────────
const formFrom = ref(appliedFrom.value)
const formTo = ref(appliedTo.value)
const formError = ref('')
const activePreset = ref<number | null>(
  matchingDateRangePreset(appliedFrom.value, appliedTo.value),
)

watch([appliedFrom, appliedTo], ([from, to]) => {
  formFrom.value = from
  formTo.value = to
  formError.value = ''
  activePreset.value = matchingDateRangePreset(from, to)
})

// ── 데이터 ─────────────────────────────────────────────────
const allItems = ref<DamageListItem[]>([])
const loading = ref(false)
const fetchError = ref<string | null>(null)
let fetchSeq = 0

async function fetchAllPages(
  query: Omit<DamageListQuery, 'page' | 'size'>,
): Promise<DamageListItem[]> {
  const firstPage = await damagesApi.list({ ...query, page: 0, size: 100 })
  if (firstPage.totalPages <= 1) return firstPage.content

  const remainingPages = await Promise.all(
    Array.from({ length: firstPage.totalPages - 1 }, (_, index) =>
      damagesApi.list({ ...query, page: index + 1, size: 100 }),
    ),
  )

  return [firstPage, ...remainingPages].flatMap((page) => page.content)
}

async function fetchItems() {
  const seq = ++fetchSeq
  loading.value = true
  fetchError.value = null
  try {
    const base = {
      ...(appliedFrom.value ? { from: toApiFromDateTime(appliedFrom.value) } : {}),
      ...(appliedTo.value ? { to: toApiToDateTime(appliedTo.value) } : {}),
    }
    const [req, inProg, done] = await Promise.all([
      fetchAllPages({ ...base, status: 'REQUESTED' }),
      fetchAllPages({ ...base, status: 'REPAIR_IN_PROGRESS' }),
      fetchAllPages({ ...base, status: 'REPAIR_COMPLETED' }),
    ])
    if (seq !== fetchSeq) return
    allItems.value = [...req, ...inProg, ...done]
  } catch {
    if (seq !== fetchSeq) return
    fetchError.value = '목록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    if (seq === fetchSeq) loading.value = false
  }
}

watch([appliedFrom, appliedTo], fetchItems, { immediate: true })

// ── 파생 데이터 ──────────────────────────────────────────
const statusCounts = computed(() => {
  const counts: Record<RepairStatusFilter, number> = {
    requested: 0,
    in_progress: 0,
    completed: 0,
  }
  for (const item of allItems.value) {
    const cat = repairStatusCategory(item)
    if (cat) counts[cat]++
  }
  return counts
})

const displayedItems = computed(() => {
  const filtered = allItems.value.filter((item) => {
    const cat = repairStatusCategory(item)
    return cat != null && activeStatuses.value.includes(cat)
  })
  return sortRepairItems(filtered, activeSort.value)
})

const totalCount = computed(() => allItems.value.length)

// ── URL 쿼리 빌더 ─────────────────────────────────────────
function buildQuery(overrides: Record<string, string | undefined> = {}): Record<string, string> {
  const base: Record<string, string | undefined> = {}
  if (appliedFrom.value) base.from = appliedFrom.value
  if (appliedTo.value) base.to = appliedTo.value
  const statusParam = statusesToParam(activeStatuses.value)
  if (statusParam) base.statuses = statusParam
  if (activeSort.value !== 'priority') base.sort = activeSort.value
  const merged = { ...base, ...overrides }
  return Object.fromEntries(
    Object.entries(merged).filter((entry): entry is [string, string] => entry[1] != null),
  )
}

// ── 상태 필터 조작 ────────────────────────────────────────
function setStatuses(next: RepairStatusFilter[]) {
  const param = statusesToParam(next)
  router.replace({ query: buildQuery({ statuses: param }) })
}

function toggleStatus(filter: RepairStatusFilter, checked: boolean) {
  const current = activeStatuses.value
  if (checked) {
    if (!current.includes(filter)) setStatuses([...current, filter])
  } else {
    setStatuses(current.filter((s) => s !== filter))
  }
}

const isAllSelected = computed(() => activeStatuses.value.length === REPAIR_STATUS_FILTERS.length)

const allChecked = computed({
  get: () => isAllSelected.value,
  set: (v: boolean) => setStatuses(v ? [...REPAIR_STATUS_FILTERS] : []),
})

const requestedChecked = computed({
  get: () => activeStatuses.value.includes('requested'),
  set: (v: boolean) => toggleStatus('requested', v),
})

const inProgressChecked = computed({
  get: () => activeStatuses.value.includes('in_progress'),
  set: (v: boolean) => toggleStatus('in_progress', v),
})

const completedChecked = computed({
  get: () => activeStatuses.value.includes('completed'),
  set: (v: boolean) => toggleStatus('completed', v),
})

// ── 정렬 ────────────────────────────────────────────────
function handleSortChange(event: Event) {
  const val = (event.target as HTMLSelectElement).value as RepairSort
  const q = buildQuery({ sort: val !== 'priority' ? val : undefined })
  router.replace({ query: q })
}

// ── 날짜 필터 핸들러 ─────────────────────────────────────
function handleSearch() {
  formError.value = ''
  if (formFrom.value && formTo.value && formFrom.value > formTo.value) {
    formError.value = '시작일은 종료일보다 이전이어야 합니다.'
    return
  }
  router.push({
    query: buildQuery({
      from: formFrom.value || undefined,
      to: formTo.value || undefined,
    }),
  })
}

function handleReset() {
  const range = dateRangeForPreset(1)
  formFrom.value = range.from
  formTo.value = range.to
  activePreset.value = 1
  formError.value = ''
  router.push({ query: buildQuery(range) })
}

function handlePresetApply({ from, to }: { from: string; to: string }) {
  formFrom.value = from
  formTo.value = to
  handleSearch()
}
</script>

<template>
  <div class="repair-view">
    <!-- 상단 날짜 필터 툴바 -->
    <PageFilterToolbar aria-label="보수 사건 조회 조건" @submit="handleSearch">
      <DateRangeFilter
        :from="formFrom"
        :to="formTo"
        :active-preset="activePreset"
        :error="formError"
        @update:from="formFrom = $event"
        @update:to="formTo = $event"
        @update:active-preset="activePreset = $event"
        @preset-apply="handlePresetApply"
      />
      <template #actions>
        <button type="button" class="krds-btn small secondary" @click="handleReset">초기화</button>
        <button type="submit" class="krds-btn small filled primary">
          조회
        </button>
      </template>
    </PageFilterToolbar>

    <!-- 본문 -->
    <div class="repair-body">
      <!-- 목록 헤더: 상태 필터 + 정렬 -->
      <div class="list-header">
        <!-- 인라인 상태 체크박스 필터 -->
        <fieldset class="status-filters" aria-label="보수 상태 필터">
          <legend class="sr-only">보수 상태 필터</legend>
          <KrdsCheckbox
            id="repair-filter-all"
            v-model="allChecked"
            :label="`전체 (${totalCount}건)`"
          />
          <KrdsCheckbox
            id="repair-filter-requested"
            v-model="requestedChecked"
            :label="`${REPAIR_FILTER_LABELS.requested} (${statusCounts.requested}건)`"
          />
          <KrdsCheckbox
            id="repair-filter-in-progress"
            v-model="inProgressChecked"
            :label="`${REPAIR_FILTER_LABELS.in_progress} (${statusCounts.in_progress}건)`"
          />
          <KrdsCheckbox
            id="repair-filter-completed"
            v-model="completedChecked"
            :label="`${REPAIR_FILTER_LABELS.completed} (${statusCounts.completed}건)`"
          />
        </fieldset>

        <!-- 정렬 드롭다운 -->
        <select
          class="roady-compact-select sort-select"
          :value="activeSort"
          aria-label="보수 사건 정렬"
          @change="handleSortChange"
        >
          <option v-for="option in REPAIR_SORT_OPTIONS" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>

      <!-- 테이블 영역 -->
      <div class="table-area">
        <RepairTable
          :items="displayedItems"
          :loading="loading"
          :error="fetchError"
          :empty-title="
            totalCount === 0 ? '보수 대상 사건이 없습니다' : '선택한 상태의 사건이 없습니다'
          "
          :empty-description="
            totalCount === 0
              ? '탐지 검토에서 &quot;보수 필요&quot;로 판정한 사건이 여기에 표시됩니다.'
              : activeStatuses.length === 0
                ? '선택된 보수 상태가 없습니다.'
                : '다른 상태 필터를 선택해 보세요.'
          "
          @retry="fetchItems"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.repair-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* ── 본문 ── */
.repair-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  padding: 1.6rem 2rem;
  gap: 1.2rem;
}

/* ── 목록 헤더 ── */
.list-header {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 1.2rem;
  flex-shrink: 0;
}

/* ── 상태 필터 ── */
.status-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem 1.2rem;
  min-width: 0;
  padding: 0;
  margin: 0;
  border: 0;
  flex: 1;
}

/* ── 정렬 드롭다운 ── */
.sort-select {
  margin-left: auto;
  width: 14rem;
  flex-shrink: 0;
}

/* ── 테이블 영역 ── */
.table-area {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* 스크린리더 전용 */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* ── 반응형 ── */
@media (max-width: 768px) {
  .repair-body {
    padding: 1.2rem;
  }

  .list-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .sort-select {
    margin-left: 0;
  }
}
</style>
