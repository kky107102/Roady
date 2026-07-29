<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import DashboardToolbar from '@/components/dashboard/DashboardToolbar.vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import TrendChart from '@/components/dashboard/TrendChart.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useDashboardStore()

const REFRESH_MS = 5 * 60 * 1000

let refreshTimer: ReturnType<typeof setInterval> | null = null

function handleVisibilityChange() {
  if (!document.hidden) store.fetchAll()
}

onMounted(() => {
  store.fetchAll()
  refreshTimer = setInterval(() => {
    if (!document.hidden) store.fetchAll()
  }, REFRESH_MS)
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  if (refreshTimer !== null) clearInterval(refreshTimer)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<template>
  <div class="dashboard">
    <!-- 조회 조건 툴바 -->
    <div class="dashboard__toolbar">
      <DashboardToolbar v-model="store.filter" @apply="store.applyFilter" />
    </div>

    <!-- 로딩 오버레이 -->
    <div v-if="store.loading" class="dashboard__loading">
      <LoadingSpinner label="대시보드 데이터 불러오는 중" />
    </div>

    <!-- 인라인 에러 배너 (레이아웃은 유지) -->
    <div v-if="store.error && !store.loading" class="dashboard__error-banner" role="alert">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <span>{{ store.error }}</span>
      <button type="button" class="error-banner__retry" @click="store.fetchAll">다시 시도</button>
    </div>

      <!-- 통계 요약 카드 -->
      <section class="dashboard__stats" aria-label="통계 요약">
        <StatCard label="신규 탐지" :count="store.totalCount" :to="{ name: 'damages' }">
          <template #icon>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
          </template>
        </StatCard>

        <StatCard label="긴급 / 고위험" :count="store.highSeverityCount" variant="danger" :to="{ name: 'damages', query: { severity: 'HIGH' } }">
          <template #icon>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </template>
        </StatCard>

        <StatCard label="검토 대기" :count="store.reviewRequiredCount" :to="{ name: 'damages', query: { status: 'REVIEW_REQUIRED' } }">
          <template #icon>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
          </template>
        </StatCard>

        <StatCard label="진행 중 보수" :count="store.repairingCount" :to="{ name: 'repairs' }">
          <template #icon>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </template>
        </StatCard>

        <StatCard label="운행 중 로디" :count="store.activeRobotCount" variant="dark" :to="{ name: 'robots' }">
          <template #icon>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
          </template>
        </StatCard>
      </section>

      <!-- 메인 콘텐츠 영역 -->
      <div class="dashboard__main">
        <!-- 지도 영역 (별도 작업 S15P11A404-137) -->
        <section class="dashboard__map-section" aria-label="도로 파손 실시간 현황">
          <div class="section-header">
            <div>
              <h2 class="section-title">도로 파손 실시간 현황</h2>
              <p class="section-subtitle">지도 서비스 연동은 S15P11A404-137에서 구현됩니다.</p>
            </div>
          </div>
          <div class="map-placeholder">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/>
              <line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
            </svg>
            <p>지도 연동 구현 예정</p>
          </div>
        </section>

        <!-- 신규 탐지 알림 (별도 작업 S15P11A404-148) -->
        <section class="dashboard__alert-section" aria-label="신규 탐지 알림">
          <div class="section-header">
            <h2 class="section-title">신규 탐지 알림</h2>
          </div>
          <div class="panel-placeholder">
            <p>탐지 알림 목록은 S15P11A404-148에서 구현됩니다.</p>
          </div>
        </section>
      </div>

      <!-- 하단 콘텐츠 영역 -->
      <div class="dashboard__bottom">
        <!-- 탐지 추이 차트 -->
        <section class="dashboard__chart-section" aria-label="탐지 추이 분석">
          <div class="section-header">
            <div>
              <h2 class="section-title">탐지 추이 분석</h2>
              <p class="section-subtitle">
                지난 7일간 일별 탐지 건수
                <span class="mock-badge" aria-label="임시 데이터">임시 데이터</span>
              </p>
            </div>
          </div>
          <TrendChart :data="store.timeSeries" />
        </section>

        <!-- 긴급 확인 필요 사건 (별도 작업) -->
        <section class="dashboard__urgent-section" aria-label="긴급 확인 필요 사건">
          <div class="section-header">
            <h2 class="section-title">긴급 확인 필요 사건</h2>
          </div>
          <div class="panel-placeholder">
            <p>긴급 사건 목록은 추후 구현됩니다.</p>
          </div>
        </section>
      </div>
  </div>
</template>

<style scoped>
.dashboard {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding: 2.4rem 3.2rem;
  min-width: 0;
}

/* ── 로딩 오버레이 ── */
.dashboard__loading {
  position: absolute;
  inset: 0;
  z-index: 10;
  background: rgb(255 255 255 / 60%);
}

/* ── 에러 배너 ── */
.dashboard__error-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.6rem;
  border-radius: 0.6rem;
  border: 1px solid var(--roady-status-danger);
  background: color-mix(in srgb, var(--roady-status-danger) 8%, transparent);
  color: var(--roady-status-danger);
  font-size: var(--krds-pc-font-size-body-small);
}

.dashboard__error-banner span {
  flex: 1;
  color: var(--roady-text-primary);
}

.error-banner__retry {
  flex-shrink: 0;
  padding: 0.4rem 1.2rem;
  border: 1px solid var(--roady-status-danger);
  border-radius: 0.4rem;
  color: var(--roady-status-danger);
  background: transparent;
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  cursor: pointer;
  transition: background-color 0.15s;
}

.error-banner__retry:hover {
  background: color-mix(in srgb, var(--roady-status-danger) 10%, transparent);
}

/* ── 툴바 ── */
.dashboard__toolbar {
  display: flex;
  justify-content: flex-end;
}

/* ── 통계 카드 행 ── */
.dashboard__stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1.6rem;
}

/* ── 메인 영역 (지도 + 알림) ── */
.dashboard__main {
  display: grid;
  grid-template-columns: 1fr 38rem;
  gap: 1.6rem;
  min-height: 36rem;
}

/* ── 하단 영역 (차트 + 긴급) ── */
.dashboard__bottom {
  display: grid;
  grid-template-columns: 1fr 38rem;
  gap: 1.6rem;
}

/* ── 공통 섹션 카드 ── */
.dashboard__map-section,
.dashboard__alert-section,
.dashboard__chart-section,
.dashboard__urgent-section {
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
  padding: 2rem 2.4rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-default);
  min-width: 0;
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.2rem;
}

.section-title {
  margin: 0;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-body-medium);
  font-weight: var(--krds-font-weight-bold);
}

.section-subtitle {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin: 0.4rem 0 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
}

/* ── 지도 placeholder ── */
.map-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.2rem;
  border-radius: 0.6rem;
  background: var(--roady-surface-background);
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
}

/* ── 패널 placeholder ── */
.panel-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.6rem;
  background: var(--roady-surface-background);
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
  padding: 2.4rem;
  text-align: center;
}

/* ── 임시 데이터 배지 ── */
.mock-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.6rem;
  border-radius: 0.4rem;
  background: color-mix(in srgb, var(--roady-status-warning) 15%, transparent);
  color: var(--roady-status-warning);
  font-size: 1.1rem;
  font-weight: var(--krds-font-weight-bold);
  letter-spacing: 0.02em;
}

/* ── 1440px 이하 대응 ── */
@media (max-width: 1440px) {
  .dashboard__stats {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (max-width: 1280px) {
  .dashboard__main,
  .dashboard__bottom {
    grid-template-columns: 1fr;
  }
}
</style>
