<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import roadyLogo from '@/assets/images/roady-logo.png'
import { useAuthStore } from '@/stores/auth'
import type { ApiErrorResponse } from '@/types/auth'

const SAVED_USERNAME_KEY = 'savedUsername'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const rememberUsername = ref(false)
const isSubmitting = ref(false)
const errorMessage = ref('')

const canSubmit = computed(
  () => username.value.trim().length > 0 && password.value.length > 0 && !isSubmitting.value,
)

onMounted(() => {
  const savedUsername = localStorage.getItem(SAVED_USERNAME_KEY)

  if (savedUsername) {
    username.value = savedUsername
    rememberUsername.value = true
  }
})

async function handleSubmit() {
  if (!canSubmit.value) {
    errorMessage.value = '아이디와 비밀번호를 모두 입력해 주세요.'
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    await authStore.login({
      username: username.value.trim(),
      password: password.value,
    })

    if (rememberUsername.value) {
      localStorage.setItem(SAVED_USERNAME_KEY, username.value.trim())
    } else {
      localStorage.removeItem(SAVED_USERNAME_KEY)
    }

    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch (error) {
    if (axios.isAxiosError<ApiErrorResponse>(error)) {
      errorMessage.value =
        error.response?.data?.message ?? '로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.'
    } else {
      errorMessage.value = '로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.'
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="brand-panel" aria-label="Roady 서비스 소개">
      <div class="brand-content">
        <img class="brand-logo" :src="roadyLogo" alt="Roady" />

        <h1>도로 파손을 더 빠르고 정확하게</h1>
        <p>탐지부터 보수 완료까지 하나의 흐름으로 관리합니다.</p>
      </div>
    </section>

    <section class="form-panel">
      <div class="login-card">
        <header class="login-header">
          <span class="service-badge">관리자 서비스</span>
          <h2>로그인</h2>
          <p>관리자 계정으로 로그인해 주세요.</p>
        </header>

        <form class="login-form" novalidate @submit.prevent="handleSubmit">
          <div class="form-field">
            <label for="username">아이디 <span aria-hidden="true">*</span></label>
            <input
              id="username"
              v-model="username"
              name="username"
              type="text"
              autocomplete="username"
              placeholder="아이디를 입력해 주세요."
              :aria-invalid="Boolean(errorMessage)"
              required
            />
          </div>

          <div class="form-field">
            <label for="password">비밀번호 <span aria-hidden="true">*</span></label>
            <input
              id="password"
              v-model="password"
              name="password"
              type="password"
              autocomplete="current-password"
              placeholder="비밀번호를 입력해 주세요."
              :aria-invalid="Boolean(errorMessage)"
              required
            />
          </div>

          <label class="remember-field">
            <input v-model="rememberUsername" type="checkbox" />
            <span>아이디 저장</span>
          </label>

          <p v-if="errorMessage" class="error-message" role="alert">
            {{ errorMessage }}
          </p>

          <button class="login-button" type="submit" :disabled="!canSubmit">
            <span v-if="isSubmitting" class="spinner" aria-hidden="true"></span>
            {{ isSubmitting ? '로그인 중...' : '로그인' }}
          </button>
        </form>

        <nav class="account-links" aria-label="계정 지원">
          <button type="button" @click="errorMessage = '비밀번호 찾기 기능은 준비 중입니다.'">
            비밀번호 찾기
          </button>
          <span aria-hidden="true"></span>
          <button type="button" @click="errorMessage = '접속 문의 기능은 준비 중입니다.'">
            접속 문의
          </button>
        </nav>

        <div class="accessibility-guide">
          <strong>접근성 안내</strong>
          <p>키보드만으로 모든 로그인 기능을 이용할 수 있습니다.</p>
        </div>

        <footer>© 2026 Roady</footer>
      </div>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  height: 100dvh;
  display: grid;
  grid-template-columns: minmax(420px, 41%) 1fr;
  overflow: hidden;
  background: #f4f7fa;
}

.brand-panel {
  position: relative;
  height: 100dvh;
  overflow: hidden;
  color: #fff;
  background: #102a50 url('@/assets/images/login-background.png') center center / cover no-repeat;
}

.brand-content {
  position: relative;
  z-index: 2;
  width: min(74%, 520px);
  margin: clamp(72px, 12vh, 130px) auto 0;
}

.brand-logo {
  width: clamp(230px, 20vw, 330px);
  height: auto;
  display: block;
}

.brand-content h1 {
  margin: clamp(24px, 3.5vh, 38px) 0 12px;
  font-size: clamp(1.55rem, 2.2vw, 2.35rem);
  line-height: 1.35;
  letter-spacing: -0.04em;
}

.brand-content p {
  color: #c8d5e7;
  font-size: clamp(0.95rem, 1.1vw, 1.1rem);
}

.form-panel {
  display: grid;
  height: 100dvh;
  min-width: 0;
  padding: 24px clamp(32px, 6vw, 96px);
  overflow: hidden;
  place-items: center;
}

.login-card {
  width: min(100%, 560px);
  height: min(784px, calc(100dvh - 48px));
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: clamp(28px, 4.5vh, 64px) clamp(38px, 4.2vw, 64px);
  border: 1px solid #d6e0eb;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 12px 36px rgb(34 57 82 / 5%);
}

.service-badge {
  display: inline-flex;
  padding: 7px 18px;
  border-radius: 999px;
  color: #234d77;
  background: #edf3f8;
  font-size: 0.78rem;
  font-weight: 700;
}

.login-header h2 {
  margin: 18px 0 12px;
  color: #101827;
  font-size: 2rem;
  letter-spacing: -0.04em;
}

.login-header p {
  margin: 0;
  color: #667386;
  font-size: 0.95rem;
}

.login-form {
  margin-top: clamp(24px, 4vh, 44px);
}

.form-field + .form-field {
  margin-top: 22px;
}

.form-field label {
  display: block;
  margin-bottom: 9px;
  color: #192436;
  font-size: 0.85rem;
  font-weight: 700;
}

.form-field input {
  width: 100%;
  height: 52px;
  padding: 0 16px;
  border: 1px solid #d4deea;
  border-radius: 7px;
  outline: none;
  color: #182438;
  background: #fff;
  font: inherit;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.form-field input::placeholder {
  color: #8290a3;
}

.form-field input:focus {
  border-color: #245783;
  box-shadow: 0 0 0 3px rgb(36 87 131 / 13%);
}

.remember-field {
  width: fit-content;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 22px;
  color: #283447;
  cursor: pointer;
  font-size: 0.95rem;
}

.remember-field input {
  width: 20px;
  height: 20px;
  accent-color: #1e4a73;
}

.error-message {
  margin: 14px 0 -4px;
  color: #c53838;
  font-size: 0.85rem;
}

.login-button {
  width: 100%;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  margin-top: 30px;
  border: 0;
  border-radius: 6px;
  color: #fff;
  background: #1c4770;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  transition:
    background 0.2s,
    transform 0.1s;
}

.login-button:hover:not(:disabled) {
  background: #153a5e;
}

.login-button:active:not(:disabled) {
  transform: translateY(1px);
}

.login-button:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.spinner {
  width: 17px;
  height: 17px;
  border: 2px solid rgb(255 255 255 / 40%);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.account-links {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 16px;
}

.account-links button {
  padding: 6px 42px;
  border: 0;
  color: #173b61;
  background: transparent;
  font: inherit;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
}

.account-links span {
  width: 1px;
  height: 22px;
  background: #d8e0e9;
}

.accessibility-guide {
  margin-top: clamp(22px, 4vh, 56px);
  padding-top: clamp(16px, 2.5vh, 24px);
  border-top: 1px solid #dbe3ec;
  color: #263247;
  font-size: 0.85rem;
}

.accessibility-guide strong {
  display: block;
  margin-bottom: 10px;
}

.accessibility-guide p {
  margin: 0;
  color: #677487;
}

.login-card footer {
  margin-top: auto;
  padding-top: clamp(18px, 3.5vh, 42px);
  color: #687589;
  text-align: center;
  font-size: 0.85rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1023px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    display: none;
  }

  .form-panel {
    padding: 32px;
  }

  .login-card {
    height: min(784px, calc(100dvh - 64px));
  }
}

@media (max-width: 560px) {
  .login-page {
    height: auto;
    min-height: 100dvh;
    overflow-y: auto;
  }

  .form-panel {
    height: auto;
    min-height: 100dvh;
    padding: 0;
    overflow: visible;
    background: #fff;
  }

  .login-card {
    height: auto;
    min-height: 100dvh;
    padding: 44px 24px 28px;
    border: 0;
    border-radius: 0;
    box-shadow: none;
  }

  .account-links button {
    padding-inline: 24px;
  }
}

@media (max-height: 760px) and (min-width: 1024px) {
  .form-panel {
    padding-block: 16px;
  }

  .login-card {
    height: calc(100dvh - 32px);
    padding-block: 24px;
  }

  .login-form {
    margin-top: 20px;
  }

  .form-field + .form-field {
    margin-top: 16px;
  }

  .form-field input,
  .login-button {
    height: 48px;
  }

  .remember-field {
    margin-top: 16px;
  }

  .login-button {
    margin-top: 20px;
  }

  .accessibility-guide {
    margin-top: 18px;
    padding-top: 16px;
  }

  .login-card footer {
    padding-top: 14px;
  }
}
</style>
