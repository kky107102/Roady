<script setup lang="ts">
import { ref, watch } from 'vue'
import type { DashboardFilter } from '@/stores/dashboard'
import PageFilterToolbar from '@/components/common/PageFilterToolbar.vue'
import DateRangeFilter from '@/components/common/DateRangeFilter.vue'

interface Props {
  modelValue: DashboardFilter
}

const props = defineProps<Props>()
const emit = defineEmits<{ 'update:modelValue': [DashboardFilter]; apply: [DashboardFilter] }>()

const local = ref<DashboardFilter>({ ...props.modelValue })
const localPreset = ref<number | null>(null)

watch(
  () => props.modelValue,
  (val) => {
    local.value = { ...val }
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
}

function updateTo(val: string) {
  local.value = { ...local.value, to: val }
}

function handlePresetApply({ from, to }: { from: string; to: string }) {
  emit('update:modelValue', { ...local.value, from, to })
  emit('apply', { ...local.value, from, to })
}

function handleApply() {
  emit('update:modelValue', { ...local.value })
  emit('apply', { ...local.value })
}

function handleReset() {
  local.value = { from: '', to: '', regionCode: '' }
  localPreset.value = null
  emit('update:modelValue', { ...local.value })
  emit('apply', { ...local.value })
}
</script>

<template>
  <PageFilterToolbar aria-label="대시보드 조회 조건">
    <DateRangeFilter
      :from="local.from"
      :to="local.to"
      :active-preset="localPreset"
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
      <button type="button" class="krds-btn small secondary" @click="handleReset">초기화</button>
      <button type="button" class="krds-btn small filled primary apply-btn" @click="handleApply">
        조회
      </button>
    </template>
  </PageFilterToolbar>
</template>

<style scoped>
.apply-btn {
  min-width: 6.4rem;
}
</style>
