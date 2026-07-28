<script setup lang="ts">
import roadyLogo from '@/assets/images/roady-logo.png'

interface Props {
  contentLabelledby: string
}

defineProps<Props>()
</script>

<template>
  <main class="auth-layout">
    <section class="brand-panel" aria-label="Roady 서비스 소개">
      <div class="brand-content">
        <img class="brand-logo" :src="roadyLogo" alt="Roady" />
        <p class="brand-slogan">도로 파손을 더 빠르고 정확하게</p>
        <p class="brand-description">탐지부터 보수 완료까지 하나의 흐름으로 관리합니다.</p>
      </div>
    </section>

    <section class="content-panel" :aria-labelledby="contentLabelledby">
      <div class="content-shell">
        <slot />
        <footer class="copyright">© 2026 Roady</footer>
      </div>
    </section>
  </main>
</template>

<style scoped>
.auth-layout {
  height: 100dvh;
  display: grid;
  grid-template-columns: 42% minmax(0, 58%);
  overflow: hidden;
  background: var(--roady-surface-background);
}

.brand-panel {
  position: relative;
  height: 100dvh;
  overflow: hidden;
  color: var(--roady-surface-default);
  background: var(--roady-brand-primary) url('@/assets/images/login-background.png') center 58% /
    cover no-repeat;
}

.brand-panel::after {
  position: absolute;
  z-index: 1;
  inset: 0;
  background:
    radial-gradient(
      circle at 15% 69%,
      rgb(22 58 95 / 96%) 0,
      rgb(22 58 95 / 88%) 5rem,
      rgb(22 58 95 / 42%) 9rem,
      transparent 15rem
    ),
    radial-gradient(
      circle at 8% 84%,
      rgb(22 58 95 / 72%) 0,
      rgb(22 58 95 / 44%) 30%,
      transparent 56%
    );
  content: '';
  pointer-events: none;
}

.brand-content {
  position: relative;
  z-index: 2;
  width: min(76%, 56rem);
  margin: clamp(8rem, 11vh, 11rem) auto 0;
}

.brand-logo {
  width: min(100%, 27.5rem);
  height: auto;
  display: block;
  filter: drop-shadow(0 0.8rem 2.4rem rgb(3 11 18 / 24%));
}

.brand-slogan {
  max-width: 48rem;
  margin: clamp(3.2rem, 4vh, 3.6rem) 0 1rem;
  font-size: clamp(2.4rem, 1.8vw, 2.8rem);
  font-weight: var(--krds-font-weight-bold);
  line-height: 1.5;
  letter-spacing: 0.1rem;
}

.brand-description {
  max-width: 52rem;
  margin: 0;
  color: var(--roady-surface-subtle);
  font-size: var(--krds-pc-font-size-body-medium);
  line-height: 1.5;
}

.content-panel {
  height: 100dvh;
  min-width: 0;
  display: grid;
  padding: 4rem;
  overflow: hidden;
  place-items: center;
}

.content-shell {
  position: relative;
  width: min(100%, 60rem);
}

.copyright {
  position: absolute;
  top: calc(100% + 3.2rem);
  left: 50%;
  margin: 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
  line-height: 1.5;
  transform: translateX(-50%);
  white-space: nowrap;
}

@media (max-width: 1023px) {
  .auth-layout {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    display: none;
  }

  .content-panel {
    padding: 3.2rem;
  }
}

@media (max-width: 560px) {
  .auth-layout {
    height: auto;
    min-height: 100dvh;
    overflow-y: auto;
  }

  .content-panel {
    height: auto;
    min-height: 100dvh;
    padding: 0;
    overflow: visible;
    background: var(--roady-surface-default);
  }
}

@media (max-height: 760px) and (min-width: 1024px) {
  .content-panel {
    padding-block: 2.4rem;
  }
}
</style>
