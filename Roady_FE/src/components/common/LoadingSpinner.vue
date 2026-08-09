<script setup lang="ts">
import { Spinner } from 'krds-vue'

interface Props {
  label?: string
  fullPage?: boolean
}

withDefaults(defineProps<Props>(), {
  label: '로딩 중',
  fullPage: false,
})
</script>

<template>
  <div class="loading-wrapper" :class="{ 'is-full-page': fullPage }" role="status">
    <Spinner :label="label" />
  </div>
</template>

<style scoped>
.loading-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem;
}

.loading-wrapper.is-full-page {
  position: fixed;
  inset: 0;
  z-index: 100;
  padding: 0;
  background: rgb(255 255 255 / 70%);
}
</style>
