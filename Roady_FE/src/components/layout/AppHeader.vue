<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const pageTitle = computed(() => {
  const matched = [...route.matched].reverse()
  const record = matched.find((r) => r.meta.title)
  return (record?.meta.title as string) ?? 'Roady'
})
</script>

<template>
  <header class="app-header">
    <h1 class="page-title">{{ pageTitle }}</h1>
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
}

.page-title {
  margin: 0;
  color: var(--roady-text-primary);
  font-size: 2rem;
  font-weight: var(--krds-font-weight-bold);
  line-height: 1.4;
}
</style>
