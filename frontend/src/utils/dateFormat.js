// H39 fix: 统一日期格式 + I18N-5: 跟随 locale。
// zh-CN → 'YYYY-MM-DD HH:mm (北京时间)'
// en-US → 'MM/DD/YYYY, HH:mm'
//
// 注意：standalone 函数读 localStorage('tm_locale') 来决定格式；
// 在 setup() 里用 `useDateFormat()` 更准确（响应式）。

import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

let _cachedLocale = null
let _tzLabel = '北京时间'

function currentLocale() {
  if (_cachedLocale) return _cachedLocale
  if (typeof localStorage !== 'undefined') {
    const saved = localStorage.getItem('tm_locale')
    if (saved) _cachedLocale = saved
  }
  return _cachedLocale || 'zh-CN'
}

/** setLocale() 调用时同步刷新缓存。 */
export function _syncDateFormatLocale(locale, tz) {
  _cachedLocale = locale
  if (tz) _tzLabel = tz
}

// ---- 内部 ----
function _format(input, mode) {
  if (!input) return '-'
  const d = input instanceof Date ? input : new Date(input)
  if (Number.isNaN(d.getTime())) return String(input)
  const pad = (n) => String(n).padStart(2, '0')
  const locale = currentLocale()
  if (locale === 'en-US') {
    if (mode === 'date') {
      return `${pad(d.getMonth() + 1)}/${pad(d.getDate())}/${d.getFullYear()}`
    }
    return `${pad(d.getMonth() + 1)}/${pad(d.getDate())}/${d.getFullYear()}, ${pad(d.getHours())}:${pad(d.getMinutes())}`
  }
  if (mode === 'date') {
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  }
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ---- standalone exports ----
export function formatDateTime(input) {
  return _format(input, 'datetime')
}
export function formatDate(input) {
  return _format(input, 'date')
}
export function formatDateTimeWithTz(input) {
  return _format(input, 'datetime') + ' ' + _tzLabel
}

// ---- composable for setup() context ----
export function useDateFormat() {
  const { locale, t } = useI18n()
  // 监听 i18n locale 变化时刷新 standalone 缓存
  if (locale.value) _cachedLocale = locale.value
  const formatted = computed(() => {
    return {
      formatDateTime: (input) => _format(input, 'datetime'),
      formatDate: (input) => _format(input, 'date'),
      formatDateTimeWithTz: (input) => _format(input, 'datetime') + ' ' + t('common.beijingTime'),
    }
  })
  return formatted
}