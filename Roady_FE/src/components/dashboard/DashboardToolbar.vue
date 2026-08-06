<script setup lang="ts">
import { ref, watch } from 'vue'
import type { DashboardFilter } from '@/stores/dashboard'
import PageFilterToolbar from '@/components/common/PageFilterToolbar.vue'
import PageFilterActions from '@/components/common/PageFilterActions.vue'
import DateRangeFilter from '@/components/common/DateRangeFilter.vue'
import { dateRangeForPreset, matchingDateRangePreset, validateDateRange } from '@/utils/localDate'

interface Props {
  modelValue: DashboardFilter
  compact?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{ 'update:modelValue': [DashboardFilter]; apply: [DashboardFilter] }>()

const local = ref<DashboardFilter>({ ...props.modelValue })
const localPreset = ref<number | null>(matchingDateRangePreset(props.modelValue.from, props.modelValue.to))
const error = ref('')

watch(
  () => props.modelValue,
  (val) => {
    local.value = { ...val }
    localPreset.value = matchingDateRangePreset(val.from, val.to)
    error.value = ''
  },
)

// 지역 코드 옵션 (API 미지원, UI 숨김 상태)
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

function updateFrom(val: string) {
  local.value = { ...local.value, from: val }
  error.value = ''
}

function updateTo(val: string) {
  local.value = { ...local.value, to: val }
  error.value = ''
}

function handlePresetApply({ from, to }: { from: string; to: string }) {
  error.value = ''
  emit('update:modelValue', { ...local.value, from, to })
  emit('apply', { ...local.value, from, to })
}

function handleApply() {
  error.value = validateDateRange(local.value.from, local.value.to)
  if (error.value) return
  emit('update:modelValue', { ...local.value })
  emit('apply', { ...local.value })
}

function handleReset() {
  local.value = { ...dateRangeForPreset(1), regionCode: '' }
  localPreset.value = 1
  error.value = ''
  emit('update:modelValue', { ...local.value })
  emit('apply', { ...local.value })
}
</script>

<template>
  <PageFilterToolbar
    aria-label="대시보드 조회 조건"
    :compact="compact"
    @submit="handleApply"
  >
    <DateRangeFilter
      :from="local.from"
      :to="local.to"
      :active-preset="localPreset"
      :error="error"
      @update:from="updateFrom"
      @update:to="updateTo"
      @update:active-preset="localPreset = $event"
      @preset-apply="handlePresetApply"
    />

    <!-- 지역 필터 (API 미지원 — 데이터 바인딩 유지, UI만 숨김) -->
    <div style="display: none" aria-hidden="true">
      <select v-model="local.regionCode">
        <option v-for="opt in regionOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <template #actions>
      <PageFilterActions @reset="handleReset" />
    </template>
  </PageFilterToolbar>
</template>
