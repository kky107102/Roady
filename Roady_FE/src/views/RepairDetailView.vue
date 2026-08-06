<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { damagesApi } from '@/api/damages'
import { repairsApi } from '@/api/repairs'
import { usersApi } from '@/api/users'
import { useNotificationStore } from '@/stores/notification'
import type { DamageDetail, DamageImage } from '@/types/damage'
import type { UserSummary } from '@/types/auth'
import type { RepairCompletePayload, RepairRequestPayload } from '@/types/repair'
import type { BadgeType } from '@/components/common/StatusBadge.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import RepairRequestModal from '@/components/repairs/RepairRequestModal.vue'
import RepairCompletionModal from '@/components/repairs/RepairCompletionModal.vue'
import {
  buildRepairRequestText,
  formatCaseId,
  formatPriorityLabel,
  formatDamageTypeLabel,
  priorityBadgeType,
} from '@/utils/repairRequest'
import { repairStatusInfo } from '@/utils/repairManagement'

// ── 라우터 ──────────────────────────────────────────────────
const route = useRoute()
const router = useRouter()
const notification = useNotificationStore()

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
const users = ref<UserSummary[]>([])
let fetchSeq = 0

onMounted(async () => {
  try {
    users.value = await usersApi.list({ role: 'REPAIRER', active: true })
  } catch {
    users.value = []
  }
})

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
  (id) => {
    if (id != null) fetchDetail(id)
  },
  { immediate: true },
)

onUnmounted(() => {
  ++fetchSeq
  for (const url of imageBlobUrls.value.values()) URL.revokeObjectURL(url)
})

// ── 표시 헬퍼 ─────────────────────────────────────────────
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

function formatDate(str: string | null | undefined): string {
  if (!str) return '-'
  const d = new Date(str)
  if (isNaN(d.getTime())) return str
  return d.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })
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
  return repairStatusInfo(status)
})

const priorityLabel = computed(() => formatPriorityLabel(detail.value?.processingPriority))

const priorityType = computed<BadgeType>(() => {
  return priorityBadgeType(detail.value?.processingPriority)
})

const damageTypeLabel = computed(() => formatDamageTypeLabel(detail.value?.reviewDamageType))

const loadedImages = computed(() =>
  (detail.value?.images ?? []).filter((img) => imageBlobUrls.value.has(img.id)),
)

const caseIdText = computed(() => {
  if (!detail.value) return ''
  return formatCaseId(detail.value.id, detail.value.createdAt)
})

const repairers = computed(() =>
  users.value.filter((user) => user.active && user.role === 'REPAIRER'),
)
const officialName = computed(() => {
  if (detail.value?.assignedToName) return detail.value.assignedToName
  return users.value.find((user) => user.id === detail.value?.assignedTo)?.name ?? null
})

// ── 보수 요청 모달 상태 ────────────────────────────────────
const requestModalOpen = ref(false)
const requestModalMode = ref<'create' | 'view' | 'edit'>('create')
const requestConfirmOpen = ref(false)
const pendingRequest = ref<RepairRequestPayload | null>(null)
const requestSubmitting = ref(false)
const requestActionHandledFor = ref<string | null>(null)

function openRequestModal(mode: 'create' | 'view' | 'edit') {
  requestModalMode.value = mode
  requestModalOpen.value = true
}

function closeRequestModal() {
  if (requestSubmitting.value) return
  requestModalOpen.value = false
}

watch(
  [damageId, () => detail.value?.currentStatus, () => route.query.action],
  ([id, status, action]) => {
    const actionKey = id != null && typeof action === 'string' ? `${id}:${action}` : null
    if (
      id != null &&
      actionKey != null &&
      requestActionHandledFor.value !== actionKey &&
      ((status === 'REQUESTED' && action === 'create-request') ||
        (['REPAIR_IN_PROGRESS', 'REPAIR_COMPLETED'].includes(status ?? '') &&
          action === 'view-request'))
    ) {
      requestActionHandledFor.value = actionKey
      openRequestModal(action === 'create-request' ? 'create' : 'view')
    }
  },
  { immediate: true },
)

async function onRequestModalConfirm(payload: RepairRequestPayload) {
  if (requestModalMode.value === 'edit') {
    await saveRepairRequestEdit(payload)
    return
  }
  requestModalOpen.value = false
  pendingRequest.value = payload
  requestConfirmOpen.value = true
}

function cancelRequestEdit() {
  if (requestSubmitting.value) return
  requestModalMode.value = 'view'
}

async function saveRepairRequestEdit(payload: RepairRequestPayload) {
  if (!detail.value || requestSubmitting.value) return
  requestSubmitting.value = true
  try {
    const updated = await repairsApi.updateRequest(detail.value.id, payload)
    const repairerName =
      repairers.value.find((user) => user.id === payload.repairerId)?.name ?? null
    detail.value = {
      ...detail.value,
      ...updated,
      processingPriority: payload.processingPriority,
      reviewDamageType: payload.reviewDamageType,
      repairerId: payload.repairerId,
      repairerName,
      repairRequestNote: payload.note,
    }
    requestModalMode.value = 'view'
    notification.success('보수 요청서가 수정되었습니다.')
  } catch {
    notification.error('보수 요청서 수정 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.')
  } finally {
    requestSubmitting.value = false
  }
}

async function confirmRepairRequest() {
  if (!detail.value || requestSubmitting.value) return
  requestSubmitting.value = true
  try {
    const payload = pendingRequest.value
    if (!payload?.processingPriority || !payload.reviewDamageType) return
    const updated = await repairsApi.submitRequest(detail.value.id, payload)
    const repairerName =
      repairers.value.find((user) => user.id === payload.repairerId)?.name ?? null
    detail.value = {
      ...detail.value,
      ...updated,
      processingPriority: payload.processingPriority,
      reviewDamageType: payload.reviewDamageType,
      repairerId: payload.repairerId,
      repairerName,
      repairRequestNote: payload.note,
    }
    requestConfirmOpen.value = false
    notification.success('보수 요청 처리되었습니다.')
  } catch {
    notification.error('보수 요청 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.')
  } finally {
    requestSubmitting.value = false
  }
}

// ── 요청 취소 확인 다이얼로그 ─────────────────────────────
const cancelConfirmOpen = ref(false)
const cancelSubmitting = ref(false)

async function confirmCancelRequest() {
  if (!detail.value || cancelSubmitting.value) return
  cancelSubmitting.value = true
  try {
    const updated = await repairsApi.cancelRequest(detail.value.id, { note: null })
    detail.value = { ...detail.value, ...updated }
    cancelConfirmOpen.value = false
    notification.success('보수 요청이 취소되었습니다.')
  } catch {
    notification.error('요청 취소 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.')
  } finally {
    cancelSubmitting.value = false
  }
}

// ── 보수 완료 모달 ─────────────────────────────────────────
const completionModalOpen = ref(false)
const completionModalReadonly = ref(false)
const completionSubmitting = ref(false)
const completionCopyState = ref<'idle' | 'success' | 'error'>('idle')
let completionCopyStateTimer: ReturnType<typeof setTimeout> | null = null
const completionActionHandledFor = ref<number | null>(null)

function openCompletionModal(readonly = false) {
  completionModalReadonly.value = readonly
  completionCopyState.value = 'idle'
  completionModalOpen.value = true
}

watch(
  [damageId, () => detail.value?.currentStatus, () => route.query.action],
  ([id, status, action]) => {
    if (
      id != null &&
      status === 'REPAIR_COMPLETED' &&
      action === 'view-completion-report' &&
      completionActionHandledFor.value !== id
    ) {
      completionActionHandledFor.value = id
      openCompletionModal(true)
    }
  },
  { immediate: true },
)

async function onCompletionConfirm(payload: RepairCompletePayload) {
  if (!detail.value || completionSubmitting.value) return
  completionSubmitting.value = true
  try {
    const updated = await repairsApi.completeRepair(detail.value.id, payload)
    detail.value = {
      ...detail.value,
      ...updated,
      repairCompletedAt: payload.completedAt,
      repairCompletionNote: payload.note,
    }
    completionModalOpen.value = false
    notification.success('보수 완료 처리되었습니다.')
  } catch {
    notification.error('보수 완료 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.')
  } finally {
    completionSubmitting.value = false
  }
}

const noRepairConfirmOpen = ref(false)
const noRepairSubmitting = ref(false)

async function confirmNoRepair() {
  if (!detail.value || noRepairSubmitting.value) return
  noRepairSubmitting.value = true
  try {
    await damagesApi.updateReview(detail.value.id, 'CANCELED')
    detail.value = { ...detail.value, currentStatus: 'CANCELED' }
    noRepairConfirmOpen.value = false
    notification.success('보수 불필요로 처리되었습니다.')
  } catch {
    notification.error('보수 불필요 처리 중 오류가 발생했습니다.')
  } finally {
    noRepairSubmitting.value = false
  }
}

async function copyCompletionReport() {
  if (!detail.value) return
  const report = [
    '[Roady 보수 완료 보고서]',
    '',
    `사건번호: ${caseIdText.value}`,
    `담당 주무관: ${officialName.value || '-'}`,
    `보수 담당자: ${detail.value.repairerName || '-'}`,
    `보수 요청 일자: ${formatDateTime(detail.value.repairRequestedAt)}`,
    `보수 완료 일자: ${formatDate(detail.value.repairCompletedAt)}`,
    `보수 전 사진: ${detail.value.images.length}장`,
    '보수 완료 사진: 이미지 없음',
    `완료 메모: ${detail.value.repairCompletionNote?.trim() || '-'}`,
  ].join('\n')

  try {
    await navigator.clipboard.writeText(report)
    completionCopyState.value = 'success'
    notification.success('완료 보고서 내용이 클립보드에 복사되었습니다.')
  } catch {
    completionCopyState.value = 'error'
    notification.error('클립보드 복사에 실패했습니다. 브라우저 권한을 확인해주세요.')
  } finally {
    if (completionCopyStateTimer) clearTimeout(completionCopyStateTimer)
    completionCopyStateTimer = setTimeout(() => {
      completionCopyState.value = 'idle'
    }, 3000)
  }
}

// ── 요청 정보 복사 ─────────────────────────────────────────
const copyState = ref<'idle' | 'success' | 'error'>('idle')
let copyStateTimer: ReturnType<typeof setTimeout> | null = null

async function copyRequestInfo() {
  if (!detail.value) return
  const url = window.location.href
  const text = buildRepairRequestText(detail.value, url)
  try {
    await navigator.clipboard.writeText(text)
    copyState.value = 'success'
    notification.success('요청 정보가 클립보드에 복사되었습니다.')
  } catch {
    copyState.value = 'error'
    notification.error('클립보드 복사에 실패했습니다. 브라우저 권한을 확인해주세요.')
  } finally {
    if (copyStateTimer) clearTimeout(copyStateTimer)
    copyStateTimer = setTimeout(() => {
      copyState.value = 'idle'
    }, 3000)
  }
}

onUnmounted(() => {
  if (copyStateTimer) clearTimeout(copyStateTimer)
  if (completionCopyStateTimer) clearTimeout(completionCopyStateTimer)
})
</script>

<template>
  <div class="repair-detail-view">
    <button type="button" class="back-link" aria-label="사건 목록으로 돌아가기" @click="handleBack">
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
      사건 목록
    </button>

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
          <span class="badge-case-id">{{ caseIdText }}</span>
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

        <!-- 오른쪽: 보수 현황 -->
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

            <!-- ── REQUESTED: 요청 전 ── -->
            <template v-if="detail.currentStatus === 'REQUESTED'">
              <div class="action-section" aria-label="보수 요청 액션">
                <p class="action-description">외부 보수 담당자에게 보수 요청을 전송하세요.</p>
                <div class="action-btn-group">
                  <button
                    type="button"
                    class="krds-btn medium filled primary action-btn"
                    @click="openRequestModal('create')"
                  >
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
                      <line x1="22" y1="2" x2="11" y2="13" />
                      <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                    보수 요청
                  </button>
                  <button
                    type="button"
                    class="krds-btn medium secondary action-btn cancel-btn"
                    @click="noRepairConfirmOpen = true"
                  >
                    보수 불필요 처리
                  </button>
                </div>
              </div>
            </template>

            <!-- ── REPAIR_IN_PROGRESS: 요청 완료 ── -->
            <template v-else-if="detail.currentStatus === 'REPAIR_IN_PROGRESS'">
              <dl class="repair-info-list">
                <div class="repair-info-row">
                  <dt class="repair-info-label">요청 일자</dt>
                  <dd class="repair-info-value">{{ formatDate(detail.updatedAt) }}</dd>
                </div>
                <div class="repair-info-row">
                  <dt class="repair-info-label">보수 담당자</dt>
                  <dd class="repair-info-value">{{ detail.repairerName || '-' }}</dd>
                </div>
              </dl>
              <div class="action-section" aria-label="요청 완료 상태 액션">
                <div class="action-btn-group">
                  <button
                    type="button"
                    class="krds-btn medium secondary action-btn"
                    @click="openRequestModal('view')"
                  >
                    요청서 확인
                  </button>
                </div>
                <div class="action-btn-group action-btn-group--secondary">
                  <button
                    type="button"
                    class="krds-btn small secondary action-btn cancel-btn"
                    @click="cancelConfirmOpen = true"
                  >
                    요청 취소
                  </button>
                </div>
                <div class="action-btn-group action-btn-group--complete">
                  <button
                    type="button"
                    class="krds-btn medium filled primary action-btn"
                    @click="openCompletionModal(false)"
                  >
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
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                      <polyline points="22 4 12 14.01 9 11.01" />
                    </svg>
                    보수 완료
                  </button>
                </div>
              </div>
            </template>

            <!-- ── REPAIR_COMPLETED: 보수 완료 ── -->
            <template v-else-if="detail.currentStatus === 'REPAIR_COMPLETED'">
              <dl class="repair-info-list">
                <div class="repair-info-row">
                  <dt class="repair-info-label">완료 일자</dt>
                  <dd class="repair-info-value">
                    {{ formatDate(detail.repairCompletedAt || detail.updatedAt) }}
                  </dd>
                </div>
                <div class="repair-info-row">
                  <dt class="repair-info-label">보수 담당자</dt>
                  <dd class="repair-info-value">{{ detail.repairerName || '-' }}</dd>
                </div>
              </dl>
              <div class="action-section" aria-label="보수 완료 상태 액션">
                <div class="action-btn-group">
                  <button
                    type="button"
                    class="krds-btn medium secondary action-btn"
                    @click="openRequestModal('view')"
                  >
                    요청서 확인
                  </button>
                  <button
                    type="button"
                    class="krds-btn medium secondary action-btn"
                    @click="openCompletionModal(true)"
                  >
                    완료 보고서 확인
                  </button>
                </div>
              </div>
            </template>

            <!-- ── 기타 상태 ── -->
            <template v-else>
              <p class="side-note">
                현재 상태({{ detail.currentStatus }})는 보수 관리 대상이 아닙니다.
              </p>
            </template>
          </section>
        </div>
      </div>
    </div>

    <!-- ── 모달들 ── -->

    <!-- 요청서 상세 모달 -->
    <RepairRequestModal
      v-if="requestModalOpen && detail"
      :key="requestModalMode"
      :detail="detail"
      :image-blob-urls="imageBlobUrls"
      :images-loading="imagesLoading"
      :readonly="requestModalMode === 'view'"
      :editing="requestModalMode === 'edit'"
      :submitting="requestSubmitting"
      :official-name="officialName"
      :repairers="repairers"
      :copy-state="copyState"
      :editable="detail.currentStatus === 'REPAIR_IN_PROGRESS'"
      @close="closeRequestModal"
      @cancel-edit="cancelRequestEdit"
      @confirm="onRequestModalConfirm"
      @copy="copyRequestInfo"
      @edit="openRequestModal('edit')"
    />

    <ConfirmDialog
      v-if="requestConfirmOpen"
      title="보수 요청을 전송할까요?"
      description="확인하면 선택한 담당자에게 보수 요청이 전달됩니다."
      confirm-label="요청 전송"
      :busy="requestSubmitting"
      @cancel="requestConfirmOpen = false"
      @confirm="confirmRepairRequest"
    />

    <ConfirmDialog
      v-if="noRepairConfirmOpen"
      title="보수 불필요로 처리할까요?"
      description="확인하면 해당 사건은 보수 대상에서 제외됩니다."
      confirm-label="보수 불필요 처리"
      :busy="noRepairSubmitting"
      @cancel="noRepairConfirmOpen = false"
      @confirm="confirmNoRepair"
    />

    <ConfirmDialog
      v-if="cancelConfirmOpen"
      title="보수 요청을 취소할까요?"
      description="취소한 요청은 다시 보수 요청할 수 있습니다."
      confirm-label="요청 취소"
      tone="danger"
      :busy="cancelSubmitting"
      @cancel="cancelConfirmOpen = false"
      @confirm="confirmCancelRequest"
    />

    <!-- 보수 완료 모달 -->
    <RepairCompletionModal
      v-if="completionModalOpen"
      :submitting="completionSubmitting"
      :readonly="completionModalReadonly"
      :completed-at="detail?.repairCompletedAt || null"
      :requested-at="detail?.repairRequestedAt || null"
      :note="detail?.repairCompletionNote || null"
      :official-name="officialName"
      :repairer-name="detail?.repairerName || null"
      :before-images="loadedImages"
      :image-blob-urls="imageBlobUrls"
      :copy-state="completionCopyState"
      @close="completionModalOpen = false"
      @confirm="onCompletionConfirm"
      @copy="copyCompletionReport"
    />
  </div>
</template>

<style scoped>
.repair-detail-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.back-link {
  align-self: flex-start;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 2.4rem 2rem 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--roady-brand-secondary);
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  cursor: pointer;
  transition: color 0.15s ease;
  white-space: nowrap;
}

.back-link:hover {
  color: var(--roady-text-primary);
}

.back-link:focus-visible {
  outline: 2px solid var(--roady-focus-ring);
  outline-offset: 2px;
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
  padding: 2rem 2rem 2.4rem;
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
  padding-bottom: 1.2rem;
  border-bottom: 1px solid var(--roady-border-default);
  margin-bottom: 1.2rem;
}

.status-row-label {
  font-size: 1.3rem;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-tertiary);
  min-width: 6rem;
}

/* ── 보수 정보 목록 ── */
.repair-info-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  margin: 0 0 1.6rem;
}

.repair-info-row {
  display: flex;
  align-items: baseline;
  gap: 0.8rem;
}

.repair-info-label {
  flex-shrink: 0;
  min-width: 7rem;
  font-size: 1.3rem;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-tertiary);
}

.repair-info-value {
  font-size: 1.4rem;
  color: var(--roady-text-primary);
}

/* ── 액션 섹션 ── */
.action-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.action-description {
  margin: 0;
  font-size: 1.3rem;
  color: var(--roady-text-secondary);
  line-height: 1.5;
}

.action-btn-group {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.action-btn-group--secondary {
  padding-top: 0.4rem;
  border-top: 1px solid var(--roady-border-default);
}

.action-btn-group--complete {
  padding-top: 0.4rem;
}

.action-btn {
  width: 100%;
  justify-content: center;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.cancel-btn {
  color: var(--roady-status-danger, #e74c3c);
  border-color: var(--roady-status-danger, #e74c3c);
}

.cancel-btn:hover:not(:disabled) {
  background: rgba(231, 76, 60, 0.06);
}

/* ── 공통 ── */
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
