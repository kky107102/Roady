<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { damagesApi } from '@/api/damages'
import { robotsApi } from '@/api/robots'
import type {
  DamageDetail,
  DamageImage,
  DamageAnalysis,
  DamageStatus,
  DamageListItem,
} from '@/types/damage'
import type { BadgeType } from '@/components/common/StatusBadge.vue'
import AiResultBadge from '@/components/common/AiResultBadge.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import {
  formatDamageTypeLabel,
  formatPriorityLabel,
  priorityBadgeType,
} from '@/utils/repairRequest'

const props = withDefaults(
  defineProps<{
    damageId: number | null
    verdictSubmitting?: boolean
    summary?: DamageListItem | null
    refreshKey?: number
    backTo?: string
  }>(),
  {
    verdictSubmitting: false,
    summary: null,
    refreshKey: 0,
    backTo: '/damages',
  },
)
const emit = defineEmits<{
  close: []
  'verdict-no-repair': []
  'verdict-repair': [payload: ReviewDecisionPayload]
  'verdict-reset': []
}>()

export interface ReviewDecisionPayload {
  processingPriority: string
  reviewDamageType: string
  reviewNote: string | null
}

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
const reviewModalOpen = ref(false)
const noRepairModalOpen = ref(false)
const resetVerdictModalOpen = ref(false)
const reviewPriority = ref('')
const reviewDamageType = ref('')
const reviewNote = ref('')
const reviewFormError = ref('')

// 경쟁 조건 방지: 가장 최근 요청의 순번만 결과를 반영함
let fetchSeq = 0

const summaryAnalysis = computed<DamageAnalysis | null>(() => {
  const summary = props.summary
  if (!summary || summary.id !== props.damageId) return null
  if (['COLLECTED', 'AI_ANALYZING'].includes(summary.currentStatus)) return null

  return {
    id: 0,
    damageId: summary.id,
    damaged: summary.repairRequired,
    damageScore: summary.damageScore,
    damageType: summary.damageType ?? null,
    repairRequired: summary.repairRequired,
    repairPriority: summary.repairPriority,
    confidenceScore: summary.confidenceScore,
    analysisStatus: 'SUCCESS',
    analyzedAt: null,
    createdAt: summary.createdAt,
  }
})

const latestAnalysis = computed<DamageAnalysis | null>(() => {
  const successful = analyses.value.find(
    (analysis) => analysis.analysisStatus === 'SUCCESS' || analysis.analysisStatus === 'CONFIRMED',
  )
  return successful ?? summaryAnalysis.value ?? analyses.value[0] ?? null
})

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
  () => [props.damageId, props.refreshKey] as const,
  ([id]) => {
    if (id != null) fetchDetail(id)
  },
  { immediate: true },
)

// ── 키보드 접근성 ─────────────────────────────────────────

function handleKeydown(e: KeyboardEvent) {
  if (e.key !== 'Escape') return
  if (noRepairModalOpen.value) {
    noRepairModalOpen.value = false
    return
  }
  if (resetVerdictModalOpen.value) {
    resetVerdictModalOpen.value = false
    return
  }
  if (reviewModalOpen.value) {
    reviewModalOpen.value = false
    return
  }
  emit('close')
}

onMounted(() => document.addEventListener('keydown', handleKeydown))
onUnmounted(() => {
  ++fetchSeq
  document.removeEventListener('keydown', handleKeydown)
  for (const url of imageBlobUrls.value.values()) URL.revokeObjectURL(url)
})

// ── 표시 헬퍼 ─────────────────────────────────────────────

const REVIEW_PRIORITY_OPTIONS = [
  { value: 'URGENT', label: '긴급' },
  { value: 'HIGH', label: '높음' },
  { value: 'NORMAL', label: '보통' },
  { value: 'LOW', label: '낮음' },
]

const REVIEW_DAMAGE_TYPE_OPTIONS = [
  { value: 'LARGE_MISSING', label: '큰 결손' },
  { value: 'SMALL_MISSING', label: '작은 결손' },
  { value: 'WEAR', label: '마모' },
  { value: 'CRACK', label: '균열' },
  { value: 'OTHER', label: '기타' },
]

const STATUS_LABELS: Record<DamageStatus, string> = {
  COLLECTED: '수집완료',
  AI_ANALYZING: 'AI 분석중',
  AI_ANALYZED: 'AI 분석완료',
  REQUESTED: '요청 전',
  REPAIR_IN_PROGRESS: '보수 중',
  CANCELED: '취소',
  REPAIR_COMPLETED: '보수 완료',
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
  return formatPriorityLabel(priority, '보류')
}

function getDamageTypeLabel(type: string | null | undefined): string {
  return formatDamageTypeLabel(type)
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

const detailConfirmed = computed(() => {
  const status = detail.value?.currentStatus
  return status != null && status !== 'AI_ANALYZED'
})

const displayedPriority = computed(() =>
  detailConfirmed.value
    ? (detail.value?.processingPriority ?? props.summary?.processingPriority ?? null)
    : (latestAnalysis.value?.repairPriority ?? null),
)

const managerReviewDamageType = computed(
  () => detail.value?.reviewDamageType ?? props.summary?.reviewDamageType ?? null,
)
const managerReviewNote = computed(
  () => detail.value?.reviewNote ?? props.summary?.reviewNote ?? null,
)

const displayedPriorityLabel = computed(() => {
  if (!displayedPriority.value) {
    if (detailConfirmed.value) return '미지정'
    return latestAnalysis.value ? '보류' : '-'
  }
  return getPriorityLabel(displayedPriority.value)
})

const displayedPriorityType = computed<BadgeType>(() => priorityBadgeType(displayedPriority.value))

const analysisPriorityLabel = computed(() =>
  latestAnalysis.value ? getPriorityLabel(latestAnalysis.value.repairPriority) : '-',
)

const analysisPriorityType = computed<BadgeType>(() => {
  const priority = latestAnalysis.value?.repairPriority
  return priorityBadgeType(priority)
})

const analysisDamageTypeLabel = computed(() => getDamageTypeLabel(latestAnalysis.value?.damageType))

const analysisDamageTypeType = computed<BadgeType>(() => 'neutral')

const canSubmitVerdict = computed(() => detail.value?.currentStatus === 'AI_ANALYZED')

const canResetVerdict = computed(() =>
  ['REQUESTED', 'CANCELED'].includes(detail.value?.currentStatus ?? ''),
)

const canManagePendingRequest = computed(() => detail.value?.currentStatus === 'REQUESTED')

const hasManagerReview = computed(
  () =>
    detailConfirmed.value &&
    Boolean(
      detail.value?.processingPriority ||
      props.summary?.processingPriority ||
      managerReviewDamageType.value ||
      managerReviewNote.value,
    ),
)

function confirmNoRepair() {
  noRepairModalOpen.value = true
}

function submitNoRepair() {
  noRepairModalOpen.value = false
  emit('verdict-no-repair')
}

function openReviewModal() {
  const suggestedPriority =
    detail.value?.processingPriority ??
    props.summary?.processingPriority ??
    latestAnalysis.value?.repairPriority
  const suggestedDamageType = managerReviewDamageType.value ?? latestAnalysis.value?.damageType
  reviewPriority.value = REVIEW_PRIORITY_OPTIONS.some(
    (option) => option.value === suggestedPriority,
  )
    ? (suggestedPriority ?? '')
    : ''
  reviewDamageType.value = REVIEW_DAMAGE_TYPE_OPTIONS.some(
    (option) => option.value === suggestedDamageType,
  )
    ? (suggestedDamageType ?? '')
    : ''
  reviewNote.value = managerReviewNote.value ?? ''
  reviewFormError.value = ''
  reviewModalOpen.value = true
}

function submitReviewDecision() {
  if (!reviewPriority.value || !reviewDamageType.value) {
    reviewFormError.value = '우선순위와 파손 유형을 모두 선택해 주세요.'
    return
  }
  emit('verdict-repair', {
    processingPriority: reviewPriority.value,
    reviewDamageType: reviewDamageType.value,
    reviewNote: reviewNote.value.trim() || null,
  })
  reviewModalOpen.value = false
}

function confirmResetVerdict() {
  resetVerdictModalOpen.value = true
}

function submitResetVerdict() {
  resetVerdictModalOpen.value = false
  emit('verdict-reset')
}

const reviewActionMode = computed<'ready' | 'waiting' | 'completed'>(() => {
  const status = detail.value?.currentStatus
  if (status === 'AI_ANALYZED') return 'ready'
  if (status === 'COLLECTED' || status === 'AI_ANALYZING') return 'waiting'
  return 'completed'
})

const reviewActionMessage = computed(() => {
  const status = detail.value?.currentStatus
  if (status === 'COLLECTED') return 'AI 분석 대기 중입니다. 분석 완료 후 판정할 수 있습니다.'
  if (status === 'AI_ANALYZING') return 'AI 분석 중입니다. 분석 완료 후 판정할 수 있습니다.'
  if (status && reviewActionMode.value === 'completed') {
    return `${STATUS_LABELS[status]} · 관리자 확인 완료`
  }
  return 'AI 판독 결과를 확인하고 보수 필요 여부를 판정해 주세요.'
})

const loadedImages = computed(() =>
  (detail.value?.images ?? []).filter((image) => imageBlobUrls.value.has(image.id)),
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
            <AiResultBadge
              v-if="!detailConfirmed"
              :type="displayedPriorityType"
              :label="displayedPriorityLabel"
            />
            <StatusBadge v-else :type="displayedPriorityType" :label="displayedPriorityLabel" />
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

        <!-- 3. 관리자 판정 -->
        <section v-if="hasManagerReview" class="manager-review-card" aria-label="관리자 판정">
          <h3 class="manager-review-title">관리자 판정</h3>
          <div class="manager-review-grid">
            <div class="manager-review-item">
              <span class="manager-review-label">우선순위</span>
              <StatusBadge :type="displayedPriorityType" :label="displayedPriorityLabel" />
            </div>
            <div class="manager-review-item">
              <span class="manager-review-label">파손 유형</span>
              <StatusBadge type="neutral" :label="getDamageTypeLabel(managerReviewDamageType)" />
            </div>
            <div v-if="managerReviewNote" class="manager-review-item manager-review-note">
              <span class="manager-review-label">비고</span>
              <p>{{ managerReviewNote }}</p>
            </div>
          </div>
        </section>

        <!-- 4. AI 판독 요약 (통합 카드) -->
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
          <div v-if="analysisError && !latestAnalysis" class="ai-card-state ai-card-state--error">
            <p class="analysis-error-msg">{{ analysisError }}</p>
            <button
              type="button"
              data-testid="analysis-retry-btn"
              class="krds-btn small secondary analysis-retry-btn"
              @click="retryAnalysis"
            >
              다시 시도
            </button>
          </div>

          <!-- 분석 재시도 로딩 -->
          <div v-if="analysisLoading && !latestAnalysis" class="ai-card-state analysis-loading">
            <LoadingSpinner label="AI 분석 결과 조회 중" />
          </div>

          <!-- 분석 요약 (결과가 없어도 항목 구조와 자리표시자를 유지) -->
          <div v-else class="ai-card-body">
            <!-- 우선순위 -->
            <div class="ai-item">
              <span class="ai-label">우선순위</span>
              <AiResultBadge
                class="ai-result-badge"
                :type="analysisPriorityType"
                :label="analysisPriorityLabel"
                size="medium"
              />
            </div>

            <div class="ai-divider" aria-hidden="true"></div>

            <!-- 파손 유형 -->
            <div class="ai-item">
              <span class="ai-label">파손 유형</span>
              <AiResultBadge
                class="ai-result-badge"
                :type="analysisDamageTypeType"
                :label="analysisDamageTypeLabel"
                size="medium"
              />
            </div>

            <div class="ai-divider" aria-hidden="true"></div>

            <!-- 파손율 -->
            <div class="ai-item">
              <span class="ai-label">파손율</span>
              <div class="score-value-row">
                <span class="ai-value">{{
                  formatDamageScore(latestAnalysis?.damageScore ?? null)
                }}</span>
                <div
                  v-if="latestAnalysis?.damageScore != null"
                  class="score-bar"
                  :aria-label="`파손율 ${formatDamageScore(latestAnalysis.damageScore)}`"
                  role="img"
                >
                  <div
                    class="score-bar-fill"
                    :style="{ width: `${clampScore(latestAnalysis.damageScore)}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- /detail-body -->

      <!-- ── 고정 하단 판정 영역 ── -->
      <div class="detail-actions" :data-action-mode="reviewActionMode">
        <p class="action-guidance" role="status">{{ reviewActionMessage }}</p>

        <template v-if="canSubmitVerdict">
          <button
            type="button"
            class="verdict-btn verdict-btn--secondary"
            :disabled="verdictSubmitting"
            @click="confirmNoRepair"
          >
            {{ verdictSubmitting ? '처리 중' : '보수 불필요' }}
          </button>
          <button
            type="button"
            class="verdict-btn verdict-btn--primary"
            :disabled="verdictSubmitting"
            @click="openReviewModal"
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
        </template>

        <template v-else-if="reviewActionMode === 'waiting'">
          <button type="button" class="verdict-btn verdict-btn--secondary" disabled>
            보수 불필요
          </button>
          <button type="button" class="verdict-btn verdict-btn--primary" disabled>보수 필요</button>
        </template>

        <div v-else-if="canManagePendingRequest" class="pending-request-controls">
          <button type="button" class="verdict-btn verdict-btn--secondary" @click="openReviewModal">
            판정 수정하기
          </button>
          <button
            type="button"
            class="verdict-btn verdict-btn--secondary verdict-reset-btn"
            @click="confirmResetVerdict"
          >
            판정 되돌리기
          </button>
          <RouterLink
            class="request-create-btn"
            :to="{
              name: 'repair-detail',
              params: { damageId: detail.id },
              query: { action: 'create-request', backTo },
            }"
          >
            요청서 작성 바로가기
          </RouterLink>
        </div>

        <div v-else class="review-completed-controls">
          <div class="review-completed-state">
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
              <path d="M20 6 9 17l-5-5" />
            </svg>
            확인 완료
          </div>
          <button
            v-if="canResetVerdict"
            type="button"
            class="verdict-reset-btn"
            :disabled="verdictSubmitting"
            @click="confirmResetVerdict"
          >
            판정 되돌리기
          </button>
        </div>
      </div>
    </template>
  </aside>

  <Teleport to="body">
    <div
      v-if="noRepairModalOpen"
      class="review-modal-backdrop"
      @click.self="noRepairModalOpen = false"
    >
      <section
        class="review-modal review-modal--confirm"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="no-repair-title"
        aria-describedby="no-repair-description"
      >
        <div class="confirm-modal-icon" aria-hidden="true">!</div>
        <div class="confirm-modal-content">
          <h2 id="no-repair-title">보수 불필요로 판정할까요?</h2>
          <p id="no-repair-description">
            판정 후 사건은 확인 목록으로 이동합니다. 필요한 경우 확인 목록에서 판정을 수정할 수
            있습니다.
          </p>
        </div>
        <div class="review-modal-actions confirm-modal-actions">
          <button
            type="button"
            class="krds-btn medium secondary"
            @click="noRepairModalOpen = false"
          >
            취소
          </button>
          <button
            type="button"
            class="krds-btn medium filled primary"
            :disabled="verdictSubmitting"
            @click="submitNoRepair"
          >
            {{ verdictSubmitting ? '처리 중' : '보수 불필요로 판정' }}
          </button>
        </div>
      </section>
    </div>

    <div
      v-if="resetVerdictModalOpen"
      class="review-modal-backdrop"
      @click.self="resetVerdictModalOpen = false"
    >
      <section
        class="review-modal review-modal--confirm"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="reset-verdict-title"
        aria-describedby="reset-verdict-description"
      >
        <div class="confirm-modal-icon" aria-hidden="true">!</div>
        <div class="confirm-modal-content">
          <h2 id="reset-verdict-title">판정을 되돌릴까요?</h2>
          <p id="reset-verdict-description">
            저장된 관리자 판정이 취소되고 사건은 미확인 목록으로 이동합니다.
          </p>
        </div>
        <div class="review-modal-actions confirm-modal-actions">
          <button
            type="button"
            class="krds-btn medium secondary"
            @click="resetVerdictModalOpen = false"
          >
            취소
          </button>
          <button
            type="button"
            class="krds-btn medium filled primary"
            :disabled="verdictSubmitting"
            @click="submitResetVerdict"
          >
            {{ verdictSubmitting ? '처리 중' : '판정 되돌리기' }}
          </button>
        </div>
      </section>
    </div>

    <div v-if="reviewModalOpen" class="review-modal-backdrop" @click.self="reviewModalOpen = false">
      <form
        class="review-modal"
        role="dialog"
        aria-modal="true"
        @submit.prevent="submitReviewDecision"
      >
        <div class="review-modal-head">
          <div>
            <p class="review-modal-eyebrow">관리자 판정</p>
            <h2>보수 필요 판정</h2>
          </div>
          <button
            type="button"
            class="review-modal-close"
            aria-label="판정 모달 닫기"
            @click="reviewModalOpen = false"
          >
            ×
          </button>
        </div>

        <p class="review-modal-description">AI 판독값을 참고해 최종 판정 내용을 입력해 주세요.</p>

        <label class="review-field">
          <span>우선순위 <strong aria-hidden="true">*</strong></span>
          <select v-model="reviewPriority" class="krds-input" required>
            <option value="" disabled>우선순위 선택</option>
            <option
              v-for="option in REVIEW_PRIORITY_OPTIONS"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </label>

        <label class="review-field">
          <span>파손 유형 <strong aria-hidden="true">*</strong></span>
          <select v-model="reviewDamageType" class="krds-input" required>
            <option value="" disabled>파손 유형 선택</option>
            <option
              v-for="option in REVIEW_DAMAGE_TYPE_OPTIONS"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </label>

        <label class="review-field">
          <span>비고 <small>(선택사항)</small></span>
          <textarea
            v-model="reviewNote"
            class="krds-input review-note-input"
            maxlength="1000"
            rows="4"
            placeholder="판정 근거나 요청 시 참고할 내용을 입력해 주세요."
          ></textarea>
          <span class="review-note-count">{{ reviewNote.length }}/1000</span>
        </label>

        <p v-if="reviewFormError" class="review-form-error" role="alert">{{ reviewFormError }}</p>

        <div class="review-modal-actions">
          <button type="button" class="krds-btn medium secondary" @click="reviewModalOpen = false">
            취소
          </button>
          <button
            type="submit"
            class="krds-btn medium filled primary"
            :disabled="verdictSubmitting"
          >
            {{ verdictSubmitting ? '저장 중' : '판정 저장' }}
          </button>
        </div>
      </form>
    </div>
  </Teleport>
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

/* 내용이 패널보다 길면 각 영역을 찌그러뜨리지 않고 본문을 스크롤한다. */
.detail-body > .case-hero,
.detail-body > .images-section,
.detail-body > .ai-card {
  flex-shrink: 0;
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
  position: relative;
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

/* ── AI 판독 요약 — 통합 카드 ── */
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
  padding: 8px 12px;
  background: transparent;
  border-bottom: 0;
}

.ai-card-heading {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--krds-pc-font-size-label-small);
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
  font-size: var(--krds-pc-font-size-label-xsmall);
  color: var(--roady-text-secondary);
  font-weight: var(--krds-font-weight-bold);
}

.ai-confidence svg {
  color: var(--roady-status-success);
}

/* 카드 상태 (오류/로딩/빈 결과) */
.ai-card-state {
  min-height: 116px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.analysis-loading {
  justify-content: center;
}

.ai-card-state--error {
  min-height: 0;
  padding: 10px 16px 0;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
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
  min-height: 0;
  padding: 8px 4px 10px;
}

.ai-item {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  grid-auto-rows: min-content;
  align-content: center;
  align-items: center;
  row-gap: 4px;
  padding: 2px 12px;
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

.ai-label {
  grid-column: 1;
  font-size: var(--krds-pc-font-size-label-small);
  color: var(--roady-text-tertiary);
  font-weight: var(--krds-font-weight-bold);
  letter-spacing: 0;
  line-height: 1.4;
}

.ai-value {
  grid-column: 1;
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
  line-height: 1.5;
}

.ai-result-badge {
  grid-column: 1;
  justify-self: start;
}

/* 파손율 진행 막대 */
.score-value-row {
  grid-column: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.score-value-row .ai-value {
  flex-shrink: 0;
}

.score-bar {
  flex: 1;
  min-width: 40px;
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

/* ── 고정 하단 판정 버튼 ── */
.detail-actions {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 12px;
  min-height: 104px;
  padding: 12px 24px 16px;
  border-top: 1px solid var(--roady-border-default);
  background: var(--roady-surface-default);
}

.action-guidance {
  grid-column: 1 / -1;
  min-height: 18px;
  margin: 0;
  font-size: 12px;
  line-height: 18px;
  color: var(--roady-text-tertiary);
  text-align: center;
}

.detail-actions[data-action-mode='waiting'] .action-guidance {
  color: var(--roady-status-warning);
}

.detail-actions[data-action-mode='completed'] .action-guidance {
  color: var(--roady-text-secondary);
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
  cursor: not-allowed;
  opacity: 0.6;
}

.review-completed-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 52px;
  border: 1px solid var(--roady-status-success);
  border-radius: 10px;
  background: color-mix(in srgb, var(--roady-status-success) 8%, #fff);
  color: var(--roady-status-success);
  font-size: 16px;
  font-weight: var(--krds-font-weight-bold);
}

.review-completed-controls {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.pending-request-controls {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 12px;
}

.request-create-btn {
  grid-column: 1 / -1;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--roady-brand-secondary);
  border-radius: 10px;
  background: var(--roady-surface-default);
  color: var(--roady-brand-secondary);
  font-size: 14px;
  font-weight: var(--krds-font-weight-bold);
  cursor: pointer;
  text-decoration: none;
}

.request-create-btn:hover {
  background: var(--roady-brand-primary-subtle);
}

.request-create-btn:focus-visible {
  outline: 0.3rem solid var(--roady-brand-secondary);
  outline-offset: 0.2rem;
}

.verdict-reset-btn {
  height: 52px;
  border: 1.5px solid var(--roady-border-default);
  border-radius: 10px;
  background: var(--roady-surface-default);
  color: var(--roady-text-secondary);
  font-size: 15px;
  font-weight: var(--krds-font-weight-bold);
  cursor: pointer;
}

.verdict-reset-btn:hover {
  border-color: var(--roady-brand-secondary);
  color: var(--roady-brand-secondary);
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

  .image-frame {
    min-height: 160px;
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

/* 패널 자체 너비를 줄였을 때 AI 판독 항목을 행 형태로 전환한다. */
@container (max-width: 560px) {
  .ai-card-body {
    display: flex;
    flex-direction: column;
    padding: 4px 12px 8px;
  }

  .ai-item {
    width: 100%;
    display: grid;
    grid-template-columns: 72px minmax(0, 1fr);
    column-gap: 12px;
    row-gap: 0;
    padding: 10px 4px;
  }

  .ai-label {
    grid-column: 1;
    align-self: center;
  }

  .ai-result-badge,
  .score-value-row {
    grid-column: 2;
    align-self: center;
  }

  .ai-divider {
    width: 100%;
    height: 1px;
    margin: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .score-bar-fill {
    transition: none;
  }
}

/* ── 관리자 판정 모달 ── */
.review-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgb(15 23 42 / 48%);
}

.review-modal {
  width: min(520px, 100%);
  max-height: calc(100vh - 48px);
  overflow-y: auto;
  padding: 24px;
  border-radius: 16px;
  background: var(--roady-surface-default);
  box-shadow: 0 20px 50px rgb(15 23 42 / 24%);
}

.review-modal--confirm {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 16px;
  width: min(480px, 100%);
}

.confirm-modal-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--roady-status-warning) 15%, #fff);
  color: var(--roady-status-warning);
  font-size: 22px;
  font-weight: var(--krds-font-weight-bold);
}

.confirm-modal-content h2 {
  margin: 0;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-heading-xsmall);
}

.confirm-modal-content p {
  margin: 8px 0 0;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-small);
  line-height: 1.6;
}

.confirm-modal-actions {
  grid-column: 1 / -1;
}

.review-modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.review-modal-eyebrow {
  margin: 0 0 4px;
  color: var(--roady-brand-secondary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
}

.review-modal-head h2 {
  margin: 0;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-heading-xsmall);
}

.review-modal-close {
  width: 40px;
  height: 40px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--roady-text-tertiary);
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
}

.review-modal-description {
  margin: 12px 0 20px;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-small);
}

.review-field {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
}

.review-field strong {
  color: var(--roady-status-danger);
}

.review-field small {
  color: var(--roady-text-tertiary);
  font-weight: var(--krds-font-weight-regular);
}

.review-field select {
  height: 48px;
}

.review-note-input {
  min-height: 112px;
  padding: 12px;
  resize: vertical;
}

.review-note-count {
  align-self: flex-end;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-label-xsmall);
  font-weight: var(--krds-font-weight-regular);
}

.review-form-error {
  margin: 12px 0 0;
  color: var(--roady-status-danger);
  font-size: var(--krds-pc-font-size-label-small);
}

.review-modal-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 24px;
}
</style>
