<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { damagesApi } from '@/api/damages'
import type { DamageDetail, DamageImage, DamageAnalysis, DamageStatus } from '@/types/damage'
import type { BadgeType } from '@/components/common/StatusBadge.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorState from '@/components/common/ErrorState.vue'

const props = defineProps<{ damageId: number | null }>()
const emit = defineEmits<{ close: [] }>()

// ── 상태 ──────────────────────────────────────────────────

const detail = ref<DamageDetail | null>(null)
const analyses = ref<DamageAnalysis[]>([])
const imageBlobUrls = ref<Map<number, string>>(new Map())
const loading = ref(false)
const error = ref<string | null>(null)

const latestAnalysis = computed<DamageAnalysis | null>(() =>
  analyses.value.find((a) => a.analysisStatus === 'SUCCESS' || a.analysisStatus === 'CONFIRMED') ??
  analyses.value[0] ??
  null,
)

// ── 이미지 로드 ────────────────────────────────────────────

async function loadImages(d: DamageDetail) {
  // 기존 blob URL 해제
  for (const url of imageBlobUrls.value.values()) URL.revokeObjectURL(url)
  imageBlobUrls.value = new Map()

  const urls = new Map<number, string>()
  await Promise.allSettled(
    d.images.map(async (img: DamageImage) => {
      try {
        const blob = await damagesApi.getImageContent(d.id, img.id)
        urls.set(img.id, URL.createObjectURL(blob))
      } catch {
        // 개별 이미지 실패는 무시
      }
    }),
  )
  imageBlobUrls.value = urls
}

// ── 데이터 조회 ────────────────────────────────────────────

async function fetchDetail(id: number) {
  loading.value = true
  error.value = null
  detail.value = null
  analyses.value = []

  try {
    const [d, a] = await Promise.all([
      damagesApi.getDetail(id),
      damagesApi.getAnalysisJobs(id).catch(() => [] as DamageAnalysis[]),
    ])
    detail.value = d
    analyses.value = a
    if (d.images.length > 0) await loadImages(d)
  } catch {
    error.value = '사건 정보를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

watch(
  () => props.damageId,
  (id) => {
    if (id != null) fetchDetail(id)
  },
  { immediate: true },
)

// ── 표시 헬퍼 ─────────────────────────────────────────────

const STATUS_LABELS: Record<DamageStatus, string> = {
  COLLECTED: '탐지됨',
  REVIEW_REQUIRED: '검토 필요',
  RECEIVED: '접수됨',
  REPAIR_SCHEDULED: '보수 예정',
  REPAIRING: '보수 중',
  REPAIR_COMPLETED: '보수 완료',
  REPAIR_NOT_REQUIRED: '보수 불필요',
}

const STATUS_BADGE_TYPES: Record<DamageStatus, BadgeType> = {
  COLLECTED: 'neutral',
  REVIEW_REQUIRED: 'warning',
  RECEIVED: 'info',
  REPAIR_SCHEDULED: 'info',
  REPAIRING: 'warning',
  REPAIR_COMPLETED: 'success',
  REPAIR_NOT_REQUIRED: 'neutral',
}

const PRIORITY_LABELS: Record<string, string> = {
  URGENT: '긴급 보수',
  HIGH: '주의 보수',
  MEDIUM: '일반 보수',
  LOW: '낮은 우선순위',
}

const PRIORITY_BADGE_TYPES: Record<string, BadgeType> = {
  URGENT: 'danger',
  HIGH: 'warning',
  MEDIUM: 'info',
  LOW: 'neutral',
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
</script>

<template>
  <aside class="detail-panel" aria-label="사건 상세 정보">
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
      <!-- 헤더 -->
      <div class="detail-head">
        <div class="detail-badges">
          <span class="detail-case-id">{{ formatCaseId(detail.id, detail.createdAt) }}</span>
          <StatusBadge
            v-if="latestAnalysis?.repairPriority"
            :type="PRIORITY_BADGE_TYPES[latestAnalysis.repairPriority] ?? 'neutral'"
            :label="PRIORITY_LABELS[latestAnalysis.repairPriority] ?? latestAnalysis.repairPriority"
          />
        </div>
        <button type="button" class="detail-close" aria-label="닫기" @click="emit('close')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="detail-body">
        <h2 class="detail-title">{{ detail.description ?? '설명 없음' }}</h2>

        <p class="detail-location">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
          </svg>
          {{ formatCoords(detail.latitude, detail.longitude) }}
        </p>

        <!-- 이미지 영역 -->
        <div class="detail-images" v-if="detail.imageCount > 0">
          <div class="detail-images-label">
            <span>탐지 이미지</span>
            <span class="detail-robot">
              탐지 로봇: {{ detail.robotId != null ? `#${detail.robotId}` : '-' }}
            </span>
          </div>

          <div v-if="imageBlobUrls.size > 0" class="image-grid">
            <img
              v-for="img in detail.images"
              :key="img.id"
              :src="imageBlobUrls.get(img.id)"
              :alt="`파손 이미지 ${img.sortOrder}`"
              class="detail-img"
              v-show="imageBlobUrls.has(img.id)"
            />
          </div>
          <div v-else class="image-loading">
            <LoadingSpinner label="이미지 불러오는 중" />
          </div>
        </div>

        <div v-else class="no-image-notice">이미지 없음</div>

        <!-- 기본 정보 -->
        <div class="detail-meta">
          <div class="meta-item">
            <span class="meta-label">탐지 일시</span>
            <span class="meta-value">{{ formatDateTime(detail.capturedAt) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">사건 상태</span>
            <StatusBadge
              :type="STATUS_BADGE_TYPES[detail.currentStatus]"
              :label="STATUS_LABELS[detail.currentStatus]"
            />
          </div>
          <div class="meta-item">
            <span class="meta-label">담당자</span>
            <span class="meta-value">
              {{ detail.assignedTo != null ? `#${detail.assignedTo}` : '미배정' }}
            </span>
          </div>
          <div class="meta-item">
            <span class="meta-label">등록 일시</span>
            <span class="meta-value">{{ formatDateTime(detail.createdAt) }}</span>
          </div>
        </div>

        <!-- AI 분석 결과 -->
        <div v-if="latestAnalysis" class="detail-analysis">
          <h3 class="analysis-title">AI 분석 결과</h3>
          <div class="detail-meta">
            <div class="meta-item" v-if="latestAnalysis.damageScore != null">
              <span class="meta-label">파손 점수</span>
              <span class="meta-value">{{ latestAnalysis.damageScore }}점</span>
            </div>
            <div class="meta-item" v-if="latestAnalysis.confidenceScore != null">
              <span class="meta-label">신뢰도</span>
              <span class="meta-value">{{ Math.round(latestAnalysis.confidenceScore * 100) }}%</span>
            </div>
            <div class="meta-item" v-if="latestAnalysis.repairRequired != null">
              <span class="meta-label">보수 필요</span>
              <span class="meta-value">{{ latestAnalysis.repairRequired ? '예' : '아니오' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">분석 상태</span>
              <span class="meta-value">{{ latestAnalysis.analysisStatus }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 액션 버튼 (S15P11A404-149에서 API 연결 예정) -->
      <div class="detail-actions">
        <button type="button" class="krds-btn large filled primary action-btn" disabled title="추후 구현 예정">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
          </svg>
          보수 요청 작성
        </button>
        <div class="action-row">
          <button type="button" class="krds-btn large outline action-btn" disabled title="추후 구현 예정">
            담당자 지정
          </button>
          <button type="button" class="krds-btn large outline action-btn action-btn--danger" disabled title="추후 구현 예정">
            오탐 처리
          </button>
        </div>
      </div>
    </template>
  </aside>
</template>

<style scoped>
.detail-panel {
  display: flex;
  flex-direction: column;
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
  padding: 2rem;
}

/* ── 헤더 ── */
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.4rem 1.6rem;
  border-bottom: 1px solid var(--roady-border-default);
  flex-shrink: 0;
}

.detail-badges {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  flex-wrap: wrap;
  min-width: 0;
}

.detail-case-id {
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-brand-secondary);
  font-family: monospace;
  white-space: nowrap;
}

.detail-close {
  flex-shrink: 0;
  width: 3.2rem;
  height: 3.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 0.4rem;
  background: transparent;
  color: var(--roady-text-secondary);
  cursor: pointer;
  transition: background-color 0.12s;
}

.detail-close:hover {
  background: var(--roady-surface-subtle);
}

/* ── 본문 ── */
.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.6rem;
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
}

.detail-title {
  margin: 0;
  font-size: var(--krds-pc-font-size-heading-xsmall);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
  line-height: 1.4;
}

.detail-location {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  font-size: var(--krds-pc-font-size-body-small);
  color: var(--roady-text-secondary);
}

/* ── 이미지 ── */
.detail-images {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.detail-images-label {
  display: flex;
  justify-content: space-between;
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-secondary);
}

.detail-robot {
  font-weight: var(--krds-font-weight-regular);
  color: var(--roady-text-tertiary);
}

.image-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.8rem;
}

.detail-img {
  width: 100%;
  border-radius: 0.6rem;
  object-fit: cover;
  max-height: 22rem;
  background: var(--roady-surface-subtle);
}

.image-loading {
  display: flex;
  justify-content: center;
  padding: 2rem;
}

.no-image-notice {
  font-size: var(--krds-pc-font-size-body-small);
  color: var(--roady-text-tertiary);
  text-align: center;
  padding: 1.6rem;
  border: 1px dashed var(--roady-border-default);
  border-radius: 0.6rem;
}

/* ── 메타 정보 ── */
.detail-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.2rem 1.6rem;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.meta-label {
  font-size: var(--krds-pc-font-size-label-xsmall);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.meta-value {
  font-size: var(--krds-pc-font-size-body-small);
  color: var(--roady-text-primary);
}

/* ── AI 분석 ── */
.detail-analysis {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.2rem;
  border-radius: 0.6rem;
  background: var(--roady-surface-background);
  border: 1px solid var(--roady-border-default);
}

.analysis-title {
  margin: 0;
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-secondary);
}

/* ── 액션 ── */
.detail-actions {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  padding: 1.4rem 1.6rem;
  border-top: 1px solid var(--roady-border-default);
}

.action-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.8rem;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
}

.action-btn--danger {
  color: var(--roady-status-danger);
  border-color: var(--roady-status-danger);
}

.action-btn--danger:hover:not(:disabled) {
  background: color-mix(in srgb, var(--roady-status-danger) 8%, transparent);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
