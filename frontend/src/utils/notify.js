// M19 fix: 全局消息工具。成功 / 错误用不同 duration，避免 3s 闪走。
import { ElMessage } from 'element-plus'

const DEFAULT_DURATION_SUCCESS = 2500
const DEFAULT_DURATION_ERROR = 4500

export function notifySuccess(msg, opts = {}) {
  return ElMessage({ message: msg, type: 'success', duration: DEFAULT_DURATION_SUCCESS, ...opts })
}

export function notifyError(msg, opts = {}) {
  return ElMessage({ message: msg, type: 'error', duration: DEFAULT_DURATION_ERROR, ...opts })
}

export function notifyWarning(msg, opts = {}) {
  return ElMessage({ message: msg, type: 'warning', duration: DEFAULT_DURATION_ERROR, ...opts })
}

export function notifyInfo(msg, opts = {}) {
  return ElMessage({ message: msg, type: 'info', duration: DEFAULT_DURATION_SUCCESS, ...opts })
}