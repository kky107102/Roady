<script setup lang="ts">
import { computed } from 'vue'

export interface SelectOption {
  value: string
  label: string
}

interface Props {
  id: string
  name: string
  label: string
  modelValue: string
  options: SelectOption[]
  placeholder?: string
  hint?: string
  error?: string
  required?: boolean
  showRequiredMark?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '',
  hint: '',
  error: '',
  required: false,
  showRequiredMark: true,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  change: [value: string]
}>()

const hintId = computed(() => `${props.id}-hint`)
const errorId = computed(() => `${props.id}-error`)
const describedBy = computed(() => {
  if (props.error) return errorId.value
  return props.hint ? hintId.value : undefined
})

function handleChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<template>
  <div class="form-group" :class="{ 'is-error': error }">
    <div class="form-tit">
      <label :for="id">
        {{ label }}
        <span v-if="required && showRequiredMark" class="required-mark" aria-hidden="true">*</span>
        <span v-if="required" class="sr-only"> 필수 입력 </span>
      </label>
    </div>

    <div class="form-conts">
      <select
        :id="id"
        :name="name"
        :value="modelValue"
        class="krds-form-select large"
        :class="{ 'is-error': error }"
        :required="required"
        :disabled="disabled"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describedBy"
        @change="handleChange"
      >
        <option v-if="placeholder" value="" disabled :selected="!modelValue">
          {{ placeholder }}
        </option>
        <option v-for="opt in options" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <p v-if="error" :id="errorId" class="form-hint-invalid" role="alert">
      {{ error }}
    </p>
    <p v-else-if="hint" :id="hintId" class="form-hint">
      {{ hint }}
    </p>
  </div>
</template>

<style scoped>
.form-tit label {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  line-height: 1.5;
  letter-spacing: 0;
}

.required-mark {
  margin-left: 0.4rem;
  color: var(--roady-status-danger);
}

.form-hint,
.form-hint-invalid {
  line-height: 1.5;
  letter-spacing: 0;
}

.krds-form-select:focus-visible {
  border-color: var(--roady-brand-primary);
  outline: 0.3rem solid var(--roady-focus-ring);
  outline-offset: 0.1rem;
}
</style>
