export const ROLE_ADMIN = 'admin'

export function getRole(user) {
  return user?.role || user?.profile?.role || ''
}

export function isAdmin(user) {
  return getRole(user) === ROLE_ADMIN || user?.is_admin === true
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
  const p = user?.permissions
  if (p) {
    if (getRole(user) === 'viewer') {
      const hasRead =
        p.can_access_projects || p.can_access_testcase_library || p.can_access_my_projects
      if (!hasRead) {
        return {
          can_access_projects: true,
          can_access_testcase_library: true,
          can_manage_testcase_library: false,
          can_access_my_projects: true,
        }
      }
    }
    return p
  }
  // 兼容旧数据：测试工程师默认无项目管理
  if (getRole(user) === 'tester') {
    return {
      can_access_projects: false,
      can_access_testcase_library: true,
      can_manage_testcase_library: false,
      can_access_my_projects: true,
    }
  }
  if (getRole(user) === 'viewer') {
    return {
      can_access_projects: true,
      can_access_testcase_library: true,
      can_manage_testcase_library: false,
      can_access_my_projects: true,
    }
  }
  return {
    can_access_projects: true,
    can_access_testcase_library: true,
    can_manage_testcase_library: true,
    can_access_my_projects: true,
  }
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
