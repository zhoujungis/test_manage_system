import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  // C10 fix: sessionStorage 优先；旧版本可能还有 localStorage 残留，作 fallback
  const token = ref(sessionStorage.getItem('access_token') || localStorage.getItem('access_token') || '')
  const ready = ref(false)

  // C18 fix: 暴露 resetReady() 让 request.js 的 doRefresh 失败回调可以重置
  // router/index.js 里模块级 authReady 变量，否则登出后路由守卫不再重新 init。
  function resetReady() { ready.value = false }

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
    sessionStorage.setItem('access_token', res.access)
    sessionStorage.setItem('refresh_token', res.refresh)
    // 兼容老路径
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
    // SECURITY: 清 token；同时把 ready 置 false 让路由守卫下次重新 init
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    token.value = ''
    user.value = null
    ready.value = false
    router.push('/login')
  }

  // 由 request.js 单飞 refresh 成功后回调，
  // 同步 Pinia 内存中的 token，避免 router guard 等拿到过期值。
  function onTokenRefreshed(access, refresh) {
    if (access) {
      token.value = access
      sessionStorage.setItem('access_token', access)
      localStorage.setItem('access_token', access)
    } else {
      token.value = ''
      user.value = null
    }
    if (refresh) {
      sessionStorage.setItem('refresh_token', refresh)
      localStorage.setItem('refresh_token', refresh)
    }
  }

  return { user, token, ready, init, login, fetchUser, logout, onTokenRefreshed, resetReady }
})
