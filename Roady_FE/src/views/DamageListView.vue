<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { damagesApi } from '@/api/damages'
import type { DamageListQuery } from '@/api/damages'
import type { DamageListItem, DamageSearchResponse, DamageStatus } from '@/types/damage'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageFilterToolbar from '@/components/common/PageFilterToolbar.vue'
import DateRangeFilter from '@/components/common/DateRangeFilter.vue'
import DamageCard from '@/components/damages/DamageCard.vue'
import DamageDetailPanel from '@/components/damages/DamageDetailPanel.vue'

// ── 상수 ──────────────────────────────────────────────────

const VALID_STATUSES: DamageStatus[] = [
  'COLLECTED', 'REVIEW_REQUIRED', 'RECEIVED',
  'REPAIR_SCHEDULED', 'REPAIRING', 'REPAIR_COMPLETED', 'REPAIR_NOT_REQUIRED',
]

const STATUS_OPTIONS = [
  { value: '', label: '전체 상태' },
  { value: 'COLLECTED', label: '탐지됨' },
  { value: 'REVIEW_REQUIRED', label: '검토 필요' },
  { value: 'RECEIVED', label: '접수됨' },
  { value: 'REPAIR_SCHEDULED', label: '보수 예정' },
  { value: 'REPAIRING', label: '보수 중' },
  { value: 'REPAIR_COMPLETED', label: '보수 완료' },
  { value: 'REPAIR_NOT_REQUIRED', label: '보수 불필요' },
]

// ── URL 파싱 ───────────────────────────────────────────────

const route = useRoute()
const router = useRouter()

function parseStatus(val: unknown): DamageStatus | undefined {
  const s = String(val || '')
  return VALID_STATUSES.includes(s as DamageStatus) ? (s as DamageStatus) : undefined
}

// ── 적용된 필터 (URL = 단일 진실 소스) ────────────────────

const appliedFrom = computed(() => String(route.query.from || ''))
const appliedTo = computed(() => String(route.query.to || ''))
const appliedStatus = computed(() => parseStatus(route.query.status))

// ── 폼 상태 (미적용 입력값) ───────────────────────────────

const formFrom = ref('')
const formTo = ref('')
const formStatus = ref('')
const formError = ref('')
const activePreset = ref<number | null>(null)

// 프리셋의 날짜 오프셋 (DateRangeFilter의 PRESETS와 동일한 순서)
const PRESET_OFFSETS = [0, 6, 29]

function toDateString(d: Date): string {
  return d.toISOString().slice(0, 10)
}

function computeActivePreset(from: string, to: string): number | null {
  if (!from || !to) return null
  const today = new Date()
  const todayStr = toDateString(today)
  if (to !== todayStr) return null
  for (let i = 0; i < PRESET_OFFSETS.length; i++) {
    const offset = PRESET_OFFSETS[i] ?? 0
    const d = new Date(today)
    d.setDate(d.getDate() - offset)
    if (from === toDateString(d)) return i
  }
  return null
}

function syncFormFromUrl() {
  formFrom.value = appliedFrom.value
  formTo.value = appliedTo.value
  formStatus.value = appliedStatus.value ?? ''
  formError.value = ''
  activePreset.value = computeActivePreset(appliedFrom.value, appliedTo.value)
}

// ── 목록 데이터 ─────────────────────────────────────────────

const items = ref<DamageListItem[]>([])
const totalElements = ref(0)
const currentPage = ref(0)     // 0-based (API 기준)
const totalPages = ref(0)
const listLoading = ref(false)
const listError = ref<string | null>(null)
const hasMore = computed(() => currentPage.value + 1 < totalPages.value)

async function loadPage(page: number, append: boolean) {
  listLoading.value = true
  if (!append) listError.value = null

  try {
    const query: DamageListQuery = { page, size: 20 }
    if (appliedFrom.value) query.from = appliedFrom.value
    if (appliedTo.value) query.to = appliedTo.value
    if (appliedStatus.value) query.status = appliedStatus.value

    const res: DamageSearchResponse = await damagesApi.list(query)

    if (append) {
      items.value = [...items.value, ...res.content]
    } else {
      items.value = res.content
      selectedId.value = null
    }
    totalElements.value = res.totalElements
    currentPage.value = res.page
    totalPages.value = res.totalPages
  } catch {
    listError.value = '목록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    listLoading.value = false
  }
}

function loadMore() {
  if (hasMore.value && !listLoading.value) {
    loadPage(currentPage.value + 1, true)
  }
}

// ── URL 변경 → 폼 동기화 + 목록 초기 로드 ───────────────

watch(
  () => route.query,
  () => {
    syncFormFromUrl()
    loadPage(0, false)
  },
  { immediate: true },
)

// ── 폼 핸들러 ──────────────────────────────────────────────

function handleApply() {
  formError.value = ''
  if (formFrom.value && formTo.value && formFrom.value > formTo.value) {
    formError.value = '시작일은 종료일보다 이전이어야 합니다.'
    return
  }
  const query: Record<string, string> = {}
  if (formFrom.value) query.from = formFrom.value
  if (formTo.value) query.to = formTo.value
  if (formStatus.value) query.status = formStatus.value
  router.push({ name: 'damages', query })
}

function handleReset() {
  activePreset.value = null
  router.push({ name: 'damages' })
}

function handlePresetApply({ from, to }: { from: string; to: string }) {
  formFrom.value = from
  formTo.value = to
  handleApply()
}

// ── 선택된 사건 (상세 패널) ─────────────────────────────

const selectedId = ref<number | null>(null)

function selectItem(id: number) {
  selectedId.value = id === selectedId.value ? null : id
}

function closeDetail() {
  selectedId.value = null
}
</script>

<template>
  <div class="damage-view">

    <!-- 상단 툴바 -->
    <PageFilterToolbar aria-label="탐지 사건 조회 조건">

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

      <!-- 처리 상태 -->
      <div class="toolbar-group">
        <span class="toolbar-label">상태</span>
        <select v-model="formStatus" class="krds-form-select small status-select" aria-label="처리 상태 필터">
          <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
      </div>

      <!-- 사건 번호·주소 검색 (준비 중, UI만 숨김) -->
      <div style="display: none" aria-hidden="true">
        <input
          type="text"
          class="krds-input small"
          placeholder="사건 번호 또는 지역 검색"
          disabled
          aria-label="사건 번호 또는 지역 검색 (준비 중)"
        />
      </div>

      <template #actions>
        <button type="button" class="krds-btn small outline" @click="handleReset">초기화</button>
        <button type="button" class="krds-btn small filled primary" @click="handleApply">조회</button>
      </template>

    </PageFilterToolbar>

    <!-- 콘텐츠 영역 -->
    <div class="damage-body">

      <!-- 왼쪽: 목록 패널 -->
      <div class="list-panel">
        <div class="list-header">
          <div>
            <h2 class="list-title">탐지된 사건</h2>
            <p class="list-subtitle">
              전체 <strong>{{ totalElements.toLocaleString('ko-KR') }}</strong>건
            </p>
          </div>
        </div>

        <div class="list-body">
          <!-- 초기 로딩 -->
          <div v-if="listLoading && items.length === 0" class="list-state">
            <LoadingSpinner label="목록 불러오는 중" />
          </div>

          <!-- 오류 -->
          <div v-else-if="listError && items.length === 0" class="list-state">
            <ErrorState :message="listError" @retry="loadPage(0, false)" />
          </div>

          <!-- 빈 결과 -->
          <EmptyState
            v-else-if="!listLoading && items.length === 0"
            title="검색 결과가 없습니다"
            description="조회 조건을 변경해 보세요."
          />

          <!-- 카드 목록 -->
          <template v-else>
            <DamageCard
              v-for="item in items"
              :key="item.id"
              :item="item"
              :selected="selectedId === item.id"
              @select="selectItem"
            />

            <!-- 더 보기 -->
            <div class="load-more-area">
              <div v-if="listLoading" class="load-more-loading">
                <LoadingSpinner label="더 불러오는 중" />
              </div>
              <button
                v-else-if="hasMore"
                type="button"
                class="krds-btn medium outline load-more-btn"
                @click="loadMore"
              >
                더 보기 ({{ totalElements - items.length }}건 남음)
              </button>
              <p v-else-if="items.length > 0" class="list-end">
                전체 {{ totalElements.toLocaleString('ko-KR') }}건 표시 완료
              </p>
            </div>
          </template>
        </div>
      </div>

      <!-- 중앙: 지도 placeholder (S15P11A404-137) -->
      <div class="map-panel" aria-label="도로 파손 지도">
        <div class="map-placeholder">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/>
            <line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
          </svg>
          <p>지도 연동 구현 예정 (S15P11A404-137)</p>
        </div>
      </div>

      <!-- 오른쪽: 상세 패널 (슬라이드 인) -->
      <Transition name="slide">
        <div v-if="selectedId != null" class="detail-panel-wrapper">
          <DamageDetailPanel
            :damage-id="selectedId"
            @close="closeDetail"
          />
        </div>
      </Transition>

    </div>
  </div>
</template>

<style scoped>
.damage-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* ── 툴바 그룹 (PageFilterToolbar 내부) ── */
.toolbar-group {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  flex-wrap: nowrap;
}

.toolbar-label {
  flex-shrink: 0;
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-secondary);
  white-space: nowrap;
}

.status-select {
  width: 14rem;
  height: 4rem;
}

/* ── 본문 ── */
.damage-body {
  flex: 1;
  display: flex;
  min-height: 0;
  position: relative;
  overflow: hidden;
}

/* ── 목록 패널 ── */
.list-panel {
  width: 42rem;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--roady-border-default);
  background: var(--roady-surface-default);
  min-height: 0;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.4rem 1.6rem 1rem;
  border-bottom: 1px solid var(--roady-border-default);
  flex-shrink: 0;
}

.list-title {
  margin: 0;
  font-size: var(--krds-pc-font-size-heading-xsmall);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
}

.list-subtitle {
  margin: 0.2rem 0 0;
  font-size: var(--krds-pc-font-size-body-small);
  color: var(--roady-text-tertiary);
}

.list-subtitle strong {
  color: var(--roady-text-primary);
  font-weight: var(--krds-font-weight-bold);
}

.list-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.list-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 4rem 2rem;
}

.load-more-area {
  padding: 1.2rem 1.6rem;
  display: flex;
  justify-content: center;
}

.load-more-loading {
  padding: 0.8rem;
}

.load-more-btn {
  width: 100%;
}

.list-end {
  margin: 0;
  font-size: var(--krds-pc-font-size-label-xsmall);
  color: var(--roady-text-tertiary);
  text-align: center;
  padding: 0.4rem 0;
}

/* ── 지도 패널 ── */
.map-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--roady-surface-background);
  min-width: 0;
}

.map-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.2rem;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
}

/* ── 상세 패널 (슬라이드) ── */
.detail-panel-wrapper {
  position: absolute;
  top: 0;
  right: 0;
  width: 42rem;
  height: 100%;
  z-index: 10;
  box-shadow: -4px 0 16px rgb(0 0 0 / 10%);
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

.slide-enter-to,
.slide-leave-from {
  transform: translateX(0);
}
</style>
