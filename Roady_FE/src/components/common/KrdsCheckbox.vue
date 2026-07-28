<script setup lang="ts">
import { Checkbox } from 'krds-vue'

interface Props {
  id: string
  label: string
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  disabled: false,
})

const model = defineModel<boolean>({ required: true })
</script>

<template>
  <Checkbox
    :id="id"
    v-model="model"
    class="roady-checkbox"
    :label="label"
    size="medium"
    :disabled="disabled"
  />
</template>

<style scoped>
.roady-checkbox {
  --krds-form-check--pc-font-size-medium: 1.5rem;
  --krds-form-check--button-margin-top: 0;
}

.roady-checkbox :deep(label) {
  align-items: center;
  color: var(--roady-text-secondary);
  font-weight: var(--krds-font-weight-regular);
  line-height: 1.5;
}

.roady-checkbox :deep(input[type='checkbox']:focus ~ label) {
  box-shadow: none;
  outline: none;
}

.roady-checkbox :deep(input[type='checkbox']:focus-visible ~ label::before) {
  outline: 0.3rem solid var(--roady-focus-ring);
  outline-offset: 0.2rem;
}
</style>
