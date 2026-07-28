<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => (route.meta.title as string) || '준비 중')
</script>

<template>
  <div class="placeholder-view">
    <div class="placeholder-content">
      <svg
        class="placeholder-icon"
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
      <p class="placeholder-title">{{ title }}</p>
      <p class="placeholder-desc">해당 화면은 현재 개발 중입니다.</p>
    </div>
  </div>
</template>

<style scoped>
.placeholder-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 40rem;
  padding: 3.2rem;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.2rem;
  text-align: center;
}

.placeholder-icon {
  width: 4.8rem;
  height: 4.8rem;
  color: var(--roady-border-default);
}

.placeholder-title {
  margin: 0;
  color: var(--roady-text-primary);
  font-size: 1.8rem;
  font-weight: var(--krds-font-weight-bold);
}

.placeholder-desc {
  margin: 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-medium);
}
</style>
