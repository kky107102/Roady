<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { damagesApi } from '@/api/damages'
import { robotsApi } from '@/api/robots'
import type { DamageDetail, DamageImage, DamageAnalysis, DamageStatus } from '@/types/damage'
import type { BadgeType } from '@/components/common/StatusBadge.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorState from '@/components/common/ErrorState.vue'

const props = withDefaults(
  defineProps<{
    damageId: number | null
    verdictSubmitting?: boolean
  }>(),
  {
    verdictSubmitting: false,
  },
)
const emit = defineEmits<{
  close: []
  'verdict-no-repair': []
  'verdict-repair': [processingPriority: string | null]
}>()

// ── 상태 ──────────────────────────────────────────────────

const detail = ref<DamageDetail | null>(null)
const analyses = ref<DamageAnalysis[]>([])
const analysisError = ref<string | null>(null)
const analysisLoading = ref(false)
const imageBlobUrls = ref<Map<number, string>>(new Map())
const imagesLoading = ref(false)
const robotName = ref<string | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// 경쟁 조건 방지: 가장 최근 요청의 순번만 결과를 반영함
let fetchSeq = 0

const latestAnalysis = computed<DamageAnalysis | null>(
  () =>
    analyses.value.find(
      (a) => a.analysisStatus === 'SUCCESS' || a.analysisStatus === 'CONFIRMED',
    ) ??
    analyses.value[0] ??
    null,
)

// ── 이미지 로드 (fire-and-forget) ─────────────────────────

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

async function loadRobotName(robotId: number, seq: number) {
  try {
    const robot = await robotsApi.get(robotId)
    if (seq === fetchSeq) robotName.value = robot.name
  } catch {
    // 이름 조회 실패 시 화면에서는 로봇 ID를 대체값으로 사용한다.
  }
}

// ── 데이터 조회 ────────────────────────────────────────────

async function fetchDetail(id: number) {
  const seq = ++fetchSeq
  loading.value = true
  error.value = null
  detail.value = null
  analyses.value = []
  analysisError.value = null
  analysisLoading.value = false
  imagesLoading.value = false
  robotName.value = null
  for (const url of imageBlobUrls.value.values()) URL.revokeObjectURL(url)
  imageBlobUrls.value = new Map()

  try {
    const [detailResult, analysisResult] = await Promise.allSettled([
      damagesApi.getDetail(id),
      damagesApi.getAnalysisJobs(id),
    ])

    if (seq !== fetchSeq) return

    if (detailResult.status === 'rejected') {
      error.value = '사건 정보를 불러오지 못했습니다.'
      return
    }

    detail.value = detailResult.value

    if (detailResult.value.robotId != null) {
      loadRobotName(detailResult.value.robotId, seq)
    }

    if (analysisResult.status === 'fulfilled') {
      analyses.value = analysisResult.value
    } else {
      analysisError.value = 'AI 분석 결과를 불러오지 못했습니다.'
    }

    if (detailResult.value.images.length > 0) {
      loadImages(detailResult.value, seq)
    }
  } finally {
    if (seq === fetchSeq) loading.value = false
  }
}

// ── 분석 결과 재시도 ───────────────────────────────────────

async function retryAnalysis() {
  if (props.damageId == null) return
  const id = props.damageId
  const seq = fetchSeq

  analysisError.value = null
  analysisLoading.value = true
  try {
    const a = await damagesApi.getAnalysisJobs(id)
    if (seq !== fetchSeq) return
    analyses.value = a
  } catch {
    if (seq !== fetchSeq) return
    analysisError.value = 'AI 분석 결과를 불러오지 못했습니다.'
  } finally {
    if (seq === fetchSeq) analysisLoading.value = false
  }
}

watch(
  () => props.damageId,
  (id) => {
    if (id != null) fetchDetail(id)
  },
  { immediate: true },
)

// ── 키보드 접근성 ─────────────────────────────────────────

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
  MISSING: '유실',
  WEAR: '마모',
  BREAKAGE: '파손',
  CRACK: '균열',
}

const STATUS_LABELS: Record<DamageStatus, string> = {
  COLLECTED: '수집완료',
  AI_ANALYZING: 'AI 분석중',
  AI_ANALYZED: 'AI 분석완료',
  REQUESTED: '요청 전',
  REPAIR_IN_PROGRESS: '요청 완료',
  CANCELED: '취소',
  REVIEW_REQUIRED: '검토 필요',
  RECEIVED: '접수됨',
  REPAIR_SCHEDULED: '보수 예정',
  REPAIRING: '보수 중',
  REPAIR_COMPLETED: '보수 완료',
  REPAIR_NOT_REQUIRED: '보수 불필요',
}

const STATUS_BADGE_TYPES: Record<DamageStatus, BadgeType> = {
  COLLECTED: 'neutral',
  AI_ANALYZING: 'info',
  AI_ANALYZED: 'warning',
  REQUESTED: 'info',
  REPAIR_IN_PROGRESS: 'warning',
  CANCELED: 'neutral',
  REVIEW_REQUIRED: 'warning',
  RECEIVED: 'info',
  REPAIR_SCHEDULED: 'info',
  REPAIRING: 'warning',
  REPAIR_COMPLETED: 'success',
  REPAIR_NOT_REQUIRED: 'neutral',
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

function formatDamageScore(score: number | null): string {
  return score != null ? `${score}%` : '-'
}

function formatConfidenceScore(score: number | null): string {
  return score != null ? `${Math.round(score * 100)}%` : '-'
}

function getPriorityLabel(priority: string | null | undefined): string {
  if (!priority) return '보류'
  return PRIORITY_LABELS[priority] ?? priority
}

function getDamageTypeLabel(type: string | null | undefined): string {
  if (!type) return '-'
  return DAMAGE_TYPE_LABELS[type] ?? type
}

function clampScore(score: number | null): number {
  if (score == null) return 0
  return Math.min(100, Math.max(0, score))
}

const robotDisplayName = computed(() => {
  if (robotName.value) return robotName.value
  if (detail.value?.robotId != null) return `#${detail.value.robotId}`
  return '-'
})

const displayedPriority = computed(
  () => detail.value?.processingPriority || latestAnalysis.value?.repairPriority || null,
)

const canSubmitVerdict = computed(
  () =>
    detail.value?.currentStatus === 'AI_ANALYZED' ||
    detail.value?.currentStatus === 'REVIEW_REQUIRED',
)
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
      <!-- ── 고정 헤더 ── -->
      <div class="detail-head">
        <h2 class="detail-head-title">사건 상세 정보</h2>
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
          <!-- 사건번호(outline 배지) + 긴급도(filled 배지) -->
          <div class="case-badges">
            <span class="badge-case-id">{{ formatCaseId(detail.id, detail.createdAt) }}</span>
            <span
              class="badge-priority"
              :class="
                displayedPriority
                  ? `badge-priority--${displayedPriority.toLowerCase()}`
                  : 'badge-priority--pending'
              "
            >
              {{
                displayedPriority
                  ? getPriorityLabel(displayedPriority)
                  : '보류'
              }}
            </span>
          </div>

          <!-- 사건명 (큰 제목) -->
          <h3 class="case-title">{{ detail.description ?? '설명 없음' }}</h3>

          <!-- 위치 & 탐지 일시 -->
          <div class="case-meta">
            <span class="case-meta-item">
              <!-- 위치 핀 -->
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
              <!-- 시계 -->
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

        <!-- 2. 탐지 이미지 -->
        <div class="images-section">
          <div class="images-header">
            <h3 class="images-title">탐지 이미지</h3>
            <span class="robot-label"> 탐지 로봇: {{ robotDisplayName }} </span>
          </div>

          <template v-if="detail.imageCount > 0">
            <div v-if="imagesLoading" class="image-loading">
              <LoadingSpinner label="이미지 불러오는 중" />
            </div>
            <div
              v-else-if="imageBlobUrls.size > 0"
              :class="['image-grid', { 'image-grid--single': imageBlobUrls.size === 1 }]"
            >
              <img
                v-for="img in detail.images"
                :key="img.id"
                :src="imageBlobUrls.get(img.id)"
                :alt="`파손 이미지 ${img.sortOrder}`"
                class="detail-img"
                v-show="imageBlobUrls.has(img.id)"
              />
            </div>
            <div v-else class="no-image-notice">이미지를 불러올 수 없습니다.</div>
          </template>
          <div v-else class="no-image-notice">이미지 없음</div>
        </div>

        <!-- 3. AI 판독 요약 (통합 카드) -->
        <div class="ai-card">
          <!-- AI 카드 헤더 -->
          <div class="ai-card-head">
            <span class="ai-card-heading">
              <!-- 별 아이콘 -->
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="currentColor"
                stroke="none"
                aria-hidden="true"
              >
                <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z" />
              </svg>
              AI 판독 요약
            </span>
            <span class="ai-confidence">
              <!-- 방패 아이콘 -->
              <svg
                width="13"
                height="13"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                aria-hidden="true"
              >
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              신뢰도 {{ formatConfidenceScore(latestAnalysis?.confidenceScore ?? null) }}
            </span>
          </div>

          <!-- AI 카드 상태별 본문 -->

          <!-- 분석 API 오류 -->
          <template v-if="analysisError">
            <div class="ai-card-state">
              <p class="analysis-error-msg">{{ analysisError }}</p>
              <button
                type="button"
                data-testid="analysis-retry-btn"
                class="krds-btn small outline analysis-retry-btn"
                @click="retryAnalysis"
              >
                다시 시도
              </button>
            </div>
          </template>

          <!-- 분석 재시도 로딩 -->
          <div v-else-if="analysisLoading" class="ai-card-state analysis-loading">
            <LoadingSpinner label="AI 분석 결과 조회 중" />
          </div>

          <!-- 분석 요약 (결과가 없을 때도 보류 상태로 동일한 구조 유지) -->
          <div v-else class="ai-card-body">
            <!-- 우선순위 -->
            <div class="ai-item">
              <div class="ai-icon-wrap ai-icon-wrap--priority" aria-hidden="true">
                <!-- 경고 삼각형 -->
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <path
                    d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
                  />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
              </div>
              <span class="ai-label">우선순위</span>
              <span
                class="ai-value"
                :class="{
                  'ai-value--urgent': latestAnalysis?.repairPriority === 'URGENT',
                  'ai-value--high': latestAnalysis?.repairPriority === 'HIGH',
                }"
              >
                {{ getPriorityLabel(latestAnalysis?.repairPriority) }}
              </span>
            </div>

            <div class="ai-divider" aria-hidden="true"></div>

            <!-- 파손 유형 -->
            <div class="ai-item">
              <div class="ai-icon-wrap ai-icon-wrap--type" aria-hidden="true">
                <!-- 태그 아이콘 -->
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <path
                    d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"
                  />
                  <line x1="7" y1="7" x2="7.01" y2="7" />
                </svg>
              </div>
              <span class="ai-label">파손 유형</span>
              <span class="ai-value">{{ getDamageTypeLabel(latestAnalysis?.damageType) }}</span>
            </div>

            <div class="ai-divider" aria-hidden="true"></div>

            <!-- 파손률 -->
            <div class="ai-item">
              <div class="ai-icon-wrap ai-icon-wrap--score" aria-hidden="true">
                <!-- 막대그래프 아이콘 -->
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                </svg>
              </div>
              <span class="ai-label">파손률</span>
              <span class="ai-value">{{
                formatDamageScore(latestAnalysis?.damageScore ?? null)
              }}</span>
              <div
                v-if="latestAnalysis?.damageScore != null"
                class="score-bar"
                aria-label="파손률 진행 막대"
                role="img"
              >
                <div
                  class="score-bar-fill"
                  :style="{ width: `${clampScore(latestAnalysis.damageScore)}%` }"
                ></div>
              </div>
              <span class="score-desc">탐지 영역 내 파손 비율</span>
            </div>
          </div>
        </div>
      </div>
      <!-- /detail-body -->

      <!-- ── 고정 하단 판정 버튼 ── -->
      <div v-if="canSubmitVerdict" class="detail-actions">
        <button
          type="button"
          class="verdict-btn verdict-btn--secondary"
          :disabled="verdictSubmitting"
          @click="emit('verdict-no-repair')"
        >
          {{ verdictSubmitting ? '처리 중' : '보수 불필요' }}
        </button>
        <button
          type="button"
          class="verdict-btn verdict-btn--primary"
          :disabled="verdictSubmitting"
          @click="emit('verdict-repair', displayedPriority)"
        >
          <!-- 렌치 아이콘 -->
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <path
              d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"
            />
          </svg>
          {{ verdictSubmitting ? '처리 중' : '보수 필요' }}
        </button>
      </div>
    </template>
  </aside>
</template>

<style scoped>
/* ── 패널 기본 ── */
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

/* ── 사건 핵심 정보 (표 없음) ── */
.case-hero {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 사건번호 + 긴급도 배지 행 */
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

.badge-priority {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: var(--krds-font-weight-bold);
  white-space: nowrap;
  letter-spacing: 0.01em;
}

.badge-priority--urgent {
  background: var(--roady-status-danger);
  color: #fff;
}

.badge-priority--high {
  background: var(--roady-status-warning);
  color: #fff;
}

.badge-priority--normal,
.badge-priority--medium {
  background: var(--roady-status-info);
  color: #fff;
}

.badge-priority--low {
  background: var(--roady-text-tertiary);
  color: #fff;
}

.badge-priority--pending {
  background: #f1f3f5;
  color: var(--roady-text-secondary);
}

/* 사건명 — 패널에서 가장 크고 굵은 텍스트 */
.case-title {
  margin: 0;
  font-size: 28px;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
  line-height: 1.3;
  word-break: break-word;
  letter-spacing: -0.01em;
}

/* 위치 & 탐지 일시 */
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

/* ── 탐지 이미지 섹션 ── */
.images-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.images-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.images-title {
  margin: 0;
  font-size: 16px;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
}

.robot-label {
  font-size: 12px;
  color: var(--roady-text-tertiary);
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.image-grid--single {
  grid-template-columns: 1fr;
}

.detail-img {
  width: 100%;
  min-width: 0;
  border-radius: 8px;
  object-fit: cover;
  aspect-ratio: 1 / 1;
  background: var(--roady-surface-subtle);
  display: block;
}

.image-grid--single .detail-img {
  aspect-ratio: 16 / 9;
  max-height: 280px;
}

.image-loading {
  display: flex;
  justify-content: center;
  padding: 32px;
}

.no-image-notice {
  font-size: 14px;
  color: var(--roady-text-tertiary);
  text-align: center;
  padding: 24px;
  border: 1px dashed var(--roady-border-default);
  border-radius: 8px;
  background: var(--roady-surface-background);
}

/* ── AI 판독 요약 — 통합 카드 ── */
.ai-card {
  border: 1px solid var(--roady-border-default);
  border-radius: 8px;
  background: #fbfcfe;
  overflow: hidden;
}

/* 카드 헤더 */
.ai-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: transparent;
  border-bottom: 0;
}

.ai-card-heading {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
}

.ai-card-heading svg {
  color: var(--roady-brand-accent-dark);
}

.ai-confidence {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--roady-text-secondary);
  font-weight: var(--krds-font-weight-bold);
}

.ai-confidence svg {
  color: var(--roady-status-success);
}

/* 카드 상태 (오류/로딩/빈 결과) */
.ai-card-state {
  min-height: 72px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.analysis-loading {
  justify-content: center;
}

.analysis-empty {
  margin: 0;
  font-size: 13px;
  color: var(--roady-text-tertiary);
  text-align: center;
}

.analysis-error-msg {
  margin: 0;
  font-size: 13px;
  color: var(--roady-status-danger);
}

.analysis-retry-btn {
  align-self: flex-start;
}

/* 카드 본문 — 3-column 가로 레이아웃 */
.ai-card-body {
  display: flex;
  align-items: stretch;
  padding: 10px 4px 12px;
}

.ai-item {
  flex: 1;
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  grid-auto-rows: min-content;
  align-content: center;
  align-items: center;
  column-gap: 9px;
  row-gap: 2px;
  padding: 4px 12px;
  text-align: left;
  min-width: 0;
}

.ai-divider {
  width: 1px;
  background: var(--roady-border-default);
  flex-shrink: 0;
  align-self: stretch;
  margin: 6px 0;
}

/* 아이콘 원형 배경 */
.ai-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  grid-column: 1;
  grid-row: 1 / span 4;
}

.ai-icon-wrap--priority {
  background: rgba(211, 47, 47, 0.1);
  color: var(--roady-status-danger);
}

.ai-icon-wrap--type {
  background: rgba(47, 107, 154, 0.12);
  color: var(--roady-brand-secondary);
}

.ai-icon-wrap--score {
  background: rgba(185, 130, 0, 0.12);
  color: var(--roady-brand-accent-dark);
}

.ai-label {
  grid-column: 2;
  font-size: 10px;
  color: var(--roady-text-tertiary);
  font-weight: var(--krds-font-weight-bold);
  letter-spacing: 0.03em;
  text-transform: uppercase;
  line-height: 1;
}

.ai-value {
  grid-column: 2;
  font-size: 15px;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
  line-height: 1.2;
}

/* 우선순위 강조 배지 */
.ai-value--urgent {
  display: inline-flex;
  align-items: center;
  padding: 2px 9px;
  background: var(--roady-status-danger);
  color: #fff;
  border-radius: 999px;
  font-size: 12px;
}

.ai-value--high {
  color: var(--roady-status-warning);
}

/* 파손률 진행 막대 */
.score-bar {
  grid-column: 2;
  width: 100%;
  height: 4px;
  background: var(--roady-surface-subtle);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 2px;
}

.score-bar-fill {
  height: 100%;
  background: var(--roady-status-danger);
  border-radius: 2px;
  transition: width 0.4s ease;
}

.score-desc {
  grid-column: 2;
  font-size: 9px;
  color: var(--roady-text-tertiary);
  line-height: 1.3;
  text-align: left;
  word-break: keep-all;
}

/* ── 고정 하단 판정 버튼 ── */
.detail-actions {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--roady-border-default);
  background: var(--roady-surface-default);
}

.verdict-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 52px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: var(--krds-font-weight-bold);
  cursor: pointer;
  transition:
    background-color 0.15s,
    border-color 0.15s;
  letter-spacing: 0.01em;
}

.verdict-btn:disabled {
  cursor: wait;
  opacity: 0.6;
}

.verdict-btn--secondary {
  background: var(--roady-surface-default);
  border: 1.5px solid var(--roady-border-default);
  color: var(--roady-text-primary);
}

.verdict-btn--secondary:hover {
  background: var(--roady-surface-subtle);
  border-color: var(--roady-text-secondary);
}

.verdict-btn--primary {
  background: var(--roady-brand-primary);
  border: 1.5px solid var(--roady-brand-primary);
  color: #fff;
}

.verdict-btn--primary:hover {
  background: var(--roady-brand-primary-hover);
  border-color: var(--roady-brand-primary-hover);
}

/* ── 반응형 ── */
@media (max-width: 600px) {
  .detail-body {
    padding: 20px;
  }

  .detail-head {
    min-height: 64px;
    padding: 0 20px;
  }

  .image-grid {
    grid-template-columns: 1fr;
  }

  .ai-card-body {
    flex-direction: column;
    padding: 12px;
    gap: 12px;
  }

  .ai-divider {
    width: 100%;
    height: 1px;
    margin: 0;
  }

  .ai-item {
    display: grid;
    text-align: left;
    padding: 0;
    column-gap: 12px;
    row-gap: 2px;
  }

  .ai-item .ai-icon-wrap {
    flex-shrink: 0;
  }

  .ai-item .score-bar {
    width: 96px;
  }

  .detail-actions {
    padding: 14px 20px;
    gap: 10px;
  }

  .verdict-btn {
    height: 48px;
    font-size: 15px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .score-bar-fill {
    transition: none;
  }
}
</style>
