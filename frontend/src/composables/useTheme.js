// DARK-1: 主题切换 composable。
// - 偏好持久化到 localStorage('tm_theme')
// - [data-theme] 写到 document.documentElement，方便 CSS 用 [data-theme="dark"] 选择
// - 监听系统 prefers-color-scheme：用户没设过偏好时跟随系统
import { ref } from 'vue'

const STORAGE_KEY = 'tm_theme'
export const THEMES = ['light', 'dark']

const themeRef = ref('light')
let initialized = false

function detectSystemTheme() {
  if (typeof window === 'undefined' || !window.matchMedia) return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function initTheme() {
  if (initialized) return
  initialized = true
  if (typeof localStorage !== 'undefined') {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && THEMES.includes(saved)) {
      themeRef.value = saved
      return
    }
  }
  themeRef.value = detectSystemTheme()
}

export function applyTheme() {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute('data-theme', themeRef.value)
}

export function setTheme(theme) {
  if (!THEMES.includes(theme)) return
  themeRef.value = theme
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, theme)
  }
  applyTheme()
}

export function toggleTheme() {
  setTheme(themeRef.value === 'dark' ? 'light' : 'dark')
}

export function useTheme() {
  return {
    theme: themeRef,
    setTheme,
    toggleTheme,
    THEMES,
  }
}