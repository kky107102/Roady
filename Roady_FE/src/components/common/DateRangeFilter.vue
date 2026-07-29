<script setup lang="ts">
const props = defineProps<{
  from: string
  to: string
  error?: string
  activePreset?: number | null
}>()

const emit = defineEmits<{
  'update:from': [string]
  'update:to': [string]
  'update:activePreset': [number | null]
  'preset-apply': [{ from: string; to: string }]
}>()

const PRESETS = [
  { label: '오늘', offset: 0 },
  { label: '7일', offset: 6 },
  { label: '30일', offset: 29 },
]

function toDateString(d: Date): string {
  return d.toISOString().slice(0, 10)
}

function setPreset(offset: number, idx: number) {
  const toDate = new Date()
  const fromDate = new Date()
  fromDate.setDate(fromDate.getDate() - offset)
  const fromStr = toDateString(fromDate)
  const toStr = toDateString(toDate)
  emit('update:activePreset', idx)
  emit('update:from', fromStr)
  emit('update:to', toStr)
  emit('preset-apply', { from: fromStr, to: toStr })
}

function onFromInput(e: Event) {
  emit('update:activePreset', null)
  emit('update:from', (e.target as HTMLInputElement).value)
}

function onToInput(e: Event) {
  emit('update:activePreset', null)
  emit('update:to', (e.target as HTMLInputElement).value)
}
</script>

<template>
  <div class="date-range-filter">
    <div class="date-range-filter__row">
      <span class="toolbar-label">기간</span>

      <div class="preset-group" role="group" aria-label="기간 프리셋">
        <button
          v-for="(p, idx) in PRESETS"
          :key="p.label"
          type="button"
          class="preset-btn"
          :class="{ 'is-active': activePreset === idx }"
          :aria-pressed="activePreset === idx"
          @click="setPreset(p.offset, idx)"
        >{{ p.label }}</button>
      </div>

      <div class="date-range" role="group" aria-label="날짜 범위">
        <input
          :value="from"
          type="date"
          class="krds-input small date-input"
          :max="to || undefined"
          aria-label="시작일"
          @input="onFromInput"
        />
        <span class="date-sep" aria-hidden="true">–</span>
        <input
          :value="to"
          type="date"
          class="krds-input small date-input"
          :min="from || undefined"
          aria-label="종료일"
          @input="onToInput"
        />
      </div>
    </div>

    <p v-if="error" class="date-error" role="alert">{{ error }}</p>
  </div>
</template>

<style scoped>
.date-range-filter {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.date-range-filter__row {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  flex-wrap: nowrap;
}

.toolbar-label {
  flex-shrink: 0;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  white-space: nowrap;
}

.preset-group {
  display: flex;
  flex-shrink: 0;
  gap: 0.4rem;
}

.preset-btn {
  height: 4rem;
  padding: 0 1rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.4rem;
  background: transparent;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-regular);
  white-space: nowrap;
  cursor: pointer;
  transition: border-color 0.12s, background-color 0.12s, color 0.12s;
}

.preset-btn:hover {
  border-color: var(--roady-brand-secondary);
  color: var(--roady-brand-secondary);
  background: var(--roady-brand-primary-subtle);
}

.preset-btn:focus-visible {
  outline: 2px solid var(--roady-focus-ring);
  outline-offset: 2px;
}

.preset-btn.is-active {
  border-color: var(--roady-brand-secondary);
  background: var(--roady-brand-primary-subtle);
  color: var(--roady-brand-secondary);
  font-weight: var(--krds-font-weight-bold);
}

.date-range {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  gap: 0.4rem;
}

.date-input {
  width: 15rem;
  height: 4rem;
}

.date-sep {
  flex-shrink: 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-label-small);
}

.date-error {
  margin: 0;
  font-size: var(--krds-pc-font-size-label-xsmall);
  color: var(--roady-status-danger);
}
</style>
