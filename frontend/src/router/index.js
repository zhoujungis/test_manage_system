import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { isPathAllowed, canManageTestCaseLibrary } from '@/utils/permissions'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/LoginView.vue'), meta: { noAuth: true } },

  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/home' },
      { path: 'home', name: 'Home', component: () => import('@/views/HomeView.vue') },

      {
        path: 'testcases',
        redirect: '/testcases/camera',
        children: [
          {
            path: ':product_line',
            name: 'TestCases',
            component: () => import('@/views/TestCaseManagementView.vue'),
            meta: { flushMain: true },
          },
          {
            path: ':product_line/new',
            name: 'TestCaseNew',
            component: () => import('@/views/TestCaseDetailView.vue'),
          },
          {
            path: ':product_line/:tid',
            name: 'TestCaseDetail',
            component: () => import('@/views/TestCaseDetailView.vue'),
          },
        ],
      },

      { path: 'tm', name: 'TM', component: () => import('@/views/PersonalProjectsView.vue') },
      {
        path: 'tm/:id/execute',
        name: 'TMExecute',
        component: () => import('@/views/MyTestExecuteView.vue'),
        meta: { flushMain: true },
      },

      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/views/ProjectListView.vue'),
      },
      {
        path: 'admin/permissions',
        name: 'AdminPermissions',
        component: () => import('@/views/AdminPermissionsView.vue'),
        meta: { requiresAdmin: true },
      },
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/AdminUsersView.vue'),
        meta: { requiresAdmin: true },
      },

      {
        path: 'projects/:id',
        component: () => import('@/layouts/ProjectLayout.vue'),
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

const r = createRouter({ history: createWebHistory(), routes })

let authReady = false

r.beforeEach(async (to, from, next) => {
  if (to.meta.noAuth) return next()
  if (!localStorage.getItem('access_token')) return next('/login')

  const auth = useAuthStore()
  if (!authReady) {
    await auth.init()
    authReady = true
  } else if (auth.token && !auth.user) {
    await auth.fetchUser()
  }

  const user = auth.user
  if (user && !isPathAllowed(user, to.path)) {
    ElMessage.warning(to.meta.requiresAdmin ? '仅管理员可访问' : '您没有访问该页面的权限')
    return next('/home')
  }
  if (user && /\/testcases\/[^/]+\/new$/.test(to.path) && !canManageTestCaseLibrary(user)) {
    ElMessage.warning('只读账号无法新建用例')
    return next('/home')
  }

  next()
})

export default r
