<script setup lang="ts">
withDefaults(defineProps<{ ariaLabel?: string; compact?: boolean }>(), { compact: false })
const emit = defineEmits<{ submit: [] }>()
</script>

<template>
  <form
    class="page-filter-toolbar"
    :class="{ 'page-filter-toolbar--compact': compact }"
    role="search"
    :aria-label="ariaLabel"
    @submit.prevent="emit('submit')"
  >
    <slot />
    <div class="toolbar-actions">
      <slot name="actions" />
    </div>
  </form>
</template>

<style scoped>
.page-filter-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.6rem;
  padding: 1.2rem 3.2rem;
  background: var(--roady-surface-default);
  border-bottom: 1px solid var(--roady-border-default);
  flex-shrink: 0;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  flex-shrink: 0;
  margin-left: auto;
}

.page-filter-toolbar--compact {
  padding: 0.8rem 0 0;
  border-bottom: 0;
  background: transparent;
}

@media (max-width: 48rem) {
  .page-filter-toolbar {
    align-items: stretch;
    padding: 1.2rem 1.6rem;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
