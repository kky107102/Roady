<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const pageTitle = computed(() => {
  const matched = [...route.matched].reverse()
  const record = matched.find((r) => r.meta.title)
  return (record?.meta.title as string) ?? 'Roady'
})

const assignedRegionName = computed(() => auth.user?.assignedRegionName?.trim() || '')
</script>

<template>
  <header class="app-header">
    <h1 class="page-title">{{ pageTitle }}</h1>
    <div class="assigned-region" :class="{ 'is-empty': !assignedRegionName }" role="status">
      <svg
        class="assigned-region__icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
        <circle cx="12" cy="10" r="2.5" />
      </svg>
      <span class="assigned-region__name">{{ assignedRegionName || '미지정' }}</span>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  padding: 0 3.2rem;
  height: 6rem;
  background: var(--roady-surface-default);
  border-bottom: 0.1rem solid var(--roady-border-default);
  flex-shrink: 0;
  justify-content: space-between;
}

.assigned-region {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
  min-width: 0;
  min-height: 3.6rem;
  padding: 0.5rem 1.1rem;
  border: 0.1rem solid var(--roady-border-default);
  border-radius: 0.6rem;
  color: var(--roady-text-secondary);
  background: var(--roady-surface-default);
  font-size: var(--krds-pc-font-size-label-small);
}

.assigned-region__icon {
  width: 2rem;
  height: 2rem;
  flex-shrink: 0;
}

.assigned-region__name {
  max-width: 20rem;
  overflow: hidden;
  font-weight: var(--krds-font-weight-regular);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.assigned-region.is-empty {
  color: var(--roady-text-tertiary);
  background: var(--roady-surface-background);
}

.page-title {
  margin: 0;
  color: var(--roady-text-primary);
  font-size: 2rem;
  font-weight: var(--krds-font-weight-bold);
  line-height: 1.4;
}

@media (max-width: 560px) {
  .app-header {
    height: 5.6rem;
    gap: 1.2rem;
    padding-inline: 1.6rem;
  }

  .page-title {
    min-width: 0;
    overflow: hidden;
    font-size: var(--krds-mobile-font-size-heading-small);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .assigned-region {
    flex-shrink: 0;
    min-height: 4rem;
  }

  .assigned-region__name {
    max-width: 8rem;
  }
}
</style>
