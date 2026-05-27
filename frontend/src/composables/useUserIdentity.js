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

const ROLE_TAG_TYPE = {
  admin: 'danger',
  tester: 'success',
  developer: 'warning',
  viewer: 'info',
}

const ROLE_LABELS = {
  admin: '管理员',
  tester: '测试工程师',
  developer: '测试开发工程师',
  viewer: '观察者',
}

/** 当前登录用户身份信息（来自 /api/auth/me/ 数据库读取） */
export function useUserIdentity() {
  const auth = useAuthStore()

  const user = computed(() => auth.user)

  const displayName = computed(
    () => user.value?.username || user.value?.email?.split('@')[0] || '用户'
  )

  const role = computed(
    () => user.value?.role || user.value?.profile?.role || ''
  )

  const roleLabel = computed(() => {
    if (user.value?.role_label) return user.value.role_label
    const code = user.value?.role || user.value?.profile?.role
    return ROLE_LABELS[code] || code || ''
  })

  const roleTagType = computed(() => ROLE_TAG_TYPE[role.value] || 'info')

  const email = computed(() => user.value?.email || '')

  const phone = computed(() => user.value?.phone || user.value?.profile?.phone || '')

  const userId = computed(() => user.value?.id ?? '')

  const joinedAt = computed(() => {
    const raw = user.value?.date_joined
    if (!raw) return ''
    return String(raw).slice(0, 19).replace('T', ' ')
  })

  const avatarLetter = computed(() => {
    const name = displayName.value || email.value || '?'
    return name.charAt(0).toUpperCase()
  })

  const isLoaded = computed(() => auth.ready && !!user.value)

  const isAdminRole = computed(() => _isAdmin(user.value))
  const canAccessProjects = computed(() => _canAccessProjects(user.value))
  const canAccessTestCaseLibrary = computed(() => _canAccessTestCaseLibrary(user.value))
  const canManageTestCaseLibrary = computed(() => _canManageTestCaseLibrary(user.value))
  const canAccessMyProjects = computed(() => _canAccessMyProjects(user.value))
  const canWriteProjects = computed(() => _canWriteProjects(user.value))
  const isViewerRole = computed(() => _isViewer(user.value))
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
    isAdmin: isAdminRole,
    canAccessProjects,
    canAccessTestCaseLibrary,
    canManageTestCaseLibrary,
    canAccessMyProjects,
    canWriteProjects,
    isViewer: isViewerRole,
    homePath,
    refresh: () => auth.fetchUser(),
  }
}
