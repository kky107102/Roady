<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import roadyLogo from '@/assets/images/roady-logo.png'
import { navGroups, roleLabels } from '@/config/navigation'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const user = computed(() => authStore.user)

const userRoleLabel = computed(() => (user.value ? roleLabels[user.value.role] : ''))

const userProfileLabel = computed(() => {
  if (!user.value) return '프로필'
  return `${user.value.username} · ${userRoleLabel.value}`
})

const canOpenSettings = computed(() => user.value?.role === 'ADMIN')

const userInitials = computed(() => {
  if (!user.value) return ''
  return user.value.username.slice(0, 2).toUpperCase()
})

const visibleGroups = computed(() =>
  navGroups
    .map((group) => ({
      ...group,
      items: group.items.filter(
        (item) => !item.roles || (user.value && item.roles.includes(user.value.role)),
      ),
    }))
    .filter((group) => group.items.length > 0),
)

function isActive(routeName: string) {
  return route.name === routeName
}

async function handleLogout() {
  await authStore.logout()
  await router.replace({ name: 'login' })
}
</script>

<template>
  <aside class="app-sidebar" aria-label="Roady 관제 시스템 탐색">
    <!-- Brand -->
    <div class="sidebar-brand">
      <img :src="roadyLogo" alt="Roady" class="brand-logo" />
      <span class="brand-subtitle">통합 관제 시스템</span>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav" aria-label="주요 메뉴">
      <template v-for="(group, index) in visibleGroups" :key="group.label">
        <div v-if="index > 0" class="nav-divider" role="separator" />
        <p class="nav-group-label">{{ group.label }}</p>
        <ul class="nav-list" role="list">
          <li v-for="item in group.items" :key="item.key">
            <RouterLink
              :to="{ name: item.routeName }"
              class="nav-link"
              :class="{ 'is-active': isActive(item.routeName) }"
              :aria-current="isActive(item.routeName) ? 'page' : undefined"
            >
              <!-- Icons -->
              <span class="nav-icon" aria-hidden="true">
                <!-- 대시보드: grid squares -->
                <svg
                  v-if="item.key === 'dashboard'"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <rect x="3" y="3" width="7" height="7" rx="1" />
                  <rect x="14" y="3" width="7" height="7" rx="1" />
                  <rect x="3" y="14" width="7" height="7" rx="1" />
                  <rect x="14" y="14" width="7" height="7" rx="1" />
                </svg>
                <!-- 탐지 검토: alert triangle -->
                <svg
                  v-else-if="item.key === 'damages'"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path
                    d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
                  />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <!-- 로디 운행: truck -->
                <svg
                  v-else-if="item.key === 'robots'"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <rect x="1" y="3" width="15" height="13" rx="1" />
                  <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
                  <circle cx="5.5" cy="18.5" r="2.5" />
                  <circle cx="18.5" cy="18.5" r="2.5" />
                </svg>
                <!-- 보수 관리: clipboard list -->
                <svg
                  v-else-if="item.key === 'repairs'"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="9" y1="13" x2="15" y2="13" />
                  <line x1="9" y1="17" x2="15" y2="17" />
                </svg>
              </span>
              <span class="nav-label">{{ item.label }}</span>
            </RouterLink>
          </li>
        </ul>
      </template>
    </nav>

    <!-- Sidebar footer actions -->
    <div class="sidebar-footer" aria-label="사용자 메뉴">
      <div class="profile-icon" role="img" :aria-label="userProfileLabel" :title="userProfileLabel">
        {{ userInitials }}
      </div>

      <RouterLink
        v-if="canOpenSettings"
        :to="{ name: 'admin-users' }"
        class="footer-action"
        :class="{ 'is-active': isActive('admin-users') }"
        aria-label="설정 관리"
        title="설정 관리"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="3" />
          <path
            d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"
          />
        </svg>
      </RouterLink>

      <button
        type="button"
        class="footer-action"
        aria-label="로그아웃"
        title="로그아웃"
        @click="handleLogout"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  display: grid;
  grid-template-rows: auto 1fr auto;
  height: 100dvh;
  overflow: hidden;
  background: var(--roady-brand-primary);
  color: var(--roady-surface-default);
}

/* ── Brand ── */
.sidebar-brand {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 2.4rem 2rem 2rem;
  border-bottom: 0.1rem solid rgb(255 255 255 / 10%);
}

.brand-logo {
  width: min(100%, 9.6rem);
  height: auto;
  display: block;
}

.brand-subtitle {
  font-size: var(--krds-pc-font-size-body-small);
  color: rgb(255 255 255 / 50%);
  letter-spacing: 0.04em;
}

/* ── Nav ── */
.sidebar-nav {
  padding: 1.6rem 1.2rem;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-group-label {
  margin: 0 0 0.8rem;
  padding: 0 0.8rem;
  font-size: 1rem;
  font-weight: var(--krds-font-weight-bold);
  letter-spacing: 0.08em;
  color: rgb(255 255 255 / 36%);
  text-transform: uppercase;
}

.nav-divider {
  height: 0.1rem;
  margin: 0.8rem 0 1.6rem;
  background: rgb(255 255 255 / 10%);
}

.nav-list {
  list-style: none;
  margin: 0 0 0.4rem;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.2rem;
  border-radius: 0.8rem;
  color: rgb(255 255 255 / 65%);
  text-decoration: none;
  font-size: var(--krds-pc-font-size-body-medium);
  font-weight: var(--krds-font-weight-regular);
  transition:
    background-color 0.15s ease,
    color 0.15s ease;
}

.nav-link:hover {
  background: rgb(255 255 255 / 8%);
  color: var(--roady-surface-default);
}

.nav-link.is-active {
  background: var(--roady-brand-secondary);
  color: var(--roady-surface-default);
  font-weight: var(--krds-font-weight-bold);
}

.nav-link:focus-visible {
  outline: 0.2rem solid rgb(255 255 255 / 55%);
  outline-offset: 0.1rem;
  color: var(--roady-surface-default);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
}

.nav-icon svg {
  width: 100%;
  height: 100%;
}

.nav-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* ── Footer actions ── */
.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 1.6rem;
  border-top: 0.1rem solid rgb(255 255 255 / 10%);
}

.profile-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3.6rem;
  height: 3.6rem;
  border-radius: 50%;
  background: var(--roady-brand-secondary);
  color: var(--roady-surface-default);
  font-size: 1.3rem;
  font-weight: var(--krds-font-weight-bold);
  letter-spacing: 0;
}

.footer-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3.6rem;
  height: 3.6rem;
  padding: 0;
  border: 0;
  border-radius: 50%;
  color: rgb(255 255 255 / 50%);
  background: transparent;
  cursor: pointer;
  text-decoration: none;
  transition:
    background-color 0.15s ease,
    color 0.15s ease;
}

.footer-action:hover,
.footer-action.is-active {
  background: rgb(255 255 255 / 8%);
  color: var(--roady-surface-default);
}

.footer-action:focus-visible {
  outline: 0.2rem solid rgb(255 255 255 / 55%);
  outline-offset: 0.1rem;
  color: var(--roady-surface-default);
}

.footer-action svg {
  width: 1.8rem;
  height: 1.8rem;
}
</style>
