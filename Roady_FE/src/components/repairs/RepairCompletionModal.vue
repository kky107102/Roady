<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { RepairCompletePayload } from '@/types/repair'
import type { DamageImage } from '@/types/damage'

const props = withDefaults(
  defineProps<{
    submitting?: boolean
    readonly?: boolean
    completedAt?: string | null
    requestedAt?: string | null
    note?: string | null
    officialName?: string | null
    repairerName?: string | null
    beforeImages?: DamageImage[]
    imageBlobUrls?: Map<number, string>
    copyState?: 'idle' | 'success' | 'error'
  }>(),
  {
    submitting: false,
    readonly: false,
    completedAt: null,
    requestedAt: null,
    note: null,
    officialName: null,
    repairerName: null,
    beforeImages: () => [],
    imageBlobUrls: () => new Map<number, string>(),
    copyState: 'idle',
  },
)

const emit = defineEmits<{
  close: []
  confirm: [payload: RepairCompletePayload]
  copy: []
}>()

// ── 상태 ──────────────────────────────────────────────────────
type Step = 'input' | 'confirm'
const step = ref<Step>('input')

function localToday(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const completionDate = ref(props.completedAt?.slice(0, 10) ?? localToday())
const completionNote = ref(props.note ?? '')
const dateError = ref('')

const todayStr = computed(localToday)

const loadedBeforeImages = computed(() =>
  props.beforeImages.filter((image) => props.imageBlobUrls.has(image.id)),
)

function formatDateTime(value: string | null): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

function handleNext() {
  if (!completionDate.value) {
    dateError.value = '보수 완료 일자를 입력해 주세요.'
    return
  }
  if (completionDate.value > todayStr.value) {
    dateError.value = '미래 날짜는 선택할 수 없습니다.'
    return
  }
  dateError.value = ''
  step.value = 'confirm'
}

function handleConfirm() {
  emit('confirm', {
    completedAt: completionDate.value,
    note: completionNote.value.trim() || null,
  })
}

function handleBack() {
  step.value = 'input'
}

// ── 키보드 닫기 ────────────────────────────────────────────────
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && !props.submitting) emit('close')
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <div
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      :aria-label="readonly ? '완료 보고서 확인' : '보수 완료 처리'"
      @click.self="!submitting && emit('close')"
    >
      <div class="modal-panel" :class="{ 'is-report': readonly }">
        <!-- 헤더 -->
        <div class="modal-header">
          <h2 class="modal-title">{{ readonly ? '완료 보고서 확인' : '보수 완료 처리' }}</h2>
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

        <!-- 입력 단계 -->
        <div v-if="readonly" class="modal-body">
          <div class="assignment-grid">
            <div>
              <span class="field-label">담당 주무관</span>
              <p class="readonly-value">{{ officialName || '-' }}</p>
            </div>
            <div>
              <span class="field-label">보수 담당자</span>
              <p class="readonly-value">{{ repairerName || '-' }}</p>
            </div>
          </div>
          <div class="date-grid">
            <div>
              <span class="field-label">보수 요청 일자</span>
              <p class="readonly-value">{{ formatDateTime(requestedAt) }}</p>
            </div>
            <div>
              <span class="field-label">보수 완료 일자</span>
              <p class="readonly-value">{{ completionDate || '-' }}</p>
            </div>
          </div>

          <section class="report-section" aria-labelledby="before-photo-title">
            <h3 id="before-photo-title" class="field-label">보수 전 사진</h3>
            <div v-if="loadedBeforeImages.length" class="report-image-grid">
              <figure v-for="(image, index) in loadedBeforeImages" :key="image.id">
                <img :src="imageBlobUrls.get(image.id)" :alt="`보수 전 사진 ${index + 1}`" />
              </figure>
            </div>
            <div v-else class="report-image-empty" role="status">보수 전 이미지가 없습니다.</div>
          </section>

          <section class="report-section" aria-labelledby="after-photo-title">
            <h3 id="after-photo-title" class="field-label">보수 완료 사진</h3>
            <div class="report-image-empty" role="status">보수 완료 이미지가 없습니다.</div>
          </section>

          <div class="field-group">
            <span class="field-label">완료 메모</span>
            <p class="readonly-value readonly-value--note">{{ completionNote || '-' }}</p>
          </div>
        </div>

        <div v-else-if="step === 'input'" class="modal-body">
          <div class="assignment-grid">
            <div>
              <span class="field-label">담당 주무관</span>
              <p class="readonly-value">{{ officialName || '-' }}</p>
            </div>
            <div>
              <span class="field-label">보수 담당자</span>
              <p class="readonly-value">{{ repairerName || '-' }}</p>
            </div>
          </div>
          <div class="field-group">
            <label for="completion-date" class="field-label">
              보수 완료 일자 <span class="required">*</span>
            </label>
            <input
              id="completion-date"
              v-model="completionDate"
              type="date"
              class="krds-input date-input"
              :max="todayStr"
              :aria-invalid="!!dateError"
              @input="dateError = ''"
            />
            <p v-if="dateError" class="field-error" role="alert">{{ dateError }}</p>
            <label for="completion-note" class="field-label">완료 메모</label>
            <textarea
              id="completion-note"
              v-model="completionNote"
              class="krds-input note-input"
              maxlength="1000"
              rows="5"
              placeholder="보수 완료 내용을 입력해주세요. (선택)"
            />
            <p class="field-hint">선택 입력 · 최대 1,000자</p>
          </div>
        </div>

        <!-- 확인 단계 -->
        <div v-else class="modal-body modal-body--confirm">
          <svg
            class="confirm-icon"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          <p class="confirm-text">보수 완료로 처리하시겠습니까?</p>
          <p class="confirm-date">
            완료 일자: <strong>{{ completionDate }}</strong>
          </p>
          <p v-if="completionNote.trim()" class="confirm-note">{{ completionNote.trim() }}</p>
        </div>

        <!-- 푸터 -->
        <div class="modal-footer">
          <template v-if="readonly">
            <button
              type="button"
              class="krds-btn medium secondary"
              :aria-label="copyState === 'success' ? '복사 완료' : '완료 보고서 내용 복사'"
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
              {{ copyState === 'success' ? '복사 완료' : '내용 복사' }}
            </button>
            <button type="button" class="krds-btn medium filled primary" @click="emit('close')">
              확인
            </button>
          </template>
          <template v-else-if="step === 'input'">
            <button
              type="button"
              class="krds-btn medium secondary"
              :disabled="submitting"
              @click="emit('close')"
            >
              취소
            </button>
            <button
              type="button"
              class="krds-btn medium filled primary"
              :disabled="submitting"
              @click="handleNext"
            >
              다음
            </button>
          </template>
          <template v-else>
            <button
              type="button"
              class="krds-btn medium secondary"
              :disabled="submitting"
              @click="handleBack"
            >
              이전
            </button>
            <button
              type="button"
              class="krds-btn medium filled primary"
              :disabled="submitting"
              :aria-busy="submitting"
              @click="handleConfirm"
            >
              {{ submitting ? '처리 중...' : '확인' }}
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
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
  padding: 2rem;
}

.modal-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 64rem;
  max-height: 90dvh;
  background: var(--roady-surface-default);
  border-radius: 1.2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.24);
  overflow: hidden;
}

.modal-panel.is-report {
  max-width: 76rem;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2rem 2.4rem 1.6rem;
  border-bottom: 1px solid var(--roady-border-default);
}

.modal-title {
  margin: 0;
  font-size: 1.8rem;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
}

.modal-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3.6rem;
  height: 3.6rem;
  border: none;
  background: none;
  border-radius: 0.6rem;
  cursor: pointer;
  color: var(--roady-text-secondary);
  transition: background-color 0.1s;
}

.modal-close-btn:hover {
  background: var(--roady-surface-background);
}

.modal-close-btn:focus-visible {
  outline: 2px solid var(--roady-focus-ring);
  outline-offset: 2px;
}

.modal-close-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding: 2.4rem;
}

.modal-body--confirm {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.2rem;
  text-align: center;
  padding: 3.2rem 2.4rem;
}

.confirm-icon {
  color: var(--roady-status-success, #2ecc71);
}

.confirm-text {
  margin: 0;
  font-size: 1.6rem;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
}

.confirm-note {
  margin: 0;
  font-size: 1.4rem;
  color: var(--roady-text-secondary);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.confirm-date,
.readonly-value {
  margin: 0;
  font-size: 1.4rem;
  color: var(--roady-text-secondary);
}

.readonly-value--note {
  white-space: pre-wrap;
}

.assignment-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.6rem;
}

.date-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.6rem;
}

.date-grid > div,
.report-section {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.report-section h3 {
  margin: 0;
}

.report-image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
  gap: 1.2rem;
}

.report-image-grid figure {
  overflow: hidden;
  margin: 0;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-background);
  aspect-ratio: 4 / 3;
}

.report-image-grid img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.report-image-empty {
  display: grid;
  min-height: 10rem;
  place-items: center;
  padding: 1.6rem;
  border: 1px dashed var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-background);
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
}

@media (max-width: 640px) {
  .assignment-grid,
  .date-grid {
    grid-template-columns: 1fr;
  }
}

.assignment-grid > div {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

/* ── 입력 필드 ── */
.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.field-label {
  font-size: 1.4rem;
  font-weight: var(--krds-font-weight-bold);
  color: var(--roady-text-primary);
}

.note-input {
  width: 100%;
  resize: vertical;
}

.date-input {
  width: 100%;
}

.required,
.field-error {
  color: var(--roady-status-danger, #e74c3c);
}

.field-error {
  margin: 0;
  font-size: 1.3rem;
}

.field-hint {
  margin: 0;
  font-size: 1.2rem;
  color: var(--roady-text-tertiary);
}

/* ── 푸터 ── */
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.6rem 2.4rem;
  border-top: 1px solid var(--roady-border-default);
}
</style>
