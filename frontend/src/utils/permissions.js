export const ROLE_ADMIN = 'admin'

export function getRole(user) {
  return user?.role || user?.profile?.role || ''
}

export function isAdmin(user) {
  return getRole(user) === ROLE_ADMIN || user?.is_admin === true
}

// SECURITY (C5 fix): fail-closed. 缺失/未知/空 payload 一律给全 false，
// 不再 fallback 到 "all true"。前端权限只是 UI 隐藏，
// 后端必须仍然强校验；这里只是把"前端误以为有空权限"上锁。
const FLAG_KEYS = [
  'can_access_projects',
  'can_access_testcase_library',
  'can_manage_testcase_library',
  'can_access_my_projects',
]

function allFlagsFalse() {
  return FLAG_KEYS.reduce((acc, k) => {
    acc[k] = false
    return acc
  }, {})
}

export function getPermissions(user) {
  if (isAdmin(user)) {
    return {
      can_access_projects: true,
      can_access_testcase_library: true,
      can_manage_testcase_library: true,
      can_access_my_projects: true,
    }
  }
  if (!user) return allFlagsFalse()

  const p = user.permissions
  // 只信任显式、由后端返回的 boolean payload
  if (p && typeof p === 'object') {
    return {
      can_access_projects: p.can_access_projects === true,
      can_access_testcase_library: p.can_access_testcase_library === true,
      can_manage_testcase_library: p.can_manage_testcase_library === true,
      can_access_my_projects: p.can_access_my_projects === true,
    }
  }
  // 兜底：无 payload 时一律 deny（原代码兜底到 all-true，是 fail-open 漏洞）
  return allFlagsFalse()
}

export function isViewer(user) {
  return getRole(user) === 'viewer'
}

export function canWriteProjects(user) {
  return canAccessProjects(user) && !isViewer(user)
}

export function canAccessProjects(user) {
  return getPermissions(user).can_access_projects
}

export function canAccessTestCaseLibrary(user) {
  return getPermissions(user).can_access_testcase_library
}

export function canManageTestCaseLibrary(user) {
  return getPermissions(user).can_manage_testcase_library
}

export function canAccessMyProjects(user) {
  return getPermissions(user).can_access_my_projects
}

export function defaultHomePath() {
  return '/home'
}

export function isProjectsPath(path) {
  return path === '/projects' || path.startsWith('/projects/')
}

export function isAdminPath(path) {
  return path.startsWith('/admin/')
}

export function isPathAllowed(user, path) {
  if (path.startsWith('/login')) return true
  if (isAdminPath(path)) return isAdmin(user)
  if (isProjectsPath(path)) return canAccessProjects(user)
  if (path.startsWith('/testcases')) return canAccessTestCaseLibrary(user)
  if (path.startsWith('/tm')) return canAccessMyProjects(user)
  return true
}

/** @deprecated 使用 canAccessProjects */
export function isTester(user) {
  return getRole(user) === 'tester'
}

export function isPathAllowedForTester(path) {
  return isPathAllowed({ role: 'tester', permissions: { can_access_projects: false } }, path)
}
