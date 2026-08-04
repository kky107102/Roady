<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { damagesApi } from '@/api/damages'
import type { DamageDetail, DamageImage, DamageListItem } from '@/types/damage'
import type { BadgeType } from '@/components/common/StatusBadge.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorState from '@/components/common/ErrorState.vue'

const props = withDefaults(
  defineProps<{
    damageId: number | null
    summary?: DamageListItem | null
  }>(),
  {
    summary: null,
  },
)
const emit = defineEmits<{ close: [] }>()

// ── 상태 ──────────────────────────────────────────────────

const detail = ref<DamageDetail | null>(null)
const imageBlobUrls = ref<Map<number, string>>(new Map())
const imagesLoading = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)
let fetchSeq = 0

// ── 이미지 로드 ────────────────────────────────────────────

async function loadImages(d: DamageDetail, seq: number) {
  imagesLoading.value = true
  const urls = new Map<number, string>()

  await Promise.allSettled(
    d.images.map(async (img: DamageImage) => {
      try {
        const blob = await damagesApi.getImageContent(d.id, img.id)
        if (seq === fetchSeq) {
          urls.set(img.id, URL.createObjectURL(blob))
        }
      } catch {
        // 개별 이미지 실패는 무시
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

// ── 데이터 조회 ────────────────────────────────────────────

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
    if (d.images.length > 0) {
      loadImages(d, seq)
    }
  } catch {
    if (seq !== fetchSeq) return
    error.value = '사건 정보를 불러오지 못했습니다.'
  } finally {
    if (seq === fetchSeq) loading.value = false
  }
}

watch(
  () => props.damageId,
  (id) => {
    if (id != null) fetchDetail(id)
  },
  { immediate: true },
)

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

onMounted(() => document.addEventListener('keydown', handleKeydown))
onUnmounted(() => {
  ++fetchSeq
  document.removeEventListener('keydown', handleKeydown)
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

function formatDateTime(str: string | null): string {
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

function formatCoords(lat: number | null, lng: number | null): string {
  if (lat == null || lng == null) return '위치 정보 없음'
  return `위도 ${lat.toFixed(4)}, 경도 ${lng.toFixed(4)}`
}

function formatLocation(damage: DamageDetail): string {
  const address = damage.roadAddressName?.trim() || damage.addressName?.trim()
  if (address) return `${address} 주변`
  return formatCoords(damage.latitude, damage.longitude)
}

const currentStatusInfo = computed(() => {
  const status = detail.value?.currentStatus
  if (!status) return null
  return REPAIR_STATUS_MAP[status] ?? { label: status, type: 'neutral' as BadgeType }
})

const processingPriority = computed(
  () => detail.value?.processingPriority ?? props.summary?.processingPriority ?? null,
)

const priorityLabel = computed(() => {
  const p = processingPriority.value
  if (!p) return '미지정'
  return PRIORITY_LABELS[p] ?? p
})

const priorityType = computed<BadgeType>(() => {
  const p = processingPriority.value
  return p ? (PRIORITY_BADGE_TYPES[p] ?? 'neutral') : 'neutral'
})

const reviewDamageType = computed(
  () => detail.value?.reviewDamageType ?? props.summary?.reviewDamageType ?? null,
)

const damageTypeLabel = computed(() => {
  const t = reviewDamageType.value
  if (!t) return '-'
  return DAMAGE_TYPE_LABELS[t] ?? t
})

const reviewNote = computed(
  () => detail.value?.reviewNote ?? props.summary?.reviewNote ?? null,
)

const loadedImages = computed(() =>
  (detail.value?.images ?? []).filter((image) => imageBlobUrls.value.has(image.id)),
)
</script>

<template>
  <aside class="detail-panel" aria-label="보수 사건 상세 정보">
    <!-- 로딩 -->
    <div v-if="loading" class="detail-loading">
      <LoadingSpinner label="사건 정보 불러오는 중" />
    </div>

    <!-- 오류 -->
    <ErrorState
      v-else-if="error"
      :message="error"
      @retry="damageId != null && fetchDetail(damageId)"
    />

    <!-- 내용 -->
    <template v-else-if="detail">
      <!-- ── 고정 헤더 ── -->
      <div class="detail-head">
        <h2 class="detail-head-title">보수 사건 상세</h2>
        <button type="button" class="detail-close" aria-label="닫기" @click="emit('close')">
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <!-- ── 스크롤 본문 ── -->
      <div class="detail-body">
        <!-- 1. 사건 핵심 정보 -->
        <div class="case-hero">
          <div class="case-badges">
            <span class="badge-case-id">{{ formatCaseId(detail.id, detail.createdAt) }}</span>
            <StatusBadge :type="priorityType" :label="priorityLabel" />
          </div>

          <h3 class="case-title">{{ detail.description ?? '설명 없음' }}</h3>

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
              {{ formatDateTime(detail.capturedAt) }}
            </span>
          </div>
        </div>

        <!-- 2. 현재 보수 상태 -->
        <div v-if="currentStatusInfo" class="status-section">
          <span class="status-section-label">현재 보수 상태</span>
          <StatusBadge :type="currentStatusInfo.type" :label="currentStatusInfo.label" />
        </div>

        <!-- 3. 관리자 판정 -->
        <section class="manager-review-card" aria-label="관리자 판정">
          <h3 class="manager-review-title">관리자 판정</h3>
          <div class="manager-review-grid">
            <div class="manager-review-item">
              <span class="manager-review-label">우선순위</span>
              <StatusBadge :type="priorityType" :label="priorityLabel" />
            </div>
            <div class="manager-review-item">
              <span class="manager-review-label">파손 유형</span>
              <StatusBadge type="neutral" :label="damageTypeLabel" />
            </div>
            <div v-if="reviewNote" class="manager-review-item manager-review-note">
              <span class="manager-review-label">비고</span>
              <p>{{ reviewNote }}</p>
            </div>
          </div>
        </section>

        <!-- 4. 탐지 이미지 -->
        <div class="images-section">
          <h3 class="images-title">탐지 이미지</h3>

          <div class="image-frame">
            <div v-if="detail.imageCount > 0 && imagesLoading" class="image-loading">
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
            <div v-else-if="detail.imageCount > 0" class="no-image-notice">
              이미지를 불러올 수 없습니다.
            </div>
            <div v-else class="no-image-notice">등록된 탐지 이미지가 없습니다.</div>
          </div>
        </div>
      </div>
    </template>
  </aside>
</template>

<style scoped>
/* ── 패널 기본 ── */
.detail-panel {
  display: flex;
  flex-direction: column;
  container-type: inline-size;
  height: 100%;
  background: var(--roady-surface-default);
  border-left: 1px solid var(--roady-border-default);
  overflow: hidden;
}

.detail-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  padding: 24px;
}

/* ── 고정 헤더 ── */
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 72px;
  padding: 0 24px;
  border-bottom: 1px solid var(--roady-border-default);
  flex-shrink: 0;
  background: var(--roady-surface-default);
}

.detail-head-title {
  margin: 0;
  font-size: 20px;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
  letter-spacing: -0.01em;
}

.detail-close {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--roady-text-tertiary);
  cursor: pointer;
  transition: background-color 0.12s;
}

.detail-close:hover {
  background: var(--roady-surface-subtle);
  color: var(--roady-text-primary);
}

/* ── 스크롤 본문 ── */
.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  min-height: 0;
}

.detail-body > * {
  flex-shrink: 0;
}

/* ── 사건 핵심 정보 ── */
.case-hero {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.case-badges {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.badge-case-id {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border: 1px solid var(--roady-border-default);
  border-radius: 6px;
  font-size: 12px;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-secondary);
  letter-spacing: 0.01em;
  background: var(--roady-surface-background);
  white-space: nowrap;
}

.case-title {
  margin: 0;
  font-size: 28px;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
  line-height: 1.3;
  word-break: break-word;
  letter-spacing: -0.01em;
}

.case-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 2px;
}

.case-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  color: var(--roady-text-secondary);
  line-height: 1.4;
}

.case-meta-item svg {
  flex-shrink: 0;
  color: var(--roady-text-tertiary);
}

/* ── 현재 보수 상태 ── */
.status-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--roady-border-default);
  border-radius: 8px;
  background: var(--roady-surface-background);
}

.status-section-label {
  font-size: 14px;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-secondary);
}

/* ── 관리자 판정 카드 ── */
.manager-review-card {
  padding: 14px 16px;
  border: 1px solid var(--roady-brand-secondary);
  border-radius: 8px;
  background: color-mix(in srgb, var(--roady-brand-primary-subtle) 55%, #fff);
}

.manager-review-title {
  margin: 0 0 12px;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
}

.manager-review-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
}

.manager-review-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.manager-review-label {
  flex-shrink: 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
}

.manager-review-note {
  grid-column: 1 / -1;
  align-items: flex-start;
}

.manager-review-note p {
  margin: 0;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-small);
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

/* ── 탐지 이미지 섹션 ── */
.images-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.images-title {
  margin: 0;
  font-size: 16px;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
}

.image-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  min-height: 180px;
  max-height: 280px;
  overflow: hidden;
  border-radius: 8px;
  background: var(--roady-surface-background);
}

.image-grid {
  display: flex;
  gap: 8px;
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
  flex: 0 0 calc((100% - 8px) / 2);
  min-width: 0;
  object-fit: cover;
  background: var(--roady-surface-subtle);
  display: block;
  scroll-snap-align: start;
}

.image-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.no-image-notice {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 14px;
  color: var(--roady-text-tertiary);
  text-align: center;
  padding: 24px;
  border: 1px dashed var(--roady-border-default);
  border-radius: 8px;
  background: var(--roady-surface-background);
}

@media (max-width: 600px) {
  .detail-body {
    padding: 20px;
  }

  .detail-head {
    min-height: 64px;
    padding: 0 20px;
  }

  .image-frame {
    min-height: 160px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .detail-close {
    transition: none;
  }
}
</style>
