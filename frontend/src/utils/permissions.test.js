// H28 fix: permissions 工具的烟雾测试 —— fail-closed 默认值 + 角色对应权限。
import { describe, it, expect } from 'vitest'
import { isPathAllowed } from './permissions.js'

describe('isPathAllowed', () => {
  it('deny-closed：未登录用户全部 false', () => {
    const u = { permissions: { can_access_projects: false, can_access_testcase_library: false, can_access_my_projects: false } }
    expect(isPathAllowed(u, '/home')).toBe(false)
    expect(isPathAllowed(u, '/projects')).toBe(false)
  })

  it('有项目管理权限 → /projects/* 放行', () => {
    const u = { permissions: { can_access_projects: true } }
    expect(isPathAllowed(u, '/projects')).toBe(true)
    expect(isPathAllowed(u, '/projects/123')).toBe(true)
  })

  it('有 my_projects 权限 → /tm/* 放行', () => {
    const u = { permissions: { can_access_my_projects: true } }
    expect(isPathAllowed(u, '/tm')).toBe(true)
    expect(isPathAllowed(u, '/tm/5/execute')).toBe(true)
  })

  it('没有测试用例库权限 → /testcases/* false', () => {
    const u = { permissions: { can_access_testcase_library: false } }
    expect(isPathAllowed(u, '/testcases/camera')).toBe(false)
  })
})