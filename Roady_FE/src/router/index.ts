import { createRouter, createWebHistory } from 'vue-router'

import type { UserRole } from '@/types/auth'
import { tokenStorage } from '@/utils/tokenStorage'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    guestOnly?: boolean
    title?: string
    roles?: UserRole[]
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { title: '대시보드 종합 현황' },
        },
        {
          path: 'damages',
          name: 'damages',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: '탐지·사건 관리' },
        },
        {
          path: 'robots',
          name: 'robots',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: '로디 운행' },
        },
        {
          path: 'repairs',
          name: 'repairs',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: '보수 요청 이력' },
        },
        {
          path: 'admin/users',
          name: 'admin-users',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: '설정 관리', roles: ['ADMIN'] },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to) => {
  const hasSession = tokenStorage.hasSession()
  const requiresAuth = to.matched.some((r) => r.meta.requiresAuth)
  const guestOnly = to.matched.some((r) => r.meta.guestOnly)

  if (requiresAuth && !hasSession) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (guestOnly && hasSession) {
    return { name: 'dashboard' }
  }
})

export default router
