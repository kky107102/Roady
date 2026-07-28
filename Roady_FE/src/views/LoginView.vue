<script setup lang="ts">
import axios from 'axios'
import { Checkbox } from 'krds-vue'
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import roadyLogo from '@/assets/images/roady-logo.png'
import KrdsTextInput from '@/components/common/KrdsTextInput.vue'
import { useAuthStore } from '@/stores/auth'
import type { ApiErrorResponse } from '@/types/auth'

interface TextInputExposed {
  focus: () => void
}

const SAVED_USERNAME_KEY = 'savedUsername'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const usernameInput = ref<TextInputExposed>()
const passwordInput = ref<TextInputExposed>()
const username = ref('')
const password = ref('')
const rememberUsername = ref(false)
const isSubmitting = ref(false)
const usernameError = ref('')
const passwordError = ref('')
const supportMessage = ref('')

onMounted(() => {
  const savedUsername = localStorage.getItem(SAVED_USERNAME_KEY)

  if (savedUsername) {
    username.value = savedUsername
    rememberUsername.value = true
  }
})

watch(username, () => {
  if (usernameError.value && username.value.trim()) {
    usernameError.value = ''
  }
})

watch(password, () => {
  if (passwordError.value && password.value) {
    passwordError.value = ''
  }
})

function validateUsername() {
  usernameError.value = username.value.trim() ? '' : '아이디를 입력해 주세요.'
  return !usernameError.value
}

function validatePassword() {
  passwordError.value = password.value ? '' : '비밀번호를 입력해 주세요.'
  return !passwordError.value
}

async function focusFirstInvalidField() {
  await nextTick()

  if (usernameError.value) {
    usernameInput.value?.focus()
    return
  }

  passwordInput.value?.focus()
}

async function handleSubmit() {
  supportMessage.value = ''

  const usernameValid = validateUsername()
  const passwordValid = validatePassword()

  if (!usernameValid || !passwordValid) {
    await focusFirstInvalidField()
    return
  }

  isSubmitting.value = true

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
    const fallbackMessage = '로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.'
    const message = axios.isAxiosError<ApiErrorResponse>(error)
      ? (error.response?.data?.message ?? fallbackMessage)
      : fallbackMessage

    password.value = ''
    passwordError.value = ''
    usernameError.value = message
    await focusFirstInvalidField()
  } finally {
    isSubmitting.value = false
  }
}

function showSupportMessage(message: string) {
  supportMessage.value = message
}
</script>

<template>
  <main class="login-page">
    <section class="brand-panel" aria-label="Roady 서비스 소개">
      <div class="brand-content">
        <img class="brand-logo" :src="roadyLogo" alt="Roady" />
        <p class="brand-slogan">도로 파손을 더 빠르고 정확하게</p>
        <p class="brand-description">탐지부터 보수 완료까지 하나의 흐름으로 관리합니다.</p>
      </div>
    </section>

    <section class="form-panel" aria-labelledby="login-title">
      <div class="login-shell">
        <div class="login-card">
          <header class="login-header">
            <h1 id="login-title">로그인</h1>
            <p>Roady 관리자 계정으로 로그인해 주세요.</p>
          </header>

          <form
            class="login-form"
            novalidate
            :aria-busy="isSubmitting"
            @submit.prevent="handleSubmit"
          >
            <KrdsTextInput
              id="username"
              ref="usernameInput"
              v-model="username"
              name="username"
              label="아이디"
              autocomplete="username"
              placeholder="아이디를 입력해 주세요."
              :error="usernameError"
              :disabled="isSubmitting"
              :show-required-mark="false"
              required
              @blur="validateUsername"
            />

            <KrdsTextInput
              id="password"
              ref="passwordInput"
              v-model="password"
              name="password"
              label="비밀번호"
              type="password"
              autocomplete="current-password"
              placeholder="비밀번호를 입력해 주세요."
              :error="passwordError"
              :disabled="isSubmitting"
              :show-required-mark="false"
              required
              show-password-toggle
              @blur="validatePassword"
            />

            <Checkbox
              id="remember-username"
              v-model="rememberUsername"
              label="아이디 저장"
              size="medium"
              :disabled="isSubmitting"
            />

            <button
              class="krds-btn large primary login-button"
              type="submit"
              :disabled="isSubmitting"
            >
              <span v-if="isSubmitting" class="spinner" aria-hidden="true"></span>
              {{ isSubmitting ? '로그인 중...' : '로그인' }}
            </button>
          </form>

          <div class="account-links" role="group" aria-label="계정 지원">
            <button
              type="button"
              class="krds-btn medium text"
              @click="showSupportMessage('비밀번호 찾기 기능은 준비 중입니다.')"
            >
              비밀번호 찾기
            </button>
            <span aria-hidden="true"></span>
            <button
              type="button"
              class="krds-btn medium text"
              @click="showSupportMessage('계정·접속 문의 기능은 준비 중입니다.')"
            >
              계정·접속 문의
            </button>
          </div>

          <p v-if="supportMessage" class="support-message" role="status">
            {{ supportMessage }}
          </p>
        </div>

        <footer class="login-copyright">© 2026 Roady</footer>
      </div>
    </section>
  </main>
</template>

<style scoped>
.login-page {
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
  letter-spacing: 0;
}

.form-panel {
  position: relative;
  height: 100dvh;
  min-width: 0;
  display: grid;
  padding: 4rem;
  overflow: hidden;
  place-items: center;
}

.login-shell {
  position: relative;
  width: min(100%, 60rem);
}

.login-card {
  width: 100%;
  min-height: 59rem;
  display: flex;
  flex-direction: column;
  padding: 4.8rem 3.9rem;
  border: 0.1rem solid var(--roady-border-default);
  border-radius: 1.2rem;
  background: var(--roady-surface-default);
  box-shadow: 0 0.8rem 2.4rem rgb(17 24 39 / 6%);
}

.login-header h1 {
  margin: 0 0 0.2rem;
  color: var(--roady-text-primary);
  font-size: 3rem;
  font-weight: var(--krds-font-weight-bold);
  line-height: 1.5;
  letter-spacing: 0.1rem;
}

.login-header p {
  margin: 0;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-medium);
  line-height: 1.5;
  letter-spacing: 0;
}

.login-header,
.login-form,
.account-links,
.support-message {
  width: 100%;
  max-width: 48rem;
  margin-inline: auto;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 2.4rem;
  margin-top: 1.6rem;
}

.login-button {
  width: 100%;
  justify-content: center;
  margin-top: 0.4rem;
  letter-spacing: 0;
}

.login-form :deep(.krds-form-check.medium) {
  --krds-form-check--pc-font-size-medium: 1.5rem;
  --krds-form-check--button-margin-top: 0;
}

.login-form :deep(.krds-form-check label) {
  align-items: center;
  color: var(--roady-text-secondary);
  font-weight: var(--krds-font-weight-regular);
  line-height: 1.5;
}

.login-form :deep(.krds-form-check input[type='checkbox']:focus ~ label) {
  box-shadow: none;
  outline: none;
}

.login-form :deep(.krds-form-check input[type='checkbox']:focus-visible ~ label::before) {
  outline: 0.3rem solid var(--roady-focus-ring);
  outline-offset: 0.2rem;
}

.spinner {
  width: 1.8rem;
  height: 1.8rem;
  border: 0.2rem solid rgb(255 255 255 / 40%);
  border-top-color: var(--roady-surface-default);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.account-links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.6rem;
  margin-top: 2rem;
}

.account-links .krds-btn {
  padding-inline: 1.2rem;
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-regular);
  letter-spacing: 0;
}

.account-links > span {
  width: 0.1rem;
  height: 2rem;
  flex: 0 0 0.1rem;
  background: var(--roady-border-default);
}

.support-message {
  margin: 1.2rem 0 0;
  color: var(--roady-status-info);
  font-size: var(--krds-pc-font-size-body-small);
  line-height: 1.5;
  letter-spacing: 0;
  text-align: center;
}

.login-copyright {
  position: absolute;
  top: calc(100% + 3.2rem);
  left: 50%;
  margin: 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
  line-height: 1.5;
  letter-spacing: 0;
  text-align: center;
  transform: translateX(-50%);
  white-space: nowrap;
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
    padding: 3.2rem;
  }

  .login-shell {
    width: min(100%, 60rem);
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
    background: var(--roady-surface-default);
  }

  .login-card {
    width: 100%;
    min-height: 100dvh;
    padding: 4rem 2.4rem 2.8rem;
    border: 0;
    border-radius: 0;
    box-shadow: none;
  }
}

@media (max-height: 760px) and (min-width: 1024px) {
  .form-panel {
    padding-block: 2.4rem;
  }

  .login-shell {
    width: min(100%, 60rem);
  }

  .login-card {
    min-height: 0;
    padding: 3.2rem 4.8rem;
  }

  .login-form {
    gap: 1.2rem;
    margin-top: 1.6rem;
  }

  .account-links {
    margin-top: 0.8rem;
  }
}
</style>
