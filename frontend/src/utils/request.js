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
  const refreshToken = sessionStorage.getItem('refresh_token') || localStorage.getItem('refresh_token')
  if (!refreshToken) return Promise.reject(new Error('no refresh token'))
  inflightRefresh = refreshClient
    .post('/auth/refresh/', { refresh: refreshToken })
    .then((res) => {
      const data = res.data
      if (!data || !data.access) throw new Error('invalid refresh response')
      // C10 fix: 迁到 sessionStorage（仍非 HttpOnly cookie，但 tab 关即清，缩小 XSS 留存时间）；
      // 同时同步写到 localStorage 兼容现有 refresh 兜底。注释里挂 TODO 提示迁 HttpOnly cookie。
      // TODO(security): 后端支持后切到 HttpOnly Secure SameSite=Lax cookie，由 Set-Cookie 注入。
      sessionStorage.setItem('access_token', data.access)
      localStorage.setItem('access_token', data.access)
      if (data.refresh) {
        sessionStorage.setItem('refresh_token', data.refresh)
        localStorage.setItem('refresh_token', data.refresh)
      }
      notifyAuthStore(data.access, data.refresh)
      return data.access
    })
    .catch((err) => {
      // refresh 失败：清掉 token、调用 store.logout() 让状态机重置
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('refresh_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      notifyAuthStore(null, null)
      // C18 fix: 走 store.logout()（重置 auth.ready）而不是直接 router.push
      // 避免 router/index.js 里模块级 authReady 卡在 true 永远不再 init。
      try {
        import('@/stores/auth').then(({ useAuthStore }) => {
          const store = useAuthStore()
          store.logout?.()
        })
      } catch {
        router.push('/login')
      }
      throw err
    })
    .finally(() => {
      inflightRefresh = null
    })
  return inflightRefresh
}

request.interceptors.request.use(
  (config) => {
    // C10 fix: sessionStorage 优先，localStorage 兜底兼容旧 refresh
    const token = sessionStorage.getItem('access_token') || localStorage.getItem('access_token')
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
    // C16 fix: 默认 toast（保持兼容所有 `catch { /* */ }` 模式）；
    // view 想自己展示更精确的错误时，传 _silent: true 即可。
    if (!error.config?._skipInterceptors && !error.config?._silent) {
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
      ElMessage({ message: msg, type: 'error', duration: 4500 })
    }
    return Promise.reject(error)
  }
)

export default request
