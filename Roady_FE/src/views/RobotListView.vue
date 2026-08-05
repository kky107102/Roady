<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { robotsApi } from '@/api/robots'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import KrdsSelect from '@/components/common/KrdsSelect.vue'
import type { SelectOption } from '@/components/common/KrdsSelect.vue'
import KrdsTextInput from '@/components/common/KrdsTextInput.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import CommonMap from '@/components/common/CommonMap.vue'
import type { Robot, RobotConnectionStatus, RobotOperationStatus } from '@/types/robot'
import {
  connectionBadge,
  connectionLabels,
  formatBattery,
  formatDateTime,
  operationBadge,
  operationLabels,
} from '@/utils/robotDisplay'
import { toRobotMapMarkers } from '@/utils/robotMap'

const robots = ref<Robot[]>([])
const loading = ref(true)
const error = ref(false)
const sortBy = ref('name-asc')
const operationFilter = ref('ALL')
const connectionFilter = ref('ALL')
const searchInput = ref('')
const appliedSearchQuery = ref('')

const collator = new Intl.Collator('ko-KR', { numeric: true, sensitivity: 'base' })

const sortOptions: SelectOption[] = [
  { value: 'name-asc', label: '로봇명 오름차순' },
  { value: 'name-desc', label: '로봇명 내림차순' },
  { value: 'serial-asc', label: '시리얼 번호순' },
  { value: 'battery-asc', label: '배터리 낮은 순' },
  { value: 'battery-desc', label: '배터리 높은 순' },
  { value: 'updated-desc', label: '최근 갱신순' },
]

const operationOptions: SelectOption[] = [
  { value: 'ALL', label: '전체' },
  ...Object.entries(operationLabels).map(([value, label]) => ({ value, label })),
]

const connectionOptions: SelectOption[] = [
  { value: 'ALL', label: '전체' },
  ...Object.entries(connectionLabels).map(([value, label]) => ({ value, label })),
]

const hasActiveFilter = computed(
  () =>
    operationFilter.value !== 'ALL' ||
    connectionFilter.value !== 'ALL' ||
    appliedSearchQuery.value.length > 0,
)
const canReset = computed(() => hasActiveFilter.value || searchInput.value.trim().length > 0)
const robotCountLabel = computed(() =>
  hasActiveFilter.value
    ? `${displayedRobots.value.length}대 / 총 ${robots.value.length}대`
    : `총 ${robots.value.length}대`,
)

const displayedRobots = computed(() => {
  const normalizedQuery = appliedSearchQuery.value.toLocaleLowerCase('ko-KR')
  const filtered = robots.value.filter((robot) => {
    const searchMatches =
      !normalizedQuery ||
      robot.name.toLocaleLowerCase('ko-KR').includes(normalizedQuery) ||
      robot.serialNumber.toLocaleLowerCase('ko-KR').includes(normalizedQuery)
    const operationMatches =
      operationFilter.value === 'ALL' ||
      robot.latestStatus?.operationStatus === (operationFilter.value as RobotOperationStatus)
    const connectionMatches =
      connectionFilter.value === 'ALL' ||
      robot.latestStatus?.connectionStatus === (connectionFilter.value as RobotConnectionStatus)

    return searchMatches && operationMatches && connectionMatches
  })

  return [...filtered].sort((a, b) => {
    if (sortBy.value === 'name-desc') return collator.compare(b.name, a.name)
    if (sortBy.value === 'serial-asc') {
      return collator.compare(a.serialNumber, b.serialNumber)
    }
    if (sortBy.value === 'battery-asc' || sortBy.value === 'battery-desc') {
      const aBattery = a.latestStatus?.batteryLevel
      const bBattery = b.latestStatus?.batteryLevel

      if (aBattery == null && bBattery == null) return collator.compare(a.name, b.name)
      if (aBattery == null) return 1
      if (bBattery == null) return -1
      return sortBy.value === 'battery-asc' ? aBattery - bBattery : bBattery - aBattery
    }
    if (sortBy.value === 'updated-desc') {
      const aTime = a.latestStatus?.recordedAt ? new Date(a.latestStatus.recordedAt).getTime() : 0
      const bTime = b.latestStatus?.recordedAt ? new Date(b.latestStatus.recordedAt).getTime() : 0
      return bTime - aTime
    }
    return collator.compare(a.name, b.name)
  })
})

const urgentRobots = computed(() =>
  robots.value
    .filter((robot) => getUrgentReasons(robot).length > 0)
    .sort((a, b) => collator.compare(a.name, b.name)),
)
const robotMarkers = computed(() => toRobotMapMarkers(robots.value))

function getUrgentReasons(robot: Robot): string[] {
  const reasons: string[] = []
  const status = robot.latestStatus

  if (status?.operationStatus === 'ERROR') reasons.push('운행 상태 오류')
  if (status?.connectionStatus === 'DISCONNECTED') reasons.push('연결 끊김')
  if (status?.batteryLevel != null && status.batteryLevel <= 10) {
    reasons.push(`배터리 부족 ${status.batteryLevel}%`)
  }

  return reasons
}

function isLowBattery(value: number | null | undefined): boolean {
  return value != null && value <= 10
}

function resetFilters() {
  operationFilter.value = 'ALL'
  connectionFilter.value = 'ALL'
  searchInput.value = ''
  appliedSearchQuery.value = ''
}

function applySearch() {
  appliedSearchQuery.value = searchInput.value.trim()
}

async function fetchRobots() {
  loading.value = true
  error.value = false

  try {
    robots.value = await robotsApi.list()
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(fetchRobots)
</script>

<template>
  <div class="robot-list">
    <header class="page-header">
      <div>
        <h1>로봇 운행 현황</h1>
        <p>등록된 로디의 최신 운행 및 연결 상태를 확인합니다.</p>
      </div>
      <span v-if="!loading && !error" class="robot-count">{{ robotCountLabel }}</span>
    </header>

    <div v-if="!loading && !error" class="overview-grid">
      <section class="overview-card map-card" aria-labelledby="robot-map-title">
        <div class="overview-header">
          <h2 id="robot-map-title">로봇 위치 현황</h2>
          <p>마지막으로 수집된 로봇 위치입니다. 마커를 선택하면 상태를 확인할 수 있습니다.</p>
        </div>
        <CommonMap
          class="robot-list-map"
          :markers="robotMarkers"
          map-label="전체 로봇 최신 위치 지도"
          empty-message="위치 정보가 수집된 로봇이 없습니다."
        />
      </section>

      <section class="overview-card urgent-card" aria-labelledby="urgent-robot-title">
        <div class="overview-header urgent-header">
          <div>
            <h2 id="urgent-robot-title">긴급 확인</h2>
            <p>오류, 연결 끊김, 배터리 부족 로봇입니다.</p>
          </div>
          <span class="urgent-count">{{ urgentRobots.length }}대</span>
        </div>

        <EmptyState v-if="urgentRobots.length === 0" title="긴급 확인이 필요한 로봇이 없습니다." />
        <ul v-else class="urgent-list">
          <li v-for="robot in urgentRobots" :key="robot.id">
            <RouterLink
              class="urgent-robot-link"
              :to="{ name: 'robot-detail', params: { id: robot.id } }"
            >
              {{ robot.name }}
            </RouterLink>
            <div class="urgent-reasons">
              <span v-for="reason in getUrgentReasons(robot)" :key="reason">
                {{ reason }}
              </span>
            </div>
          </li>
        </ul>
      </section>
    </div>

    <form
      v-if="!loading && !error && robots.length > 0"
      class="list-toolbar"
      aria-label="로봇 목록 정렬 및 필터"
      @submit.prevent="applySearch"
    >
      <KrdsSelect
        id="robot-sort"
        v-model="sortBy"
        name="robot-sort"
        label="정렬 기준"
        size="medium"
        :options="sortOptions"
      />
      <KrdsSelect
        id="operation-filter"
        v-model="operationFilter"
        name="operation-filter"
        label="운행 상태"
        size="medium"
        :options="operationOptions"
      />
      <KrdsSelect
        id="connection-filter"
        v-model="connectionFilter"
        name="connection-filter"
        label="연결 상태"
        size="medium"
        :options="connectionOptions"
      />
      <KrdsTextInput
        id="robot-search"
        v-model="searchInput"
        name="robot-search"
        label="검색"
        size="medium"
        placeholder="로봇명 또는 시리얼 번호"
        autocomplete="off"
      />
      <div class="toolbar-actions">
        <button type="submit" class="search-button">검색</button>
        <button type="button" class="filter-reset" :disabled="!canReset" @click="resetFilters">
          필터 초기화
        </button>
      </div>
    </form>

    <section class="content-panel" aria-label="로봇 목록">
      <LoadingSpinner v-if="loading" label="로봇 목록을 불러오는 중" />
      <ErrorState
        v-else-if="error"
        message="로봇 목록을 불러오지 못했습니다."
        retry-label="다시 시도"
        @retry="fetchRobots"
      />
      <EmptyState
        v-else-if="robots.length === 0"
        title="등록된 로봇이 없습니다."
        description="로봇이 등록되면 이곳에서 운행 상태를 확인할 수 있습니다."
      />
      <EmptyState
        v-else-if="displayedRobots.length === 0"
        title="조건에 맞는 로봇이 없습니다."
        description="검색어나 상태 필터를 변경해 주세요."
      >
        <button type="button" class="krds-btn medium secondary" @click="resetFilters">
          필터 초기화
        </button>
      </EmptyState>

      <div v-else class="table-scroll">
        <table>
          <caption class="sr-only">
            로봇명, 시리얼 번호, 운행 및 연결 상태, 배터리, 마지막 갱신 시각
          </caption>
          <colgroup>
            <col class="col-name" />
            <col class="col-serial" />
            <col class="col-operation" />
            <col class="col-connection" />
            <col class="col-battery" />
            <col class="col-updated" />
            <col class="col-detail" />
          </colgroup>
          <thead>
            <tr>
              <th scope="col">로봇명</th>
              <th scope="col">시리얼 번호</th>
              <th scope="col">운행 상태</th>
              <th scope="col">연결 상태</th>
              <th scope="col" class="battery-cell">배터리</th>
              <th scope="col" class="updated-cell">마지막 갱신</th>
              <th scope="col"><span class="sr-only">상세 이동</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="robot in displayedRobots" :key="robot.id">
              <td class="robot-name">{{ robot.name }}</td>
              <td class="serial-number" :title="robot.serialNumber">
                {{ robot.serialNumber }}
              </td>
              <td>
                <StatusBadge
                  :type="operationBadge(robot.latestStatus?.operationStatus).type"
                  :label="operationBadge(robot.latestStatus?.operationStatus).label"
                />
              </td>
              <td>
                <StatusBadge
                  :type="connectionBadge(robot.latestStatus?.connectionStatus).type"
                  :label="connectionBadge(robot.latestStatus?.connectionStatus).label"
                />
              </td>
              <td
                class="battery-cell"
                :class="{ 'low-battery': isLowBattery(robot.latestStatus?.batteryLevel) }"
              >
                {{ formatBattery(robot.latestStatus?.batteryLevel) }}
              </td>
              <td class="updated-cell">{{ formatDateTime(robot.latestStatus?.recordedAt) }}</td>
              <td class="detail-cell">
                <RouterLink
                  class="detail-link"
                  :to="{ name: 'robot-detail', params: { id: robot.id } }"
                  :aria-label="`${robot.name} 상세 보기`"
                >
                  상세 보기
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.robot-list {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding: 2.4rem 3.2rem;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 2rem;
}

.page-header h1 {
  margin: 0;
  font-size: var(--krds-pc-font-size-heading-medium);
}

.page-header p {
  margin: 0.6rem 0 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
}

.robot-count {
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
}

.content-panel {
  overflow: hidden;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-default);
}

.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(30rem, 1fr);
  gap: 1.6rem;
  min-height: 31rem;
}

.overview-card {
  display: flex;
  min-width: 0;
  padding: 2rem 2.4rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-default);
}

.map-card,
.urgent-card {
  flex-direction: column;
  gap: 1.6rem;
}

.overview-header h2 {
  margin: 0;
  font-size: var(--krds-pc-font-size-heading-xsmall);
}

.overview-header p {
  margin: 0.4rem 0 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
}

.robot-list-map {
  flex: 1;
  min-height: 22rem;
}

.urgent-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.2rem;
}

.urgent-count {
  flex-shrink: 0;
  padding: 0.3rem 0.8rem;
  border-radius: 999px;
  color: var(--roady-status-danger);
  background: color-mix(in srgb, var(--roady-status-danger) 10%, transparent);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
}

.urgent-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  max-height: 23rem;
  padding: 0;
  margin: 0;
  overflow-y: auto;
  list-style: none;
}

.urgent-list li {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  padding: 1.2rem 0;
  border-bottom: 1px solid var(--roady-border-default);
}

.urgent-list li:last-child {
  border-bottom: 0;
}

.urgent-robot-link {
  align-self: flex-start;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  text-underline-offset: 0.3rem;
}

.urgent-reasons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.urgent-reasons span {
  padding: 0.3rem 0.7rem;
  border-radius: 0.4rem;
  color: var(--roady-status-danger);
  background: color-mix(in srgb, var(--roady-status-danger) 9%, transparent);
  font-size: var(--krds-pc-font-size-label-xsmall);
  font-weight: var(--krds-font-weight-bold);
}

.list-toolbar {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) minmax(17rem, max-content);
  align-items: end;
  gap: 1.2rem;
  padding: 1.6rem 2rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-default);
}

.list-toolbar > :deep(.form-group) {
  min-width: 0;
}

.list-toolbar :deep(.krds-form-select),
.list-toolbar :deep(.krds-input) {
  width: 100%;
  min-width: 0;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 0.6rem;
}

.search-button,
.filter-reset {
  height: 4.8rem;
  min-width: 0;
  padding: 0 1rem;
  border-radius: 0.6rem;
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  cursor: pointer;
}

.search-button {
  flex: 0 0 6.4rem;
  border: 1px solid var(--roady-brand-primary);
  color: var(--roady-surface-default);
  background: var(--roady-brand-primary);
}

.search-button:hover {
  background: var(--roady-brand-primary-hover);
}

.filter-reset {
  flex: 1 1 9.6rem;
  border: 1px solid var(--roady-border-default);
  color: var(--roady-text-secondary);
  background: var(--roady-surface-default);
}

.filter-reset:hover:not(:disabled) {
  border-color: var(--roady-brand-secondary);
  color: var(--roady-brand-secondary);
}

.filter-reset:disabled {
  cursor: default;
  opacity: 0.45;
}

.table-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
}

.col-name {
  width: 14%;
}

.col-serial {
  width: 24%;
}

.col-operation,
.col-connection {
  width: 13%;
}

.col-battery {
  width: 9%;
}

.col-updated {
  width: 17%;
}

.col-detail {
  width: 10%;
}

th,
td {
  overflow: hidden;
  padding: 1.6rem 1.8rem;
  border-bottom: 1px solid var(--roady-border-default);
  text-align: left;
  font-size: var(--krds-pc-font-size-body-small);
  white-space: nowrap;
}

th {
  color: var(--roady-text-secondary);
  background: var(--roady-surface-subtle);
  font-weight: var(--krds-font-weight-bold);
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr:hover {
  background: var(--roady-surface-background);
}

.robot-name {
  color: var(--roady-text-primary);
  font-weight: var(--krds-font-weight-bold);
}

.serial-number {
  text-overflow: ellipsis;
}

.battery-cell,
.updated-cell {
  text-align: center;
}

.low-battery {
  color: var(--roady-status-danger);
  font-weight: var(--krds-font-weight-bold);
}

.detail-cell {
  text-align: right;
}

.detail-link {
  color: var(--roady-brand-secondary);
  font-weight: var(--krds-font-weight-bold);
  text-underline-offset: 0.3rem;
}

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

@media (max-width: 768px) {
  .robot-list {
    padding: 2rem;
  }

  .list-toolbar {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1100px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .list-toolbar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .filter-reset {
    justify-self: start;
  }

  .toolbar-actions {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .list-toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
