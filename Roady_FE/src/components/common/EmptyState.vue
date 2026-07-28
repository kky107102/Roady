<script setup lang="ts">
interface Props {
  title?: string
  description?: string
}

withDefaults(defineProps<Props>(), {
  title: '데이터가 없습니다.',
  description: '',
})
</script>

<template>
  <div class="empty-state" role="status">
    <svg
      class="empty-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      <line x1="9" y1="10" x2="15" y2="10" />
    </svg>
    <p class="empty-title">{{ title }}</p>
    <p v-if="description" class="empty-desc">{{ description }}</p>
    <slot />
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.2rem;
  padding: 6rem 3.2rem;
  text-align: center;
}

.empty-icon {
  width: 5.6rem;
  height: 5.6rem;
  color: var(--roady-border-default);
}

.empty-title {
  margin: 0;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-medium);
  font-weight: var(--krds-font-weight-bold);
}

.empty-desc {
  margin: 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
  line-height: 1.6;
}
</style>
