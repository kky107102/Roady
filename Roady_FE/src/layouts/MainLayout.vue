<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import ToastContainer from '@/components/common/ToastContainer.vue'
</script>

<template>
  <div class="main-layout">
    <a href="#main-content" class="skip-link">본문 바로가기</a>
    <AppSidebar />
    <div class="layout-body">
      <AppHeader />
      <main id="main-content" class="layout-main" tabindex="-1">
        <RouterView />
      </main>
    </div>
  </div>
  <ToastContainer />
</template>

<style scoped>
.main-layout {
  display: grid;
  grid-template-columns: 20rem 1fr;
  height: 100dvh;
  overflow: hidden;
}

.layout-body {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
  overflow: hidden;
}

.layout-main {
  overflow-y: auto;
  background: var(--roady-surface-background);
}

.layout-main:focus {
  outline: none;
}

.skip-link {
  position: absolute;
  top: -10rem;
  left: 1.6rem;
  z-index: 9999;
  padding: 0.8rem 1.6rem;
  border-radius: 0 0 0.4rem 0.4rem;
  color: var(--roady-surface-default);
  background: var(--roady-brand-primary);
  font-size: 1.4rem;
  font-weight: var(--krds-font-weight-bold);
  text-decoration: none;
  transition: top 0.15s ease;
}

.skip-link:focus {
  top: 0;
}
</style>
