import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// 主请求实例：带 Authorization header，处理 401 重试等
const request = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
})

// SECURITY (C7 fix): 独立的 refresh 客户端（不带任何拦截器），
// 避免 refresh 端点 401 时再次触发主拦截器，造成无限递归调用。
const refreshClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
})

// 单飞 refresh：并发 401 复用同一次 refresh 结果，
// 避免多个请求并发旋转 token 把有效 session 强制下线。
let inflightRefresh = null

function notifyAuthStore(access, refresh) {
  // 通知 Pinia auth store 刷新内存中的 token。
  // 用 lazy import 避免循环依赖（store 反过来也用到 request）。
  try {
    import('@/stores/auth').then(({ useAuthStore }) => {
      try {
        const store = useAuthStore()
        store.onTokenRefreshed?.(access, refresh)
      } catch {
        // store 尚未初始化时静默；后续正常调用仍能从 localStorage 读
      }
    })
  } catch {
    /* ignore */
  }
}

function doRefresh() {
  if (inflightRefresh) return inflightRefresh
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return Promise.reject(new Error('no refresh token'))
  inflightRefresh = refreshClient
    .post('/auth/refresh/', { refresh: refreshToken })
    .then((res) => {
      const data = res.data
      if (!data || !data.access) throw new Error('invalid refresh response')
      localStorage.setItem('access_token', data.access)
      if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
      notifyAuthStore(data.access, data.refresh)
      return data.access
    })
    .catch((err) => {
      // refresh 失败：清掉 token、跳登录
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      notifyAuthStore(null, null)
      router.push('/login')
      throw err
    })
    .finally(() => {
      inflightRefresh = null
    })
  return inflightRefresh
}

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
    const status = error.response?.status
    const cfg = error.config || {}

    if (status === 401 && !cfg._retried) {
      cfg._retried = true
      try {
        const newAccess = await doRefresh()
        cfg.headers = cfg.headers || {}
        cfg.headers.Authorization = `Bearer ${newAccess}`
        // 用主 request 重放原请求（自动带上新 token）
        return request(cfg)
      } catch {
        // refresh 已失败并跳转；这里直接抛错
        return Promise.reject(error)
      }
    }

    // 不属于 401 重试路径：显示通用错误
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
