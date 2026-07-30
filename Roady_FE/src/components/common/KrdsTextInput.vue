<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  id: string
  name: string
  label: string
  modelValue: string
  type?: 'text' | 'password'
  size?: 'small' | 'medium' | 'large'
  autocomplete?: string
  placeholder?: string
  hint?: string
  error?: string
  required?: boolean
  showRequiredMark?: boolean
  disabled?: boolean
  showPasswordToggle?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  size: 'large',
  autocomplete: 'off',
  placeholder: '',
  hint: '',
  error: '',
  required: false,
  showRequiredMark: true,
  disabled: false,
  showPasswordToggle: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  blur: []
}>()

const inputRef = ref<HTMLInputElement>()
const passwordVisible = ref(false)

const inputType = computed(() =>
  props.type === 'password' && passwordVisible.value ? 'text' : props.type,
)
const hintId = computed(() => `${props.id}-hint`)
const errorId = computed(() => `${props.id}-error`)
const describedBy = computed(() => {
  if (props.error) {
    return errorId.value
  }

  return props.hint ? hintId.value : undefined
})

function handleInput(event: Event) {
  emit('update:modelValue', (event.target as HTMLInputElement).value)
}

function togglePasswordVisibility() {
  passwordVisible.value = !passwordVisible.value
  inputRef.value?.focus()
}

defineExpose({
  focus: () => inputRef.value?.focus(),
})
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

    <div class="form-conts" :class="{ 'password-input-wrap': showPasswordToggle }">
      <input
        :id="id"
        ref="inputRef"
        :name="name"
        :value="modelValue"
        :type="inputType"
        :class="['krds-input', size]"
        :autocomplete="autocomplete"
        :placeholder="placeholder"
        :required="required"
        :disabled="disabled"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describedBy"
        @input="handleInput"
        @blur="emit('blur')"
      />

      <button
        v-if="showPasswordToggle"
        type="button"
        class="password-toggle"
        :aria-controls="id"
        :aria-pressed="passwordVisible"
        :aria-label="passwordVisible ? '비밀번호 숨기기' : '비밀번호 표시'"
        @click="togglePasswordVisibility"
      >
        <svg
          v-if="passwordVisible"
          class="password-toggle-icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path d="M3 3 21 21" />
          <path d="M10.6 6.2A10.7 10.7 0 0 1 12 6c6.5 0 10 6 10 6a18 18 0 0 1-2.1 2.8" />
          <path d="M6.6 6.6C3.6 8.4 2 12 2 12s3.5 6 10 6c1.8 0 3.3-.4 4.6-1" />
          <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
        </svg>
        <svg v-else class="password-toggle-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      </button>
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

.krds-input::placeholder {
  color: var(--roady-text-tertiary);
  opacity: 1;
}

.krds-input:focus-visible {
  border-color: var(--roady-brand-primary);
  outline: 0.3rem solid var(--roady-focus-ring);
  outline-offset: 0.1rem;
}

.password-input-wrap {
  position: relative;
}

.password-input-wrap .krds-input {
  padding-right: 5.6rem;
}

.password-toggle {
  position: absolute;
  top: 50%;
  right: 0.8rem;
  width: 4rem;
  height: 4rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: 50%;
  color: var(--roady-text-secondary);
  background: transparent;
  cursor: pointer;
  letter-spacing: 0;
  transform: translateY(-50%);
  transition:
    color 0.15s ease,
    background-color 0.15s ease;
}

.password-toggle:hover {
  color: var(--roady-text-primary);
  background: var(--roady-surface-subtle);
}

.password-toggle:focus-visible {
  color: var(--roady-text-primary);
  outline: 0.3rem solid var(--roady-focus-ring);
  outline-offset: 0;
}

.password-toggle-icon {
  width: 2.4rem;
  height: 2.4rem;
  fill: none;
  stroke: currentcolor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
</style>
