<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { damagesApi } from '@/api/damages'
import type { DamageListQuery } from '@/api/damages'
import type { DamageListItem } from '@/types/damage'
import PageFilterToolbar from '@/components/common/PageFilterToolbar.vue'
import PageFilterActions from '@/components/common/PageFilterActions.vue'
import DateRangeFilter from '@/components/common/DateRangeFilter.vue'
import RepairStatusFilterChips from '@/components/common/RepairStatusFilterChips.vue'
import RepairTable from '@/components/repairs/RepairTable.vue'
import {
  dateRangeForPreset,
  dateRangeFromQuery,
  dateRangeToQuery,
  matchingDateRangePreset,
  validateDateRange,
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
  REPAIR_SORT_OPTIONS,
} from '@/utils/repairManagement'
import type { RepairStatusFilter, RepairSort } from '@/utils/repairManagement'

// ── 라우터 ──────────────────────────────────────────────────
const route = useRoute()
const router = useRouter()

// ── URL → 적용 필터 (단일 진실 소스) ──────────────────────
const defaultDateRange = dateRangeForPreset(1)
const appliedRange = computed(() => dateRangeFromQuery(route.query, defaultDateRange))
const appliedFrom = computed(() => appliedRange.value.from)
const appliedTo = computed(() => appliedRange.value.to)

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
const activePreset = ref<number | null>(matchingDateRangePreset(appliedFrom.value, appliedTo.value))

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
const selectedStatusChips = computed<RepairStatusFilter[]>(() =>
  activeStatuses.value.length === REPAIR_STATUS_FILTERS.length ? [] : activeStatuses.value,
)

// ── URL 쿼리 빌더 ─────────────────────────────────────────
function buildQuery(overrides: Record<string, string | undefined> = {}): Record<string, string> {
  const from = Object.hasOwn(overrides, 'from') ? overrides.from || '' : appliedFrom.value
  const to = Object.hasOwn(overrides, 'to') ? overrides.to || '' : appliedTo.value
  const base: Record<string, string | undefined> = dateRangeToQuery(from, to)
  const statusParam = statusesToParam(activeStatuses.value)
  if (statusParam) base.statuses = statusParam
  if (activeSort.value !== 'priority') base.sort = activeSort.value
  const remainingOverrides = { ...overrides }
  delete remainingOverrides.from
  delete remainingOverrides.to
  delete remainingOverrides.range
  const merged = { ...base, ...remainingOverrides }
  return Object.fromEntries(
    Object.entries(merged).filter((entry): entry is [string, string] => entry[1] != null),
  )
}

// ── 상태 필터 조작 ────────────────────────────────────────
function setStatuses(next: RepairStatusFilter[]) {
  const param = statusesToParam(next)
  router.replace({ query: buildQuery({ statuses: param }) })
}

// ── 정렬 ────────────────────────────────────────────────
function handleSortChange(event: Event) {
  const val = (event.target as HTMLSelectElement).value as RepairSort
  const q = buildQuery({ sort: val !== 'priority' ? val : undefined })
  router.replace({ query: q })
}

// ── 날짜 필터 핸들러 ─────────────────────────────────────
function handleSearch() {
  formError.value = validateDateRange(formFrom.value, formTo.value)
  if (formError.value) return
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
        <PageFilterActions @reset="handleReset" />
      </template>
    </PageFilterToolbar>

    <!-- 본문 -->
    <div class="repair-body">
      <!-- 목록 헤더: 상태 필터 + 정렬 -->
      <RepairStatusFilterChips
        :selected="selectedStatusChips"
        :counts="statusCounts"
        aria-label="보수 상태 필터"
        @update:selected="setStatuses"
      >
        <template #actions>
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
        </template>
      </RepairStatusFilterChips>

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

/* ── 정렬 드롭다운 ── */
.sort-select {
  min-inline-size: var(--roady-control-sort-min-width);
}

/* ── 테이블 영역 ── */
.table-area {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* ── 반응형 ── */
@media (max-width: 768px) {
  .repair-body {
    padding: 1.2rem;
  }

  .sort-select {
    width: 100%;
  }
}
</style>
