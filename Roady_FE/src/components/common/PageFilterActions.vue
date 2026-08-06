<script setup lang="ts">
withDefaults(
  defineProps<{
    resetLabel?: string
    submitLabel?: string
    busy?: boolean
  }>(),
  {
    resetLabel: '초기화',
    submitLabel: '조회',
    busy: false,
  },
)

defineEmits<{ reset: [] }>()
</script>

<template>
  <button
    type="button"
    class="krds-btn small secondary"
    :disabled="busy"
    @click="$emit('reset')"
  >
    {{ resetLabel }}
  </button>
  <button
    type="submit"
    class="krds-btn small filled primary"
    :disabled="busy"
    :aria-busy="busy || undefined"
  >
    {{ submitLabel }}
  </button>
</template>
