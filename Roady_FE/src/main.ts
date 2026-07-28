import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'krds-vue/dist/index.css'

import App from './App.vue'
import { setSessionExpiredHandler } from './api/http'
import './assets/styles/roady-krds.css'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

const authStore = useAuthStore(pinia)

setSessionExpiredHandler(() => {
  const currentRoute = router.currentRoute.value
  const redirect = currentRoute.name === 'login' ? undefined : currentRoute.fullPath

  authStore.clearSession()
  void router.replace({
    name: 'login',
    query: redirect ? { redirect } : undefined,
  })
})

await authStore.restoreSession()
await router.isReady()

app.mount('#app')
