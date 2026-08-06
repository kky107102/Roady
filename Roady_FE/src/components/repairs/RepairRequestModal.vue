<script setup lang="ts">
import { ref, computed } from 'vue'
import type { DamageDetail, DamageImage } from '@/types/damage'
import type { UserSummary } from '@/types/auth'
import type { RepairRequestPayload } from '@/types/repair'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { BadgeType } from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import DocumentSection from '@/components/common/DocumentSection.vue'
import { useDialogFocus } from '@/composables/useDialogFocus'
import {
  formatCaseId,
  formatRepairLocation,
  formatPriorityLabel,
  formatDamageTypeLabel,
  priorityBadgeType,
} from '@/utils/repairRequest'

const props = withDefaults(
  defineProps<{
    detail: DamageDetail
    imageBlobUrls: Map<number, string>
    imagesLoading?: boolean
    readonly?: boolean
    submitting?: boolean
    editing?: boolean
    officialName?: string | null
    repairers?: UserSummary[]
    copyState?: 'idle' | 'success' | 'error'
    editable?: boolean
  }>(),
  {
    imagesLoading: false,
    readonly: false,
    submitting: false,
    editing: false,
    officialName: null,
    repairers: () => [],
    copyState: 'idle',
    editable: false,
  },
)

const emit = defineEmits<{
  close: []
  cancelEdit: []
  confirm: [payload: RepairRequestPayload]
  copy: []
  edit: []
}>()

const note = ref<string>(
  props.readonly || props.editing ? (props.detail.repairRequestNote ?? '') : '',
)
const priority = ref(props.detail.processingPriority ?? '')
const damageType = ref(props.detail.reviewDamageType ?? '')
const repairerId = ref<number | null>(props.detail.repairerId ?? null)
const formError = ref('')
const modalRef = ref<HTMLElement | null>(null)

useDialogFocus(modalRef, true, {
  onEscape: () => {
    if (!props.submitting) emit('close')
  },
})

const PRIORITY_OPTIONS = [
  { value: 'URGENT', label: '긴급' },
  { value: 'HIGH', label: '높음' },
  { value: 'NORMAL', label: '보통' },
  { value: 'LOW', label: '낮음' },
]

const DAMAGE_TYPE_OPTIONS = [
  { value: 'LARGE_MISSING', label: '큰 결손' },
  { value: 'SMALL_MISSING', label: '작은 결손' },
  { value: 'WEAR', label: '마모' },
  { value: 'CRACK', label: '균열' },
  { value: 'OTHER', label: '기타' },
]

// ── 표시 헬퍼 ─────────────────────────────────────────────────
const caseId = computed(() => formatCaseId(props.detail.id, props.detail.createdAt))
const location = computed(() => formatRepairLocation(props.detail))
const priorityLabel = computed(() => formatPriorityLabel(priority.value))
const priorityType = computed<BadgeType>(() => priorityBadgeType(priority.value))
const damageTypeLabel = computed(() => formatDamageTypeLabel(damageType.value))
const repairerName = computed(() => {
  if (props.detail.repairerName) return props.detail.repairerName
  return props.repairers.find((user) => user.id === repairerId.value)?.name ?? '-'
})

const loadedImages = computed(() =>
  (props.detail.images ?? []).filter((img) => props.imageBlobUrls.has(img.id)),
)

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

// ── 이미지 다운로드 ────────────────────────────────────────────
function downloadImage(img: DamageImage) {
  const blobUrl = props.imageBlobUrls.get(img.id)
  if (!blobUrl) return
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = img.originalFilename || `image-${img.sortOrder}.jpg`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

// ── 제출 ──────────────────────────────────────────────────────
function handleConfirm() {
  if (!priority.value || !damageType.value) {
    formError.value = '우선순위와 파손 유형을 모두 선택해 주세요.'
    return
  }
  emit('confirm', {
    note: note.value.trim() || null,
    processingPriority: priority.value,
    reviewDamageType: damageType.value,
    repairerId: repairerId.value,
  })
}
</script>

<template>
  <Teleport to="body">
    <div
      ref="modalRef"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      tabindex="-1"
      :aria-label="readonly ? '요청서 확인' : editing ? '보수 요청서 수정' : '보수 요청서 작성'"
      @click.self="emit('close')"
    >
      <div class="modal-panel">
        <!-- 헤더 -->
        <div class="modal-header">
          <h2 class="modal-title">
            {{ readonly ? '요청서 확인' : editing ? '보수 요청서 수정' : '보수 요청서 작성' }}
          </h2>
          <div class="modal-header-actions">
            <button
              v-if="readonly && editable"
              type="button"
              class="modal-edit-btn"
              @click="emit('edit')"
            >
              <span>수정하기</span>
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L8 18l-4 1 1-4Z" />
              </svg>
            </button>
            <button
              type="button"
              class="modal-close-btn"
              aria-label="닫기"
              :disabled="submitting"
              @click="emit('close')"
            >
              <svg
                width="20"
                height="20"
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
        </div>

        <!-- 본문 -->
        <div class="modal-body">
          <!-- 사건 기본 정보 -->
          <DocumentSection title="사건 정보">
            <dl class="info-grid">
              <div class="info-row">
                <dt class="info-label">사건번호</dt>
                <dd class="info-value">
                  <span class="case-id-badge">{{ caseId }}</span>
                </dd>
              </div>
              <div class="info-row">
                <dt class="info-label">사건명</dt>
                <dd class="info-value">{{ detail.description || '미확인' }}</dd>
              </div>
              <div class="info-row">
                <dt class="info-label">담당 주무관</dt>
                <dd class="info-value">{{ officialName || detail.assignedToName || '-' }}</dd>
              </div>
              <div class="info-row">
                <dt class="info-label">보수 담당자</dt>
                <dd v-if="readonly" class="info-value">{{ repairerName }}</dd>
                <dd v-else class="info-value info-value--field">
                  <select v-model="repairerId" class="krds-input request-select">
                    <option :value="null">미지정</option>
                    <option v-for="repairer in repairers" :key="repairer.id" :value="repairer.id">
                      {{ repairer.name }}
                    </option>
                  </select>
                </dd>
              </div>
              <div class="info-row">
                <dt class="info-label">탐지 일시</dt>
                <dd class="info-value">{{ formatDateTime(detail.capturedAt) }}</dd>
              </div>
              <div class="info-row">
                <dt class="info-label">위치</dt>
                <dd class="info-value">{{ location }}</dd>
              </div>
              <div v-if="detail.latitude != null && detail.longitude != null" class="info-row">
                <dt class="info-label">좌표</dt>
                <dd class="info-value">
                  {{ detail.latitude?.toFixed(6) }}, {{ detail.longitude?.toFixed(6) }}
                </dd>
              </div>
            </dl>
          </DocumentSection>

          <!-- 관리자 판정 -->
          <DocumentSection title="관리자 판정">
            <dl class="info-grid">
              <div class="info-row">
                <dt class="info-label">우선순위</dt>
                <dd v-if="readonly" class="info-value">
                  <StatusBadge :type="priorityType" :label="priorityLabel" />
                </dd>
                <dd v-else class="info-value info-value--field">
                  <select v-model="priority" class="krds-input request-select" required>
                    <option value="" disabled>우선순위 선택</option>
                    <option
                      v-for="option in PRIORITY_OPTIONS"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                </dd>
              </div>
              <div class="info-row">
                <dt class="info-label">파손 유형</dt>
                <dd v-if="readonly" class="info-value">
                  <StatusBadge type="neutral" :label="damageTypeLabel" />
                </dd>
                <dd v-else class="info-value info-value--field">
                  <select v-model="damageType" class="krds-input request-select" required>
                    <option value="" disabled>파손 유형 선택</option>
                    <option
                      v-for="option in DAMAGE_TYPE_OPTIONS"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                </dd>
              </div>
            </dl>
          </DocumentSection>

          <!-- 탐지 이미지 -->
          <DocumentSection title="탐지 이미지">
            <div class="image-section">
              <div v-if="detail.imageCount > 0 && imagesLoading" class="image-loading">
                <LoadingSpinner label="이미지 불러오는 중" />
              </div>
              <div v-else-if="loadedImages.length > 0" class="image-list">
                <div v-for="img in loadedImages" :key="img.id" class="image-item">
                  <img
                    :src="imageBlobUrls.get(img.id)"
                    :alt="`탐지 이미지 ${img.sortOrder}`"
                    class="modal-img"
                  />
                  <button
                    type="button"
                    class="img-download-btn krds-btn small secondary"
                    :aria-label="`이미지 ${img.sortOrder} 다운로드`"
                    @click="downloadImage(img)"
                  >
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
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    다운로드
                  </button>
                </div>
              </div>
              <div v-else-if="detail.imageCount > 0" class="image-empty">
                이미지를 불러올 수 없습니다.
              </div>
              <div v-else class="image-empty">등록된 탐지 이미지가 없습니다.</div>
            </div>
          </DocumentSection>

          <!-- 비고 -->
          <DocumentSection title="비고">
            <p v-if="readonly" class="note-text">{{ note || '-' }}</p>
            <div v-else class="note-field">
              <label for="repair-request-note" class="sr-only">
                외부 보수 담당자에게 전달할 내용
              </label>
              <textarea
                id="repair-request-note"
                v-model="note"
                class="note-textarea krds-input"
                rows="4"
                maxlength="1000"
                placeholder="외부 보수 담당자에게 전달할 내용을 입력하세요 (선택)"
                aria-describedby="repair-note-hint"
              />
              <p id="repair-note-hint" class="note-hint">{{ note.length }}/1000자</p>
            </div>
          </DocumentSection>
          <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>
        </div>

        <!-- 푸터 -->
        <div class="modal-footer">
          <template v-if="readonly">
            <button
              type="button"
              class="krds-btn medium secondary"
              :aria-label="copyState === 'success' ? '복사 완료' : '최종 요청 정보 클립보드에 복사'"
              @click="emit('copy')"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
              {{ copyState === 'success' ? '복사 완료' : '요청 복사' }}
            </button>
            <button type="button" class="krds-btn medium filled primary" @click="emit('close')">
              확인
            </button>
          </template>
          <template v-else>
            <button
              type="button"
              class="krds-btn medium secondary"
              :disabled="submitting"
              @click="editing ? emit('cancelEdit') : emit('close')"
            >
              취소
            </button>
            <button
              type="button"
              class="krds-btn medium filled primary"
              :disabled="submitting"
              :aria-busy="submitting"
              @click="handleConfirm"
            >
              {{ submitting ? '처리 중...' : editing ? '저장' : '보수 요청하기' }}
            </button>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: var(--roady-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--roady-z-modal);
  padding: 2rem;
}

.modal-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 64rem;
  max-height: 90dvh;
  background: var(--roady-surface-default);
  border-radius: var(--roady-radius-dialog);
  box-shadow: var(--roady-shadow-dialog);
  overflow: hidden;
}

/* ── 헤더 ── */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2rem 2.4rem 1.6rem;
  border-bottom: 1px solid var(--roady-border-default);
  flex-shrink: 0;
}

.modal-title {
  margin: 0;
  font-size: var(--krds-pc-font-size-heading-small);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
}

.modal-header-actions {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.modal-edit-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  min-height: 3.6rem;
  padding: 0 1rem;
  border: 1px solid var(--roady-border-default);
  background: var(--roady-surface-default);
  border-radius: var(--roady-radius-control);
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-medium);
  cursor: pointer;
}

.modal-edit-btn:hover {
  background: var(--roady-surface-background);
}

.modal-edit-btn:focus-visible {
  outline: 2px solid var(--roady-focus-ring);
  outline-offset: 2px;
}

.modal-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3.6rem;
  height: 3.6rem;
  border: none;
  background: none;
  border-radius: var(--roady-radius-control);
  cursor: pointer;
  color: var(--roady-text-secondary);
  transition: background-color var(--roady-transition-fast);
}

.modal-close-btn:hover {
  background: var(--roady-surface-background);
  color: var(--roady-text-primary);
}

.modal-close-btn:focus-visible {
  outline: 2px solid var(--roady-focus-ring);
  outline-offset: 2px;
}

.modal-close-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── 본문 ── */
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 2.4rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  margin: 0;
}

.info-row {
  display: flex;
  align-items: baseline;
  gap: 1.2rem;
}

.info-label {
  flex-shrink: 0;
  min-width: 8rem;
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-tertiary);
}

.info-value {
  font-size: var(--krds-pc-font-size-body-small);
  color: var(--roady-text-primary);
  line-height: 1.5;
  word-break: break-word;
}

.info-value--field {
  flex: 1;
}

.request-select {
  width: 100%;
  min-width: 18rem;
}

.case-id-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.3rem 0.8rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 4px;
  font-size: var(--krds-pc-font-size-label-xsmall);
  font-family: monospace;
  color: var(--roady-text-secondary);
  background: var(--roady-surface-background);
}

/* ── 이미지 ── */
.image-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.image-loading {
  display: flex;
  justify-content: center;
  padding: 2rem;
}

.image-list {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.image-item {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.modal-img {
  width: 100%;
  max-height: 32rem;
  object-fit: contain;
  border-radius: 0.8rem;
  background: var(--roady-surface-background);
  display: block;
}

.img-download-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  align-self: flex-start;
}

.image-empty {
  padding: 2rem;
  text-align: center;
  font-size: var(--krds-pc-font-size-body-small);
  color: var(--roady-text-tertiary);
  border: 1px dashed var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-background);
}

/* ── 비고 ── */
.note-text {
  margin: 0;
  font-size: var(--krds-pc-font-size-body-small);
  color: var(--roady-text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
  min-height: 4rem;
}

.note-field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.note-textarea {
  width: 100%;
  resize: vertical;
  font-size: var(--krds-pc-font-size-body-small);
  line-height: 1.6;
  min-height: 9.6rem;
}

.note-hint {
  margin: 0;
  font-size: var(--krds-pc-font-size-label-xsmall);
  color: var(--roady-text-tertiary);
  text-align: right;
}

.form-error {
  margin: 0;
  color: var(--roady-status-danger, #e74c3c);
  font-size: var(--krds-pc-font-size-label-small);
}

/* ── 푸터 ── */
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.6rem 2.4rem;
  border-top: 1px solid var(--roady-border-default);
  flex-shrink: 0;
}

/* ── 접근성 ── */
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
</style>
