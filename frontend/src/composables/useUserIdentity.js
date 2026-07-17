import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  canAccessProjects as _canAccessProjects,
  canAccessTestCaseLibrary as _canAccessTestCaseLibrary,
  canManageTestCaseLibrary as _canManageTestCaseLibrary,
  canAccessMyProjects as _canAccessMyProjects,
  canWriteProjects as _canWriteProjects,
  isAdmin as _isAdmin,
  isViewer as _isViewer,
  defaultHomePath as _defaultHomePath,
} from '@/utils/permissions'
import { formatDateTime } from '@/utils/dateFormat'

const ROLE_TAG_TYPE = { admin: 'danger', tester: 'success', developer: 'warning', viewer: 'info' }
const ROLE_LABELS = { admin: '管理员', tester: '测试工程师', developer: '测试开发工程师', viewer: '观察者' }

/** 当前登录用户身份信息（来自 /api/auth/me/ 数据库读取）
 *
 * M25 fix: 去掉 `user.value?.profile?.xxx` fallback —— 后端 UserSerializer 不再返回 profile 对象，
 * 之前的 fallback 链是死代码。
 * M37 fix: 多个权限 getter 合并到 `permissions` 对象，避免一上来 15+ 个 computed 全跑。
 */
export function useUserIdentity() {
  const auth = useAuthStore()

  const user = computed(() => auth.user)

  const displayName = computed(
    () => user.value?.username || user.value?.email?.split('@')[0] || '用户'
  )
  const role = computed(() => user.value?.role || '')
  const roleLabel = computed(() => {
    if (user.value?.role_label) return user.value.role_label
    return ROLE_LABELS[role.value] || role.value || ''
  })
  const roleTagType = computed(() => ROLE_TAG_TYPE[role.value] || 'info')
  const email = computed(() => user.value?.email || '')
  const phone = computed(() => user.value?.phone || '')
  const userId = computed(() => user.value?.id ?? '')
  const joinedAt = computed(() => formatDateTime(user.value?.date_joined))
  const avatarLetter = computed(() => (displayName.value || email.value || '?').charAt(0).toUpperCase())
  const isLoaded = computed(() => auth.ready && !!user.value)

  // 把所有权限相关的 computed 合并到一个对象 —— 懒加载
  const permissions = computed(() => ({
    isAdmin: _isAdmin(user.value),
    isViewer: _isViewer(user.value),
    canAccessProjects: _canAccessProjects(user.value),
    canAccessTestCaseLibrary: _canAccessTestCaseLibrary(user.value),
    canManageTestCaseLibrary: _canManageTestCaseLibrary(user.value),
    canAccessMyProjects: _canAccessMyProjects(user.value),
    canWriteProjects: _canWriteProjects(user.value),
  }))

  const homePath = computed(() => _defaultHomePath())

  return {
    user,
    displayName,
    role,
    roleLabel,
    roleTagType,
    email,
    phone,
    userId,
    joinedAt,
    avatarLetter,
    isLoaded,
    permissions,   // 替代旧 API 中的 canAccessProjects 等（保留向后兼容导出）
    // 向后兼容：保持 canAccessProjects 等顶级 computed 也能用
    isAdmin: computed(() => permissions.value.isAdmin),
    canAccessProjects: computed(() => permissions.value.canAccessProjects),
    canAccessTestCaseLibrary: computed(() => permissions.value.canAccessTestCaseLibrary),
    canManageTestCaseLibrary: computed(() => permissions.value.canManageTestCaseLibrary),
    canAccessMyProjects: computed(() => permissions.value.canAccessMyProjects),
    canWriteProjects: computed(() => permissions.value.canWriteProjects),
    isViewer: computed(() => permissions.value.isViewer),
    homePath,
    refresh: () => auth.fetchUser(),
  }
}