<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { RepairCompletePayload } from '@/types/repair'

const props = withDefaults(
  defineProps<{
    submitting?: boolean
    readonly?: boolean
    completedAt?: string | null
    note?: string | null
    officialName?: string | null
    repairerName?: string | null
  }>(),
  {
    submitting: false,
    readonly: false,
    completedAt: null,
    note: null,
    officialName: null,
    repairerName: null,
  },
)

const emit = defineEmits<{
  close: []
  confirm: [payload: RepairCompletePayload]
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
      <div class="modal-panel">
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
          <div class="field-group">
            <span class="field-label">보수 완료 일자</span>
            <p class="readonly-value">{{ completionDate || '-' }}</p>
          </div>
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
