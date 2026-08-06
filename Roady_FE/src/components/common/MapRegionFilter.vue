<script setup lang="ts">
import type { MapRegionOption } from '@/types/map'

interface Props {
  id: string
  modelValue: string
  assignedRegionName?: string | null
  options?: MapRegionOption[]
  loading?: boolean
  error?: string | null
}

withDefaults(defineProps<Props>(), {
  assignedRegionName: null,
  options: () => [],
  loading: false,
  error: null,
})

const emit = defineEmits<{
  'update:modelValue': [code: string]
  retry: []
}>()

function handleChange(event: Event) {
  emit('update:modelValue', (event.target as HTMLSelectElement).value)
}
</script>

<template>
  <div class="map-region-filter" role="group" :aria-labelledby="`${id}-label`">
    <template v-if="!assignedRegionName">
      <p class="map-region-filter__message" role="status">담당 지역 미지정</p>
    </template>

    <template v-else-if="error">
      <p class="map-region-filter__message" role="alert">{{ error }}</p>
      <button type="button" class="map-region-filter__retry" @click="emit('retry')">
        다시 시도
      </button>
    </template>

    <template v-else>
      <label :id="`${id}-label`" class="map-region-filter__label" :for="id">
        지도 읍면동 선택
      </label>
      <select
        :id="id"
        class="map-region-filter__select"
        :value="modelValue"
        :disabled="loading || options.length === 0"
        :aria-busy="loading || undefined"
        @change="handleChange"
      >
        <option value="">읍면동 선택</option>
        <option v-for="option in options" :key="option.code" :value="option.code">
          {{ option.name }}
        </option>
      </select>
      <span v-if="loading" class="map-region-filter__state" role="status">불러오는 중</span>
      <span v-else-if="options.length === 0" class="map-region-filter__state" role="status">
        선택 가능한 읍면동이 없습니다.
      </span>
    </template>
  </div>
</template>

<style scoped>
.map-region-filter {
  position: absolute;
  top: 1.2rem;
  right: 1.2rem;
  z-index: var(--roady-z-map-control);
  display: flex;
  align-items: center;
  gap: 0.6rem;
  max-width: calc(100% - 3.2rem);
}

.map-region-filter__label {
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

.map-region-filter__select {
  min-width: 14rem;
  height: 3.4rem;
  padding: 0 3.8rem 0 1rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.6rem;
  color: var(--roady-text-primary);
  background: var(--roady-surface-default);
  font: inherit;
  box-shadow: 0 0.3rem 0.8rem rgb(0 0 0 / 10%);
}

.map-region-filter__select:focus-visible,
.map-region-filter__retry:focus-visible {
  border-color: var(--roady-brand-secondary);
  outline: 0.3rem solid var(--roady-focus-ring);
  outline-offset: 0.2rem;
}

.map-region-filter__select option:checked {
  color: var(--roady-surface-default);
  background: var(--roady-brand-primary);
}

.map-region-filter__select:disabled {
  color: var(--roady-text-tertiary);
  cursor: not-allowed;
}

.map-region-filter__message,
.map-region-filter__state {
  margin: 0;
  padding: 0.6rem 0.9rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.6rem;
  color: var(--roady-text-secondary);
  background: var(--roady-surface-default);
  font-size: var(--krds-pc-font-size-label-small);
  white-space: nowrap;
}

.map-region-filter__retry {
  border: 0;
  color: var(--roady-brand-secondary);
  background: transparent;
  font: inherit;
  font-weight: var(--krds-font-weight-bold);
  text-decoration: underline;
  cursor: pointer;
}

@media (max-width: 48rem) {
  .map-region-filter {
    right: 0.8rem;
    max-width: calc(100% - 1.6rem);
  }

  .map-region-filter__message,
  .map-region-filter__state {
    white-space: normal;
  }

  .map-region-filter__select {
    width: 100%;
    min-width: 0;
  }
}
</style>
