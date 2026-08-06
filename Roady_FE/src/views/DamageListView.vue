<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { LocationQueryRaw } from 'vue-router'
import { damagesApi } from '@/api/damages'
import type { DamageListQuery } from '@/api/damages'
import {
  dateRangeForPreset,
  dateRangeFromQuery,
  dateRangeToQuery,
  matchingDateRangePreset,
  validateDateRange,
  toApiFromDateTime,
  toApiToDateTime,
} from '@/utils/localDate'
import type { DamageListItem } from '@/types/damage'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageFilterToolbar from '@/components/common/PageFilterToolbar.vue'
import PageFilterActions from '@/components/common/PageFilterActions.vue'
import DateRangeFilter from '@/components/common/DateRangeFilter.vue'
import DamageCard from '@/components/damages/DamageCard.vue'
import DamageReviewTabs from '@/components/damages/DamageReviewTabs.vue'
import DamageStatusFilterChips from '@/components/damages/DamageStatusFilterChips.vue'
import DamageDetailPanel from '@/components/damages/DamageDetailPanel.vue'
import type { ReviewDecisionPayload } from '@/components/damages/DamageDetailPanel.vue'
import CommonMap from '@/components/common/CommonMap.vue'
import MapRegionFilter from '@/components/common/MapRegionFilter.vue'
import { mergeDamageMapMarkers, toDamageMapCenter, toDamageMapMarkers } from '@/utils/damageMap'
import { useAssignedMapRegion } from '@/composables/useAssignedMapRegion'
import type { DamageMapMarkerResponse } from '@/types/damage'
import type { MapBounds } from '@/types/map'
import { useNotificationStore } from '@/stores/notification'
import {
  defaultDamageSort,
  isReviewConfirmed,
  isReviewVisible,
  sortReviewDamages,
} from '@/utils/damageReview'
import type { ConfirmedStatusFilter, DamageSort, ReviewTab } from '@/utils/damageReview'

// ── 상수 ──────────────────────────────────────────────────

const PAGE_SIZE = 100

const SORT_OPTIONS: { value: DamageSort; label: string }[] = [
  { value: 'latest', label: '최신순' },
  { value: 'oldest', label: '오래된 순' },
  { value: 'priority', label: '우선순위 순' },
]

// ── URL 파싱 ───────────────────────────────────────────────

const route = useRoute()
const router = useRouter()
const notification = useNotificationStore()
const mapRegion = useAssignedMapRegion()

// ── 적용된 필터 (URL = 단일 진실 소스) ────────────────────

const defaultDateRange = dateRangeForPreset(1)
const appliedRange = computed(() => dateRangeFromQuery(route.query, defaultDateRange))
const appliedFrom = computed(() => appliedRange.value.from)
const appliedTo = computed(() => appliedRange.value.to)
const reviewTab = computed<ReviewTab>(() =>
  route.query.review === 'confirmed' ? 'confirmed' : 'pending',
)

function parseDamageSort(value: unknown, tab: ReviewTab): DamageSort {
  const raw = Array.isArray(value) ? value[0] : value
  return raw === 'latest' || raw === 'oldest' || raw === 'priority' ? raw : defaultDamageSort(tab)
}

const sortOrder = ref<DamageSort>(parseDamageSort(route.query.sort, reviewTab.value))

// ── 폼 상태 (미적용 입력값) ───────────────────────────────

const formFrom = ref('')
const formTo = ref('')
const formError = ref('')
const activePreset = ref<number | null>(null)

function syncFormFromUrl() {
  formFrom.value = appliedFrom.value
  formTo.value = appliedTo.value
  formError.value = ''
  activePreset.value = matchingDateRangePreset(appliedFrom.value, appliedTo.value)
}

// ── 목록 데이터 ─────────────────────────────────────────────

const items = ref<DamageListItem[]>([])
const listLoading = ref(false)
const listError = ref<string | null>(null)
let listRequestSeq = 0

const selectedConfirmedStatuses = ref<ConfirmedStatusFilter[]>([])
const isAllConfirmedStatusesSelected = computed(
  () => selectedConfirmedStatuses.value.length === 0,
)

function updateConfirmedStatuses(statuses: ConfirmedStatusFilter[]) {
  selectedConfirmedStatuses.value = statuses
}

function confirmedStatusCategory(item: DamageListItem): ConfirmedStatusFilter | null {
  if (item.currentStatus === 'REQUESTED') {
    return 'requested'
  }
  if (item.currentStatus === 'REPAIR_IN_PROGRESS') {
    return 'in_progress'
  }
  if (item.currentStatus === 'REPAIR_COMPLETED') return 'completed'
  return null
}

const confirmedItems = computed(() =>
  items.value.filter((item) => isReviewVisible(item) && isReviewConfirmed(item)),
)

const confirmedStatusCounts = computed(() => ({
  requested: confirmedItems.value.filter((item) => confirmedStatusCategory(item) === 'requested')
    .length,
  in_progress: confirmedItems.value.filter(
    (item) => confirmedStatusCategory(item) === 'in_progress',
  ).length,
  completed: confirmedItems.value.filter((item) => confirmedStatusCategory(item) === 'completed')
    .length,
}))

const visibleItems = computed(() => {
  const filtered = items.value.filter(
    (item) =>
      isReviewVisible(item) &&
      (reviewTab.value === 'confirmed' ? isReviewConfirmed(item) : !isReviewConfirmed(item)),
  )
  const statusFiltered =
    reviewTab.value !== 'confirmed' || isAllConfirmedStatusesSelected.value
      ? filtered
      : filtered.filter((item) => {
          const category = confirmedStatusCategory(item)
          return category != null && selectedConfirmedStatuses.value.includes(category)
        })
  return sortReviewDamages(statusFiltered, reviewTab.value, sortOrder.value)
})
const boundaryMarkers = ref<DamageMapMarkerResponse[] | null>(null)
const currentMapBounds = ref<MapBounds | null>(null)
const mapMarkersLoading = ref(false)
const mapMarkersError = ref<string | null>(null)
let mapMarkerRequestSequence = 0

const damageMarkers = computed(() =>
  boundaryMarkers.value == null
    ? toDamageMapMarkers(visibleItems.value)
    : mergeDamageMapMarkers(boundaryMarkers.value, visibleItems.value),
)

async function fetchMapMarkers(bounds: MapBounds) {
  const sequence = ++mapMarkerRequestSequence
  mapMarkersLoading.value = true
  mapMarkersError.value = null
  try {
    const markers = await damagesApi.mapMarkers({
      ...bounds,
      ...(appliedFrom.value ? { from: toApiFromDateTime(appliedFrom.value) } : {}),
      ...(appliedTo.value ? { to: toApiToDateTime(appliedTo.value) } : {}),
      ...(mapRegion.assignedRegionCode.value
        ? { regionCode: mapRegion.assignedRegionCode.value }
        : {}),
    })
    if (sequence === mapMarkerRequestSequence) boundaryMarkers.value = markers
  } catch {
    if (sequence === mapMarkerRequestSequence) {
      mapMarkersError.value = '지도 마커를 불러오지 못했습니다.'
    }
  } finally {
    if (sequence === mapMarkerRequestSequence) mapMarkersLoading.value = false
  }
}

function handleMapBoundsChange(bounds: MapBounds) {
  currentMapBounds.value = bounds
  void fetchMapMarkers(bounds)
}

function retryMapMarkers() {
  if (currentMapBounds.value) void fetchMapMarkers(currentMapBounds.value)
}

watch(
  () => visibleItems.value.map((item) => `${item.id}:${item.currentStatus}`).join(','),
  () => {
    if (currentMapBounds.value) void fetchMapMarkers(currentMapBounds.value)
  },
)

async function loadDamages() {
  const requestSeq = ++listRequestSeq
  listLoading.value = true
  listError.value = null

  try {
    const query: DamageListQuery = { page: 0, size: PAGE_SIZE }
    if (appliedFrom.value) query.from = toApiFromDateTime(appliedFrom.value)
    if (appliedTo.value) query.to = toApiToDateTime(appliedTo.value)

    const firstPage = await damagesApi.list(query)
    const remainingPages = Array.from(
      { length: Math.max(0, firstPage.totalPages - 1) },
      (_, index) => index + 1,
    )
    const remainingResults = await Promise.all(
      remainingPages.map((page) => damagesApi.list({ ...query, page })),
    )

    if (requestSeq !== listRequestSeq) return

    items.value = [firstPage, ...remainingResults].flatMap((result) => result.content)
  } catch {
    if (requestSeq !== listRequestSeq) return
    listError.value = '목록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    if (requestSeq === listRequestSeq) listLoading.value = false
  }
}

// ── URL 변경 → 폼 동기화 + 목록 초기 로드 ───────────────

watch(
  () => [route.query.from, route.query.to, route.query.range, route.query.review, route.query.sort],
  () => {
    syncFormFromUrl()
    sortOrder.value = parseDamageSort(route.query.sort, reviewTab.value)
    loadDamages()
  },
  { immediate: true },
)

// ── 폼 핸들러 ──────────────────────────────────────────────

function handleApply() {
  formError.value = validateDateRange(formFrom.value, formTo.value)
  if (formError.value) return
  const query: Record<string, string> = dateRangeToQuery(formFrom.value, formTo.value)
  if (mapRegion.selectedCode.value) query.emd = mapRegion.selectedCode.value
  query.review = reviewTab.value
  router.push({ name: 'damages', query })
}

function handleReset() {
  const range = dateRangeForPreset(1)
  formFrom.value = range.from
  formTo.value = range.to
  activePreset.value = 1
  formError.value = ''
  router.push({
    name: 'damages',
    query: {
      review: reviewTab.value,
      ...dateRangeToQuery(range.from, range.to),
      ...(mapRegion.selectedCode.value ? { emd: mapRegion.selectedCode.value } : {}),
    },
  })
}

function handlePresetApply({ from, to }: { from: string; to: string }) {
  formFrom.value = from
  formTo.value = to
  handleApply()
}

// ── 선택된 사건 (상세 패널) ─────────────────────────────

function parseDamageId(value: unknown): number | null {
  const raw = Array.isArray(value) ? value[0] : value
  const id = Number(raw)
  return Number.isInteger(id) && id > 0 ? id : null
}

const selectedId = ref<number | null>(parseDamageId(route.query.damageId))
const selectedItem = computed(
  () => items.value.find((item) => item.id === selectedId.value) ?? null,
)
const selectedMapCenter = computed(() => toDamageMapCenter(selectedItem.value))
const verdictSubmitting = ref(false)
const detailRefreshKey = ref(0)

function updateSelectedDamage(id: number | null) {
  const query = { ...route.query }
  if (id == null) delete query.damageId
  else query.damageId = String(id)
  router.replace({ path: route.path, query })
}

function selectItem(id: number) {
  updateSelectedDamage(id === selectedId.value ? null : id)
}

function closeDetail() {
  if (verdictSubmitting.value) return
  updateSelectedDamage(null)
}

watch(
  () => route.query.damageId,
  (value) => {
    selectedId.value = parseDamageId(value)
  },
)

async function submitVerdict(
  status: 'AI_ANALYZED' | 'REQUESTED' | 'CANCELED',
  decision: ReviewDecisionPayload | null = null,
  overrideDamageId?: number,
) {
  const damageId = overrideDamageId ?? selectedId.value
  if (damageId == null || verdictSubmitting.value) return
  const wasConfirmed = selectedItem.value ? isReviewConfirmed(selectedItem.value) : false

  verdictSubmitting.value = true
  try {
    const isRepairRequired = status === 'REQUESTED'
    await damagesApi.updateReview(
      damageId,
      status,
      isRepairRequired ? decision?.processingPriority : null,
      isRepairRequired ? decision?.reviewDamageType : null,
      isRepairRequired ? decision?.reviewNote : null,
    )
    const toRepairDetailAction = {
      label: '요청서 작성하기',
      to: {
        name: 'repair-detail',
        params: { damageId: String(damageId) },
        query: {
          action: 'create-request',
          backTo: router.resolve({
            name: 'damages',
            query: { review: 'confirmed', damageId: String(damageId) },
          }).fullPath,
        },
      },
    }
    const revertAction = {
      label: '판정 되돌리기',
      onClick: () => submitVerdict('AI_ANALYZED', null, damageId),
    }

    if (isRepairRequired) {
      notification.success(
        wasConfirmed
          ? '판정이 수정되었습니다.'
          : '보수 필요로 판정했습니다. 요청 전 목록에서 확인할 수 있습니다.',
        7000,
        wasConfirmed ? [toRepairDetailAction] : [toRepairDetailAction, revertAction],
      )
    } else if (status === 'CANCELED') {
      notification.success('보수 불필요로 판정했습니다.', 7000, [revertAction])
    } else {
      notification.success('관리자 판정을 되돌렸습니다. 미확인 목록에서 다시 검토할 수 있습니다.')
    }
    await loadDamages()
    if (status === 'REQUESTED' && wasConfirmed) {
      items.value = items.value.map((item) =>
        item.id === damageId
          ? {
              ...item,
              processingPriority: decision?.processingPriority ?? null,
              reviewDamageType: decision?.reviewDamageType ?? null,
              reviewNote: decision?.reviewNote ?? null,
            }
          : item,
      )
      detailRefreshKey.value += 1
    } else {
      updateSelectedDamage(null)
    }
  } catch {
    notification.error('판정을 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.')
  } finally {
    verdictSubmitting.value = false
  }
}

function selectReviewTab(tab: ReviewTab) {
  if (tab === reviewTab.value) return
  const query: LocationQueryRaw = { ...route.query, review: tab }
  delete query.damageId
  router.push({
    path: route.path,
    query,
  })
}

watch(reviewTab, (tab) => {
  sortOrder.value = parseDamageSort(route.query.sort, tab)
  selectedConfirmedStatuses.value = []
})

const detailPanelWidth = ref(460)
let resizeStartX = 0
let resizeStartWidth = 0

function clampDetailPanelWidth(width: number): number {
  const viewportLimit = typeof window === 'undefined' ? 600 : Math.max(380, window.innerWidth - 420)
  return Math.min(Math.max(width, 380), Math.min(600, viewportLimit))
}

function handleDetailResize(event: PointerEvent) {
  detailPanelWidth.value = clampDetailPanelWidth(resizeStartWidth + resizeStartX - event.clientX)
}

function stopDetailResize() {
  document.removeEventListener('pointermove', handleDetailResize)
  document.removeEventListener('pointerup', stopDetailResize)
}

function startDetailResize(event: PointerEvent) {
  resizeStartX = event.clientX
  resizeStartWidth = detailPanelWidth.value
  document.addEventListener('pointermove', handleDetailResize)
  document.addEventListener('pointerup', stopDetailResize)
}

function handleDetailResizeKeydown(event: KeyboardEvent) {
  if (event.key === 'ArrowLeft') {
    event.preventDefault()
    detailPanelWidth.value = clampDetailPanelWidth(detailPanelWidth.value + 20)
  } else if (event.key === 'ArrowRight') {
    event.preventDefault()
    detailPanelWidth.value = clampDetailPanelWidth(detailPanelWidth.value - 20)
  }
}

onBeforeUnmount(stopDetailResize)
</script>

<template>
  <div class="damage-view">
    <!-- 상단 툴바 -->
    <PageFilterToolbar aria-label="탐지 사건 조회 조건" @submit="handleApply">
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
        <PageFilterActions @reset="handleReset" />
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
              현재 <strong>{{ visibleItems.length.toLocaleString('ko-KR') }}</strong
              >건
            </p>
          </div>
          <select v-model="sortOrder" class="roady-compact-select list-sort-select" aria-label="탐지 사건 정렬">
            <option v-for="option in SORT_OPTIONS" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <DamageReviewTabs :model-value="reviewTab" @update:model-value="selectReviewTab" />

        <DamageStatusFilterChips
          v-if="reviewTab === 'confirmed'"
          :selected="selectedConfirmedStatuses"
          :counts="confirmedStatusCounts"
          @update:selected="updateConfirmedStatuses"
        />

        <div class="list-body">
          <!-- 초기 로딩 -->
          <div v-if="listLoading && items.length === 0" class="list-state">
            <LoadingSpinner label="목록 불러오는 중" />
          </div>

          <!-- 오류 -->
          <div v-else-if="listError && items.length === 0" class="list-state">
            <ErrorState :message="listError" @retry="loadDamages" />
          </div>

          <!-- 빈 결과 -->
          <EmptyState
            v-else-if="!listLoading && visibleItems.length === 0"
            :title="reviewTab === 'pending' ? '미확인 사건이 없습니다' : '확인된 사건이 없습니다'"
            description="다른 탭이나 조회 조건을 확인해 보세요."
          />

          <!-- 카드 목록 -->
          <template v-else>
            <DamageCard
              v-for="item in visibleItems"
              :key="item.id"
              :item="item"
              :selected="selectedId === item.id"
              @select="selectItem"
            />

            <!-- 조회 결과 -->
            <div class="load-more-area">
              <p v-if="items.length > 0" class="list-end">
                현재 탭 {{ visibleItems.length.toLocaleString('ko-KR') }}건 표시
              </p>
            </div>
          </template>
        </div>
      </div>

      <!-- 중앙: 탐지 사건 지도 -->
      <div class="map-panel" aria-label="도로 파손 지도">
        <CommonMap
          class="damage-map"
          :markers="damageMarkers"
          :viewport-bounds="mapRegion.selectedBounds.value"
          :focused-center="selectedMapCenter"
          :focus-zoom="16"
          :right-inset="selectedId != null ? detailPanelWidth : 0"
          map-label="조회된 탐지 사건 위치 지도"
          empty-message="위치 정보가 있는 탐지 사건이 없습니다."
          @marker-select="selectItem(Number($event))"
          @bounds-change="handleMapBoundsChange"
        >
          <MapRegionFilter
            id="damage-map-region"
            :model-value="mapRegion.selectedCode.value"
            :assigned-region-name="mapRegion.assignedRegionName.value"
            :options="mapRegion.options.value"
            :loading="mapRegion.loading.value"
            :error="mapRegion.error.value"
            @update:model-value="mapRegion.select"
            @retry="mapRegion.load"
          />
          <div v-if="mapMarkersError" class="map-query-error" role="alert">
            <span>{{ mapMarkersError }}</span>
            <button type="button" @click="retryMapMarkers">다시 시도</button>
          </div>
          <span v-if="mapMarkersLoading" class="map-query-loading" role="status">
            파손 위치 갱신 중
          </span>
        </CommonMap>
      </div>

      <!-- 오른쪽: 상세 패널 (슬라이드 인) -->
      <Transition name="slide">
        <div
          v-if="selectedId != null"
          class="detail-panel-wrapper"
          :style="{ width: `${detailPanelWidth}px` }"
        >
          <div
            class="detail-resize-handle"
            role="separator"
            aria-label="사건 상세 패널 너비 조절"
            aria-orientation="vertical"
            :aria-valuenow="detailPanelWidth"
            aria-valuemin="380"
            aria-valuemax="600"
            tabindex="0"
            @pointerdown.prevent="startDetailResize"
            @keydown="handleDetailResizeKeydown"
          />
          <DamageDetailPanel
            :damage-id="selectedId"
            :refresh-key="detailRefreshKey"
            :summary="selectedItem"
            :back-to="route.fullPath"
            :verdict-submitting="verdictSubmitting"
            @close="closeDetail"
            @verdict-no-repair="submitVerdict('CANCELED')"
            @verdict-repair="submitVerdict('REQUESTED', $event)"
            @verdict-reset="submitVerdict('AI_ANALYZED')"
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
  flex-shrink: 0;
}

.list-sort-select {
  width: 12rem;
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
  position: relative;
  z-index: 0;
  isolation: isolate;
  overflow: hidden;
  background: var(--roady-surface-background);
  min-width: 0;
}

.damage-map {
  min-height: 100%;
  border-radius: 0;
}

.map-query-error,
.map-query-loading {
  position: absolute;
  right: 1.6rem;
  bottom: 1.6rem;
  z-index: 600;
  padding: 0.8rem 1.2rem;
  border-radius: 0.6rem;
  background: var(--roady-surface-default);
  box-shadow: 0 0.4rem 1.2rem rgb(0 0 0 / 12%);
  font-size: var(--krds-pc-font-size-label-small);
}

.map-query-error {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  border: 1px solid var(--roady-status-danger);
  color: var(--roady-status-danger);
}

.map-query-error button {
  border: 0;
  color: inherit;
  background: transparent;
  font: inherit;
  font-weight: var(--krds-font-weight-bold);
  text-decoration: underline;
  cursor: pointer;
}

.map-query-loading {
  color: var(--roady-text-secondary);
  pointer-events: none;
}

/* ── 상세 패널 (슬라이드) ── */
.detail-panel-wrapper {
  position: absolute;
  top: 0;
  right: 0;
  max-width: calc(100% - 2rem);
  height: 100%;
  z-index: 10;
  box-shadow: -4px 0 16px rgb(0 0 0 / 10%);
}

.detail-resize-handle {
  position: absolute;
  top: 0;
  bottom: 0;
  left: -0.5rem;
  z-index: 11;
  width: 1rem;
  cursor: ew-resize;
  touch-action: none;
}

.detail-resize-handle::after {
  position: absolute;
  top: 50%;
  left: 0.3rem;
  width: 0.4rem;
  height: 4.8rem;
  border-radius: 999px;
  background: var(--roady-border-default);
  content: '';
  transform: translateY(-50%);
  transition: background-color 0.12s;
}

.detail-resize-handle:hover::after,
.detail-resize-handle:focus-visible::after {
  background: var(--roady-brand-secondary);
}

.detail-resize-handle:focus-visible {
  outline: none;
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

@media (prefers-reduced-motion: reduce) {
  .slide-enter-active,
  .slide-leave-active {
    transition: none;
  }
}
</style>
