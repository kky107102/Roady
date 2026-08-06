<script setup lang="ts">
import { computed, ref } from 'vue'
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

const userInitials = computed(() => {
  if (!user.value) return ''
  return user.value.username.slice(0, 2).toUpperCase()
})

const logoutPending = ref(false)

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
  if (logoutPending.value) return
  logoutPending.value = true
  try {
    await authStore.logout()
    await router.replace({ name: 'login' })
  } finally {
    logoutPending.value = false
  }
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
              :aria-label="item.label"
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

    <!-- Sidebar profile -->
    <div class="sidebar-footer" aria-label="관리자 프로필">
      <div class="profile-summary">
        <div
          class="profile-icon"
          role="img"
          :aria-label="userProfileLabel"
          :title="userProfileLabel"
        >
          {{ userInitials }}
        </div>
        <div class="profile-details">
          <strong class="profile-name">{{ user?.username || '사용자' }}</strong>
          <span class="profile-department">{{ userRoleLabel }}</span>
        </div>
      </div>
      <button
        type="button"
        class="logout-button"
        :disabled="logoutPending"
        aria-label="로그아웃"
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
        <span class="sr-only">{{ logoutPending ? '로그아웃 중' : '로그아웃' }}</span>
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

.nav-link:focus {
  outline: none;
  box-shadow: none;
}

.nav-link:focus-visible {
  background: rgb(255 255 255 / 12%);
  color: var(--roady-surface-default);
}

.nav-link.is-active:focus-visible {
  background: var(--roady-brand-secondary);
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

/* ── Sidebar profile ── */
.sidebar-footer {
  display: flex;
  align-items: center;
  gap: var(--krds-number-6);
  padding: var(--krds-number-8);
  border-top: 0.1rem solid rgb(255 255 255 / 10%);
}

.profile-summary {
  display: flex;
  flex: 1;
  align-items: center;
  gap: var(--krds-number-6);
  min-width: 0;
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
  flex-shrink: 0;
}

.profile-details {
  display: grid;
  gap: var(--krds-number-2);
  min-width: 0;
}

.profile-name,
.profile-department {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-name {
  color: var(--roady-surface-default);
  font-size: var(--krds-pc-font-size-label-medium);
  font-weight: var(--krds-font-weight-bold);
}

.profile-department {
  color: rgb(255 255 255 / 60%);
  font-size: var(--krds-pc-font-size-label-xsmall);
}

.logout-button {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: var(--krds-number-14);
  height: var(--krds-number-14);
  padding: 0;
  border: 0;
  border-radius: var(--roady-radius-control);
  color: rgb(255 255 255 / 60%);
  background: transparent;
  font: inherit;
  cursor: pointer;
  transition:
    background-color var(--roady-transition-fast),
    color var(--roady-transition-fast);
}

.logout-button:hover:not(:disabled) {
  color: var(--roady-surface-default);
  background: rgb(255 255 255 / 10%);
}

.logout-button:focus-visible {
  outline: 0.2rem solid rgb(255 255 255 / 55%);
  outline-offset: 0.1rem;
}

.logout-button:disabled {
  opacity: 0.55;
}

.logout-button svg {
  flex-shrink: 0;
  width: var(--krds-number-9);
  height: var(--krds-number-9);
}

.sr-only {
  position: absolute;
  width: var(--krds-number-1);
  height: var(--krds-number-1);
  padding: 0;
  margin: calc(var(--krds-number-1) * -1);
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 768px) {
  .app-sidebar {
    grid-template-columns: auto minmax(0, 1fr) auto;
    grid-template-rows: auto;
    height: auto;
    min-height: 6.4rem;
  }

  .sidebar-brand {
    justify-content: center;
    padding: 1.2rem 1.6rem;
    border-right: 0.1rem solid rgb(255 255 255 / 10%);
    border-bottom: 0;
  }

  .brand-logo {
    width: 7.2rem;
  }

  .brand-subtitle,
  .nav-group-label,
  .nav-divider,
  .profile-summary {
    display: none;
  }

  .sidebar-nav {
    display: flex;
    align-items: center;
    padding: 0.8rem;
    overflow-x: auto;
    overflow-y: hidden;
  }

  .nav-group,
  .nav-list {
    width: 100%;
  }

  .nav-list {
    flex-direction: row;
    justify-content: center;
    gap: 0.4rem;
    margin: 0;
  }

  .nav-link {
    justify-content: center;
    min-height: 4.4rem;
    padding: 0.8rem 1rem;
  }

  .sidebar-footer {
    padding: 1rem 1.2rem;
    border-top: 0;
    border-left: 0.1rem solid rgb(255 255 255 / 10%);
  }

  .logout-button {
    width: var(--krds-number-15);
    height: var(--krds-number-15);
    border-radius: 50%;
  }
}

@media (max-width: 560px) {
  .sidebar-brand {
    padding-inline: 1.2rem;
  }

  .brand-logo {
    width: 6.4rem;
  }

  .nav-link {
    min-width: 4.4rem;
    padding-inline: 0.8rem;
  }

  .nav-label {
    position: absolute;
    width: 0.1rem;
    height: 0.1rem;
    overflow: hidden;
    clip: rect(0 0 0 0);
    clip-path: inset(50%);
    white-space: nowrap;
  }

  .sidebar-footer {
    padding-inline: 0.8rem;
  }
}
</style>
