<script setup lang="ts">
interface Props {
  message?: string
  retryLabel?: string
}

withDefaults(defineProps<Props>(), {
  message: '데이터를 불러오는 중 문제가 발생했습니다.',
  retryLabel: '다시 시도',
})

const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="error-state" role="alert">
    <svg
      class="error-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
    <p class="error-message">{{ message }}</p>
    <button type="button" class="krds-btn medium secondary error-retry" @click="emit('retry')">
      {{ retryLabel }}
    </button>
  </div>
</template>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.6rem;
  padding: 6rem 3.2rem;
  text-align: center;
}

.error-icon {
  width: 5.6rem;
  height: 5.6rem;
  color: var(--roady-status-danger);
}

.error-message {
  margin: 0;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-medium);
}

.error-retry {
  margin-top: 0.4rem;
}
</style>
