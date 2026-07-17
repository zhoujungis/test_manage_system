// H32 fix: AbortController 跨 view 统一工具。
// 用法：
//   const { signal, abortOnUnmount } = useAbort()
//   async function load() {
//     try {
//       const data = await getProjects({}, { signal: signal() })
//       ...
//     } catch (e) {
//       if (axios.isCancel(e)) return  // 切页 / 重新触发，旧请求被取消
//     }
//   }
//
// `signal()` 每次取最新 controller 的 signal；同一组件多次并发调用，
// 旧的 controller 会自动 abort。

import { onBeforeUnmount, ref } from 'vue'
import axios from 'axios'

export function useAbort() {
  const _ctrl = ref(null)

  function signal() {
    // 取最新 signal；旧 controller 自动 abort（避免 stale response）
    if (_ctrl.value) _ctrl.value.abort()
    _ctrl.value = new AbortController()
    return _ctrl.value.signal
  }

  function cancel() {
    if (_ctrl.value) {
      _ctrl.value.abort()
      _ctrl.value = null
    }
  }

  function isCancel(err) {
    return axios.isCancel(err)
  }

  // H17 兼容：组件卸载时清掉，避免 in-flight 请求写回已 unmount 的 ref
  onBeforeUnmount(cancel)

  return { signal, cancel, isCancel }
}