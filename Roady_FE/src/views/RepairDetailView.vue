<script setup lang="ts">
import { ref, watch, computed, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { damagesApi } from '@/api/damages'
import type { DamageDetail, DamageImage } from '@/types/damage'
import type { BadgeType } from '@/components/common/StatusBadge.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorState from '@/components/common/ErrorState.vue'

// ── 라우터 ──────────────────────────────────────────────────
const route = useRoute()
const router = useRouter()

const damageId = computed(() => {
  const raw = route.params.damageId
  const id = Number(Array.isArray(raw) ? raw[0] : raw)
  return Number.isFinite(id) && id > 0 ? id : null
})

function handleBack() {
  const backTo = route.query.backTo
  const target = typeof backTo === 'string' && backTo.startsWith('/') ? backTo : '/repairs'
  router.push(target)
}

// ── 데이터 ─────────────────────────────────────────────────
const detail = ref<DamageDetail | null>(null)
const imageBlobUrls = ref<Map<number, string>>(new Map())
const imagesLoading = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)
let fetchSeq = 0

async function loadImages(d: DamageDetail, seq: number) {
  imagesLoading.value = true
  const urls = new Map<number, string>()
  await Promise.allSettled(
    d.images.map(async (img: DamageImage) => {
      try {
        const blob = await damagesApi.getImageContent(d.id, img.id)
        if (seq === fetchSeq) urls.set(img.id, URL.createObjectURL(blob))
      } catch {
        // 개별 이미지 실패 무시
      }
    }),
  )
  if (seq !== fetchSeq) {
    for (const url of urls.values()) URL.revokeObjectURL(url)
    return
  }
  imageBlobUrls.value = urls
  imagesLoading.value = false
}

async function fetchDetail(id: number) {
  const seq = ++fetchSeq
  loading.value = true
  error.value = null
  detail.value = null
  imagesLoading.value = false
  for (const url of imageBlobUrls.value.values()) URL.revokeObjectURL(url)
  imageBlobUrls.value = new Map()
  try {
    const d = await damagesApi.getDetail(id)
    if (seq !== fetchSeq) return
    detail.value = d
    if (d.images.length > 0) loadImages(d, seq)
  } catch {
    if (seq !== fetchSeq) return
    error.value = '사건 정보를 불러오지 못했습니다.'
  } finally {
    if (seq === fetchSeq) loading.value = false
  }
}

watch(
  damageId,
  (id) => { if (id != null) fetchDetail(id) },
  { immediate: true },
)

onUnmounted(() => {
  ++fetchSeq
  for (const url of imageBlobUrls.value.values()) URL.revokeObjectURL(url)
})

// ── 표시 헬퍼 ─────────────────────────────────────────────
const PRIORITY_LABELS: Record<string, string> = {
  URGENT: '긴급',
  HIGH: '높음',
  NORMAL: '보통',
  MEDIUM: '보통',
  LOW: '낮음',
}

const PRIORITY_BADGE_TYPES: Record<string, BadgeType> = {
  URGENT: 'danger',
  HIGH: 'warning',
  NORMAL: 'info',
  MEDIUM: 'info',
  LOW: 'neutral',
}

const DAMAGE_TYPE_LABELS: Record<string, string> = {
  LARGE_MISSING: '큰 결손',
  SMALL_MISSING: '작은 결손',
  MISSING: '큰 결손',
  WEAR: '마모',
  BREAKAGE: '작은 결손',
  CRACK: '균열',
  OTHER: '기타',
}

const REPAIR_STATUS_MAP: Record<string, { label: string; type: BadgeType }> = {
  REQUESTED: { label: '요청 전', type: 'warning' },
  REPAIR_IN_PROGRESS: { label: '요청 완료', type: 'info' },
  REPAIR_COMPLETED: { label: '보수 완료', type: 'success' },
}

function formatCaseId(id: number, createdAt: string): string {
  const year = new Date(createdAt).getFullYear()
  return `RD-${year}-${String(id).padStart(6, '0')}`
}

function formatDateTime(str: string | null | undefined): string {
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

function formatLocation(d: DamageDetail): string {
  const address = d.roadAddressName?.trim() || d.addressName?.trim()
  if (address) return `${address} 주변`
  if (d.latitude != null && d.longitude != null)
    return `위도 ${d.latitude.toFixed(4)}, 경도 ${d.longitude.toFixed(4)}`
  return '위치 정보 없음'
}

const currentStatusInfo = computed(() => {
  const status = detail.value?.currentStatus
  if (!status) return null
  return REPAIR_STATUS_MAP[status] ?? { label: status, type: 'neutral' as BadgeType }
})

const priorityLabel = computed(() => {
  const p = detail.value?.processingPriority
  if (!p) return '미지정'
  return PRIORITY_LABELS[p] ?? p
})

const priorityType = computed<BadgeType>(() => {
  const p = detail.value?.processingPriority
  return p ? (PRIORITY_BADGE_TYPES[p] ?? 'neutral') : 'neutral'
})

const damageTypeLabel = computed(() => {
  const t = detail.value?.reviewDamageType
  if (!t) return '-'
  return DAMAGE_TYPE_LABELS[t] ?? t
})

const loadedImages = computed(() =>
  (detail.value?.images ?? []).filter((img) => imageBlobUrls.value.has(img.id)),
)
</script>

<template>
  <div class="repair-detail-view">
    <!-- 페이지 헤더 -->
    <div class="page-head">
      <button type="button" class="back-btn" aria-label="목록으로 돌아가기" @click="handleBack">
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <line x1="19" y1="12" x2="5" y2="12" />
          <polyline points="12 19 5 12 12 5" />
        </svg>
        목록으로
      </button>
      <h1 class="page-title">보수 사건 상세</h1>
    </div>

    <!-- 로딩 -->
    <div v-if="loading" class="page-state">
      <LoadingSpinner label="사건 정보 불러오는 중" />
    </div>

    <!-- 오류 -->
    <div v-else-if="error" class="page-state">
      <ErrorState :message="error" @retry="damageId != null && fetchDetail(damageId)" />
    </div>

    <!-- damageId 없음 -->
    <div v-else-if="damageId == null" class="page-state">
      <ErrorState message="올바른 사건 ID가 필요합니다." />
    </div>

    <!-- 본문 -->
    <div v-else-if="detail" class="page-body">
      <!-- ── 사건 핵심 정보 ── -->
      <section class="case-hero" aria-label="사건 핵심 정보">
        <div class="case-badges">
          <span class="badge-case-id">{{ formatCaseId(detail.id, detail.createdAt) }}</span>
          <StatusBadge :type="priorityType" :label="priorityLabel" />
          <StatusBadge
            v-if="currentStatusInfo"
            :type="currentStatusInfo.type"
            :label="currentStatusInfo.label"
          />
        </div>
        <h2 class="case-title">{{ detail.description ?? '설명 없음' }}</h2>
        <div class="case-meta">
          <span class="case-meta-item">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              aria-hidden="true"
            >
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
            {{ formatLocation(detail) }}
          </span>
          <span class="case-meta-item">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            탐지: {{ formatDateTime(detail.capturedAt) }}
          </span>
          <span class="case-meta-item">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              aria-hidden="true"
            >
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            최근 변경: {{ formatDateTime(detail.updatedAt) }}
          </span>
        </div>
      </section>

      <!-- 두 컬럼 레이아웃 -->
      <div class="two-col">
        <!-- 왼쪽: 관리자 판정 + 이미지 -->
        <div class="col-main">
          <!-- 관리자 판정 -->
          <section class="card" aria-label="관리자 판정">
            <h3 class="card-title">관리자 판정</h3>
            <div class="review-grid">
              <div class="review-item">
                <span class="review-label">우선순위</span>
                <StatusBadge :type="priorityType" :label="priorityLabel" />
              </div>
              <div class="review-item">
                <span class="review-label">파손 유형</span>
                <StatusBadge type="neutral" :label="damageTypeLabel" />
              </div>
              <div v-if="detail.reviewNote" class="review-item review-note-item">
                <span class="review-label">비고</span>
                <p class="review-note">{{ detail.reviewNote }}</p>
              </div>
            </div>
          </section>

          <!-- 탐지 이미지 -->
          <section class="card" aria-label="탐지 이미지">
            <h3 class="card-title">탐지 이미지</h3>
            <div class="image-frame">
              <div v-if="detail.imageCount > 0 && imagesLoading" class="image-state">
                <LoadingSpinner label="이미지 불러오는 중" />
              </div>
              <div
                v-else-if="loadedImages.length > 0"
                :class="['image-grid', { 'image-grid--single': loadedImages.length === 1 }]"
              >
                <img
                  v-for="img in loadedImages"
                  :key="img.id"
                  :src="imageBlobUrls.get(img.id)"
                  :alt="`파손 이미지 ${img.sortOrder}`"
                  class="detail-img"
                />
              </div>
              <div v-else-if="detail.imageCount > 0" class="no-image">
                이미지를 불러올 수 없습니다.
              </div>
              <div v-else class="no-image">등록된 탐지 이미지가 없습니다.</div>
            </div>
          </section>
        </div>

        <!-- 오른쪽: 보수 상태 이력 영역 (향후 확장용 플레이스홀더) -->
        <div class="col-side">
          <section class="card" aria-label="보수 현황">
            <h3 class="card-title">보수 현황</h3>
            <div class="status-row">
              <span class="status-row-label">현재 상태</span>
              <StatusBadge
                v-if="currentStatusInfo"
                :type="currentStatusInfo.type"
                :label="currentStatusInfo.label"
              />
              <span v-else class="text-tertiary">-</span>
            </div>
            <p class="side-note">보수 요청·완료 처리는 현장 담당자 앱에서 진행됩니다.</p>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.repair-detail-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* ── 페이지 헤더 ── */
.page-head {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  padding: 0 2rem;
  min-height: 6.4rem;
  border-bottom: 1px solid var(--roady-border-default);
  background: var(--roady-surface-default);
  flex-shrink: 0;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.8rem 1.2rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.6rem;
  background: var(--roady-surface-default);
  color: var(--roady-text-secondary);
  font-size: 1.4rem;
  font-weight: var(--krds-font-weight-bold);
  cursor: pointer;
  transition: background-color 0.1s;
  white-space: nowrap;
}

.back-btn:hover {
  background: var(--roady-surface-background);
  color: var(--roady-text-primary);
}

.back-btn:focus-visible {
  outline: 2px solid var(--roady-focus-ring);
  outline-offset: 2px;
}

.page-title {
  margin: 0;
  font-size: 2rem;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
  letter-spacing: -0.01em;
}

/* ── 상태 행 (로딩/에러) ── */
.page-state {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  padding: 4rem 2rem;
}

/* ── 본문 ── */
.page-body {
  flex: 1;
  overflow-y: auto;
  padding: 2.4rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  min-height: 0;
}

/* ── 사건 핵심 정보 ── */
.case-hero {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.case-badges {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  flex-wrap: wrap;
}

.badge-case-id {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 6px;
  font-size: 1.2rem;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-secondary);
  letter-spacing: 0.01em;
  background: var(--roady-surface-background);
  font-family: monospace;
  white-space: nowrap;
}

.case-title {
  margin: 0;
  font-size: 2.4rem;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
  line-height: 1.3;
  word-break: break-word;
  letter-spacing: -0.01em;
}

.case-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 2rem;
}

.case-meta-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 1.4rem;
  color: var(--roady-text-secondary);
}

.case-meta-item svg {
  flex-shrink: 0;
  color: var(--roady-text-tertiary);
}

/* ── 두 컬럼 레이아웃 ── */
.two-col {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 2rem;
  align-items: start;
}

.col-main {
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
}

.col-side {
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
}

/* ── 카드 ── */
.card {
  padding: 1.6rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-default);
}

.card-title {
  margin: 0 0 1.4rem;
  font-size: 1.6rem;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
}

/* ── 관리자 판정 그리드 ── */
.review-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.2rem 2rem;
}

.review-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.review-label {
  flex-shrink: 0;
  font-size: 1.3rem;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-tertiary);
  min-width: 5.6rem;
}

.review-note-item {
  grid-column: 1 / -1;
  align-items: flex-start;
}

.review-note {
  margin: 0;
  font-size: 1.4rem;
  color: var(--roady-text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

/* ── 탐지 이미지 ── */
.image-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  min-height: 200px;
  max-height: 360px;
  overflow: hidden;
  border-radius: 0.8rem;
  background: var(--roady-surface-background);
}

.image-grid {
  display: flex;
  gap: 0.8rem;
  width: 100%;
  height: 100%;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
}

.image-grid--single .detail-img {
  flex-basis: 100%;
}

.detail-img {
  width: 100%;
  height: 100%;
  flex: 0 0 calc((100% - 0.8rem) / 2);
  min-width: 0;
  object-fit: cover;
  background: var(--roady-surface-subtle);
  display: block;
  scroll-snap-align: start;
}

.image-state {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.no-image {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 1.4rem;
  color: var(--roady-text-tertiary);
  text-align: center;
  padding: 2.4rem;
  border: 1px dashed var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-background);
}

/* ── 사이드 카드 ── */
.status-row {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  padding: 1rem 0;
}

.status-row-label {
  font-size: 1.3rem;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-tertiary);
  min-width: 6rem;
}

.side-note {
  margin: 1.2rem 0 0;
  padding: 1rem 1.2rem;
  border-radius: 0.6rem;
  background: var(--roady-surface-background);
  font-size: 1.3rem;
  color: var(--roady-text-tertiary);
  line-height: 1.5;
}

.text-tertiary {
  color: var(--roady-text-tertiary);
  font-size: 1.4rem;
}

/* ── 반응형 ── */
@media (max-width: 900px) {
  .two-col {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .page-body {
    padding: 1.6rem;
  }

  .case-title {
    font-size: 2rem;
  }

  .review-grid {
    grid-template-columns: 1fr;
  }
}
</style>
