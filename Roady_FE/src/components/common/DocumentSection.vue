<script setup lang="ts">
import { useId } from 'vue'

const props = defineProps<{
  title: string
}>()

const titleId = `document-section-${useId()}`
</script>

<template>
  <section class="document-section" :aria-labelledby="titleId">
    <h3 :id="titleId" class="document-section__title">{{ props.title }}</h3>
    <div class="document-section__content">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.document-section {
  display: flex;
  flex-direction: column;
  gap: var(--krds-number-6);
  padding-top: var(--krds-number-8);
  border-top: var(--krds-number-1) solid var(--roady-border-default);
}

.document-section:first-child {
  padding-top: 0;
  border-top: 0;
}

.document-section__title {
  margin: 0;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-heading-xsmall);
  font-weight: var(--krds-font-weight-bold);
  line-height: 1.4;
}

.document-section__content {
  min-width: 0;
}
</style>
