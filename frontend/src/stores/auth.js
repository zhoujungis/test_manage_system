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
    localStorage.clear()
    token.value = ''
    user.value = null
    router.push('/login')
  }

  return { user, token, ready, init, login, fetchUser, logout }
})
