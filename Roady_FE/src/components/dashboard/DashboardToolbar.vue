<script setup lang="ts">
import { ref, watch } from 'vue'
import KrdsSelect from '@/components/common/KrdsSelect.vue'
import type { SelectOption } from '@/components/common/KrdsSelect.vue'
import type { DashboardFilter } from '@/stores/dashboard'

interface Props {
  modelValue: DashboardFilter
}

const props = defineProps<Props>()
const emit = defineEmits<{ 'update:modelValue': [DashboardFilter]; apply: [DashboardFilter] }>()

const local = ref<DashboardFilter>({ ...props.modelValue })

watch(
  () => props.modelValue,
  (val) => { local.value = { ...val } },
)

const PRESETS = [
  { label: '오늘', offset: 0 },
  { label: '7일', offset: 6 },
  { label: '30일', offset: 29 },
]

function toDateString(date: Date): string {
  return date.toISOString().slice(0, 10)
}

function setPreset(offset: number) {
  const to = new Date()
  const from = new Date()
  from.setDate(from.getDate() - offset)
  local.value.from = toDateString(from)
  local.value.to = toDateString(to)
  emit('update:modelValue', { ...local.value })
  emit('apply', { ...local.value })
}

const regionOptions: SelectOption[] = [
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

function handleApply() {
  emit('update:modelValue', { ...local.value })
  emit('apply', { ...local.value })
}
</script>

<template>
  <div class="dashboard-toolbar" role="search" aria-label="대시보드 조회 조건">
    <div class="toolbar-group">
      <label class="toolbar-label" for="filter-from">기간</label>
      <div class="date-presets" role="group" aria-label="기간 단축 선택">
        <button
          v-for="preset in PRESETS"
          :key="preset.label"
          type="button"
          class="preset-btn"
          @click="setPreset(preset.offset)"
        >
          {{ preset.label }}
        </button>
      </div>
      <div class="date-range">
        <input
          id="filter-from"
          v-model="local.from"
          type="date"
          class="krds-input small date-input"
          :max="local.to"
          aria-label="조회 시작일"
        />
        <span class="date-sep" aria-hidden="true">~</span>
        <input
          v-model="local.to"
          type="date"
          class="krds-input small date-input"
          :min="local.from"
          aria-label="조회 종료일"
        />
      </div>
    </div>

    <div class="toolbar-group">
      <label class="toolbar-label" for="filter-region">지역</label>
      <KrdsSelect
        id="filter-region"
        name="filter-region"
        label=""
        v-model="local.regionCode"
        :options="regionOptions"
        style="min-width: 16rem;"
      />
    </div>

    <button type="button" class="krds-btn small filled primary" @click="handleApply">
      조회
    </button>
  </div>
</template>

<style scoped>
.dashboard-toolbar {
  display: flex;
  align-items: center;
  gap: 1.6rem;
  flex-wrap: wrap;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.toolbar-label {
  flex-shrink: 0;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  white-space: nowrap;
}

/* ── 기간 단축 버튼 ── */
.date-presets {
  display: flex;
  gap: 0.4rem;
}

.preset-btn {
  padding: 0.4rem 1rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.4rem;
  background: transparent;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-label-small);
  white-space: nowrap;
  cursor: pointer;
  transition: border-color 0.15s, background-color 0.15s, color 0.15s;
}

.preset-btn:hover {
  border-color: var(--roady-brand-secondary);
  color: var(--roady-brand-secondary);
  background: color-mix(in srgb, var(--roady-brand-secondary) 6%, transparent);
}

.preset-btn:focus-visible {
  outline: 2px solid var(--roady-focus-ring, var(--roady-brand-secondary));
  outline-offset: 2px;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.date-input {
  width: 14rem;
}

.date-sep {
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
}

/* KrdsSelect label 숨김 처리 - label prop이 빈 문자열일 때 */
:deep(.form-tit) {
  display: none;
}

:deep(.krds-form-select) {
  height: 3.6rem;
}
</style>
