import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || '')
  const ready = ref(false)

  async function init() {
    if (token.value) {
      try {
        const res = await request.get('/auth/me/')
        user.value = res
      } catch {
        logout()
      }
    }
    ready.value = true
  }

  async function login(email, password) {
    const res = await request.post('/auth/login/', { email, password }, { _skipInterceptors: true })
    localStorage.setItem('access_token', res.access)
    localStorage.setItem('refresh_token', res.refresh)
    token.value = res.access
    await fetchUser()
    return res
  }

  async function fetchUser() {
    try {
      const res = await request.get('/auth/me/')
      user.value = res
    } catch {
      logout()
    }
  }

  function logout() {
    // SECURITY: 只清 token key，保留其他用户偏好
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    token.value = ''
    user.value = null
    router.push('/login')
  }

  // 由 request.js 单飞 refresh 成功后回调，
  // 同步 Pinia 内存中的 token，避免 router guard 等拿到过期值。
  function onTokenRefreshed(access, refresh) {
    if (access) {
      token.value = access
    } else {
      token.value = ''
      user.value = null
    }
    if (refresh) {
      localStorage.setItem('refresh_token', refresh)
    }
  }

  return { user, token, ready, init, login, fetchUser, logout, onTokenRefreshed }
})
