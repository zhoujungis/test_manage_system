import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  isPathAllowed,
  canManageTestCaseLibrary,
  isAdmin,
} from '@/utils/permissions'

// 路由 meta 约定：
//   - requiresAuth: 必须登录（默认全部登录态页面都 true）
//   - noAuth: 公开页（如 /login）
//   - permission: 进入页面所需的细粒度权限 key
//   - writePermission: 进入页面所需的写权限（比 permission 更严）
//   - admin: 只有管理员可访问
const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/LoginView.vue'), meta: { noAuth: true } },

  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/home' },
      { path: 'home', name: 'Home', component: () => import('@/views/HomeView.vue'), meta: { permission: 'any' } },

      {
        path: 'testcases',
        redirect: '/testcases/camera',
        children: [
          {
            path: ':product_line',
            name: 'TestCases',
            component: () => import('@/views/TestCaseManagementView.vue'),
            meta: { permission: 'library', flushMain: true },
          },
          {
            path: ':product_line/new',
            name: 'TestCaseNew',
            component: () => import('@/views/TestCaseDetailView.vue'),
            meta: { writePermission: 'manageLibrary' },
          },
          {
            path: ':product_line/:tid',
            name: 'TestCaseDetail',
            component: () => import('@/views/TestCaseDetailView.vue'),
            meta: { permission: 'library' },
          },
        ],
      },

      { path: 'tm', name: 'TM', component: () => import('@/views/PersonalProjectsView.vue'), meta: { permission: 'myProjects' } },
      {
        path: 'tm/:id/execute',
        name: 'TMExecute',
        component: () => import('@/views/MyTestExecuteView.vue'),
        meta: { permission: 'myProjects', flushMain: true },
      },

      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/views/ProjectListView.vue'),
        meta: { permission: 'projects' },
      },
      {
        path: 'admin/permissions',
        name: 'AdminPermissions',
        component: () => import('@/views/AdminPermissionsView.vue'),
        meta: { admin: true },
      },
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/AdminUsersView.vue'),
        meta: { admin: true },
      },

      {
        path: 'projects/:id',
        component: () => import('@/layouts/ProjectLayout.vue'),
        meta: { permission: 'projects' },
        children: [
          { path: 'modules', name: 'Modules', component: () => import('@/views/ModuleTreeView.vue') },
          { path: 'testcases', name: 'ProjectTestCases', component: () => import('@/views/TestCaseListView.vue') },
          { path: 'testcases/:tid', name: 'ProjectTestCaseDetail', component: () => import('@/views/TestCaseDetailView.vue') },
          { path: 'testplans', name: 'TestPlans', component: () => import('@/views/TestPlanListView.vue') },
          { path: 'testplans/:pid', name: 'TestPlanDetail', component: () => import('@/views/TestPlanDetailView.vue') },
          { path: 'testruns', name: 'TestRuns', component: () => import('@/views/TestRunListView.vue') },
          { path: 'testruns/:rid', name: 'TestRunExecute', component: () => import('@/views/TestRunExecuteView.vue') },
          { path: 'defects', name: 'Defects', component: () => import('@/views/DefectListView.vue') },
          { path: 'defects/:did', name: 'DefectDetail', component: () => import('@/views/DefectDetailView.vue') },
        ],
      },
    ],
  },
]

const r = createRouter({
  history: createWebHistory(),
  routes,
  // M29 fix: 路由切换时保留滚动位置（列表页 → 详情 → 返回）
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { top: 0 }
  },
})

/**
 * meta.permission 字符串 -> 是否满足
 *   'any' 仅需登录
 *   'projects' 'library' 'manageLibrary' 'myProjects' 对应四个 flag
 *   其他 / 缺失 → 视为 'any'
 */
function hasReadPermission(user, key) {
  if (isAdmin(user)) return true
  if (!user) return false
  if (!key || key === 'any') return true
  return {
    projects: user.permissions?.can_access_projects === true,
    library: user.permissions?.can_access_testcase_library === true,
    myProjects: user.permissions?.can_access_my_projects === true,
    manageLibrary: user.permissions?.can_manage_testcase_library === true,
  }[key] === true
}

function hasWritePermission(user, key) {
  if (isAdmin(user)) return true
  if (!user) return false
  if (!key) return false
  if (key === 'manageLibrary') return canManageTestCaseLibrary(user)
  return false
}

// C18 fix: 用 store.ready 取代模块级 authReady 变量。
// 之前模块级变量在 logout 后永远是 true，导致再登录后路由不再重新 init。
// store.logout() 会把 ready 重置为 false。
r.beforeEach(async (to, from) => {
  const meta = to.meta || {}

  // 1. noAuth 直接放行
  if (meta.noAuth) return true

  // 2. 缺 token → 跳登录 + 携带 redirect
  // C10 fix: sessionStorage 优先 + localStorage 兜底
  const hasToken = sessionStorage.getItem('access_token') || localStorage.getItem('access_token')
  if (!hasToken) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  // 3. 拉取 user（首次访问 / 过期丢失）
  const auth = useAuthStore()
  if (!auth.ready) {
    await auth.init()
  } else if (auth.token && !auth.user) {
    try {
      await auth.fetchUser()
    } catch {
      auth.logout()
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }

  const user = auth.user

  // 4. 拿到 user 但访问失败一律 deny-closed
  if (!user) return { path: '/login', query: { redirect: to.fullPath } }

  if (meta.admin && !isAdmin(user)) {
    ElMessage.warning('仅管理员可访问')
    return { path: '/home' }
  }
  if (!hasReadPermission(user, meta.permission)) {
    ElMessage.warning('您没有访问该页面的权限')
    return { path: '/home' }
  }
  if (meta.writePermission && !hasWritePermission(user, meta.writePermission)) {
    ElMessage.warning('当前账号没有写权限')
    return { path: '/home' }
  }

  // 5. 兜底 —— 路径白名单再核对一次
  if (!isPathAllowed(user, to.path)) {
    ElMessage.warning('您没有访问该页面的权限')
    return { path: '/home' }
  }

  return true
})

export default r
