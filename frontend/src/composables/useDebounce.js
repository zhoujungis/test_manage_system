import { ref, watch, onScopeDispose } from 'vue'

export function useDebounce(source, delay = 300) {
  const debounced = ref(source.value)

  let timer = null
  watch(source, (val) => {
    clearTimeout(timer)
    timer = setTimeout(() => {
      debounced.value = val
    }, delay)
  })

  // H33 fix: 卸载时清掉 pending timer —— 不然组件 unmount 后定时器还会
  // 触发写入已无人订阅的 ref，泄漏 timer 与潜在状态写入。
  onScopeDispose(() => {
    if (timer) clearTimeout(timer)
    timer = null
  })

  return debounced
}