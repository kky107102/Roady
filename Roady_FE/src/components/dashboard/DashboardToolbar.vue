<script setup lang="ts">
import { ref, watch } from 'vue'
import type { DashboardFilter } from '@/stores/dashboard'

interface Props {
  modelValue: DashboardFilter
}

const props = defineProps<Props>()
const emit = defineEmits<{ 'update:modelValue': [DashboardFilter]; apply: [DashboardFilter] }>()

const local = ref<DashboardFilter>({ ...props.modelValue })
const activePreset = ref<number | null>(null)

watch(
  () => props.modelValue,
  (val) => { local.value = { ...val } },
)

const PRESETS: { label: string; offset: number }[] = [
  { label: '오늘', offset: 0 },
  { label: '7일', offset: 6 },
  { label: '30일', offset: 29 },
]

function toDateString(date: Date): string {
  return date.toISOString().slice(0, 10)
}

function setPreset(offset: number, index: number) {
  const to = new Date()
  const from = new Date()
  from.setDate(from.getDate() - offset)
  local.value = { ...local.value, from: toDateString(from), to: toDateString(to) }
  activePreset.value = index
  emit('update:modelValue', { ...local.value })
  emit('apply', { ...local.value })
}

function onDateInput() {
  activePreset.value = null
}

function handleApply() {
  emit('update:modelValue', { ...local.value })
  emit('apply', { ...local.value })
}

const regionOptions = [
  { value: '', label: '전체 지역' },
  { value: '11', label: '서울특별시' },
  { value: '21', label: '부산광역시' },
  { value: '22', label: '대구광역시' },
  { value: '23', label: '인천광역시' },
  { value: '24', label: '광주광역시' },
  { value: '25', label: '대전광역시' },
  { value: '26', label: '울산광역시' },
  { value: '29', label: '세종특별자치시' },
  { value: '31', label: '경기도' },
  { value: '32', label: '강원특별자치도' },
  { value: '33', label: '충청북도' },
  { value: '34', label: '충청남도' },
  { value: '35', label: '전라북도' },
  { value: '36', label: '전라남도' },
  { value: '37', label: '경상북도' },
  { value: '38', label: '경상남도' },
  { value: '39', label: '제주특별자치도' },
]
</script>

<template>
  <div class="dashboard-toolbar" role="search" aria-label="대시보드 조회 조건">

    <!-- 기간 그룹 -->
    <div class="toolbar-group">
      <span id="period-label" class="toolbar-label">기간</span>

      <div class="preset-group" role="group" aria-labelledby="period-label">
        <button
          v-for="(preset, idx) in PRESETS"
          :key="preset.label"
          type="button"
          class="preset-btn"
          :class="{ 'is-active': activePreset === idx }"
          :aria-pressed="activePreset === idx"
          @click="setPreset(preset.offset, idx)"
        >
          {{ preset.label }}
        </button>
      </div>

      <div class="date-range" role="group" aria-label="조회 날짜 범위">
        <input
          id="filter-from"
          v-model="local.from"
          type="date"
          class="krds-input small date-input"
          :max="local.to"
          aria-label="조회 시작일"
          @input="onDateInput"
        />
        <span class="date-sep" aria-hidden="true">–</span>
        <input
          v-model="local.to"
          type="date"
          class="krds-input small date-input"
          :min="local.from"
          aria-label="조회 종료일"
          @input="onDateInput"
        />
      </div>
    </div>

    <!-- 지역 그룹 (API 미지원) -->
    <div class="toolbar-group">
      <span id="region-label" class="toolbar-label">지역</span>

      <select
        id="filter-region"
        v-model="local.regionCode"
        class="krds-form-select small region-select"
        aria-labelledby="region-label"
        disabled
        title="지역 필터는 현재 준비 중입니다"
      >
        <option v-for="opt in regionOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <span class="coming-soon" aria-label="지역 필터 준비 중">준비 중</span>
    </div>

    <!-- 조회 -->
    <button type="button" class="krds-btn small filled primary apply-btn" @click="handleApply">
      조회
    </button>

  </div>
</template>

<style scoped>
/* ── 툴바: 모든 요소 한 줄 ── */
.dashboard-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 2rem;
}

/* ── 그룹: 레이블 + 컨트롤 가로 배치 ── */
.toolbar-group {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 0.8rem;
}

.toolbar-label {
  flex-shrink: 0;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  white-space: nowrap;
}

/* ── 프리셋 버튼 ── */
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

/* ── 날짜 범위 ── */
.date-range {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  gap: 0.4rem;
}

.date-input {
  width: 16rem;
}

.date-sep {
  flex-shrink: 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-label-small);
}

/* ── 지역 셀렉트 ── */
.region-select {
  width: 17rem;
  flex-shrink: 0;
}

/* ── 준비 중 배지 ── */
.coming-soon {
  flex-shrink: 0;
  padding: 0.2rem 0.6rem;
  border-radius: 0.3rem;
  background: var(--roady-surface-subtle);
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-label-xsmall);
  font-weight: var(--krds-font-weight-bold);
  white-space: nowrap;
}

/* ── 조회 버튼 ── */
.apply-btn {
  flex-shrink: 0;
  min-width: 6.4rem;
}
</style>
