import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const request = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
})

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    if (error.response?.status === 401) {
      error.config._skipInterceptors = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !error.config._retry) {
        error.config._retry = true
        try {
          const res = await request.post('/auth/refresh/', {
            refresh: refreshToken,
          }, { _skipInterceptors: true })
          localStorage.setItem('access_token', res.access)
          if (res.refresh) {
            localStorage.setItem('refresh_token', res.refresh)
          }
          error.config.headers.Authorization = `Bearer ${res.access}`
          return request(error.config)
        } catch {
          localStorage.clear()
          router.push('/login')
        }
      } else {
        localStorage.clear()
        router.push('/login')
      }
    }
    if (!error.config?._skipInterceptors) {
      const data = error.response?.data || {}
      let msg = ''
      if (typeof data === 'string') {
        msg = data
      } else {
        msg = data.detail || data.message || data.error || ''
        if (!msg) {
          const extract = (v) => {
            if (typeof v === 'string' && v) return [v]
            if (Array.isArray(v)) return v.flatMap(extract)
            if (v && typeof v === 'object') return Object.values(v).flatMap(extract)
            return []
          }
          const found = extract(data)
          msg = found[0] || ''
        }
      }
      if (!msg) msg = '请求失败'
      ElMessage({ message: msg, type: 'error' })
    }
    return Promise.reject(error)
  }
)

export default request
