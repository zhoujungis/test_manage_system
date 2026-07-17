// H39 fix: 统一项目内的日期显示格式。原先 4-5 个 view 各用各的：
//   - row.created_at?.slice(0, 19).replace('T', ' ')
//   - new Date(d).toLocaleString('zh-CN', {...})
//   - 原始 YYYY-MM-DD 字符串
// 后端时区是 Asia/Shanghai，这里统一显示为本地时间并标上时区。

const TZ = 'Asia/Shanghai'
const ZONE_SUFFIX = ' (北京时间)'

/** 把 ISO 字符串 / Date 转成 'YYYY-MM-DD HH:mm' 本地时间字符串。 */
export function formatDateTime(input) {
  if (!input) return '-'
  const d = input instanceof Date ? input : new Date(input)
  if (Number.isNaN(d.getTime())) return String(input)
  const pad = (n) => String(n).padStart(2, '0')
  return (
    d.getFullYear() + '-' +
    pad(d.getMonth() + 1) + '-' +
    pad(d.getDate()) + ' ' +
    pad(d.getHours()) + ':' +
    pad(d.getMinutes())
  )
}

/** 'YYYY-MM-DD' 纯日期。 */
export function formatDate(input) {
  if (!input) return '-'
  const d = input instanceof Date ? input : new Date(input)
  if (Number.isNaN(d.getTime())) return String(input)
  const pad = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate())
}

/** 带时区提示的完整日期时间。 */
export function formatDateTimeWithTz(input) {
  return formatDateTime(input) + ZONE_SUFFIX
}

export { TZ }