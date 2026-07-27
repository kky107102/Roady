<script setup lang="ts">
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

async function handleLogout() {
  await authStore.logout()
  await router.replace('/login')
}
</script>

<template>
  <main class="dashboard-placeholder">
    <div>
      <p>Roady 관제 시스템</p>
      <h1>로그인에 성공했습니다.</h1>
      <button type="button" @click="handleLogout">로그아웃</button>
    </div>
  </main>
</template>

<style scoped>
.dashboard-placeholder {
  min-height: 100dvh;
  display: grid;
  padding: 24px;
  color: #172235;
  background: #f4f7fa;
  place-items: center;
  text-align: center;
}

.dashboard-placeholder p {
  color: #456483;
  font-weight: 700;
}

.dashboard-placeholder button {
  margin-top: 20px;
  padding: 11px 22px;
  border: 0;
  border-radius: 6px;
  color: #fff;
  background: #1c4770;
  cursor: pointer;
}
</style>
