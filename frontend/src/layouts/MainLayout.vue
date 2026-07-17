<template>
  <div class="app-shell">
    <AppHeader />
    <main class="app-shell__main" :class="{ 'app-shell__main--flush': isFlush }">
      <!-- H37 fix: 面包屑让深链 /projects/:id/testplans/:pid 可追溯 -->
      <el-breadcrumb v-if="crumbs.length > 1" class="app-shell__crumbs" separator="/">
        <el-breadcrumb-item v-for="(c, i) in crumbs" :key="i" :to="c.to">
          {{ c.label }}
        </el-breadcrumb-item>
      </el-breadcrumb>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'

const { t } = useI18n()
const route = useRoute()

const isFlush = computed(() => route.meta?.flushMain === true)

// 路径 → i18n key 的映射。matched 链能拿到模板字符串如 '/projects/:id'。
const CRUMB_KEYS = {
  '/': 'crumb.home',
  '/home': 'crumb.home',
  '/projects': 'crumb.projects',
  '/projects/:id': 'crumb.project',
  '/projects/:id/modules': 'crumb.modules',
  '/projects/:id/testcases': 'crumb.testcases',
  '/projects/:id/testplans': 'crumb.testplans',
  '/projects/:id/testplans/:pid': 'crumb.testplanDetail',
  '/projects/:id/testruns': 'crumb.testruns',
  '/projects/:id/testruns/:rid': 'crumb.testrunDetail',
  '/projects/:id/defects': 'crumb.defects',
  '/projects/:id/defects/:did': 'crumb.defectDetail',
  '/testcases': 'crumb.library',
  '/testcases/:product_line': 'crumb.library',
  '/testcases/:product_line/new': 'crumb.testcaseNew',
  '/testcases/:product_line/:tid': 'crumb.testcaseDetail',
  '/tm': 'crumb.myProjectsRoot',
  '/tm/:id/execute': 'crumb.myExecution',
  '/admin/users': 'menu.adminUsers',
  '/admin/permissions': 'menu.adminPermissions',
}

const crumbs = computed(() => {
  return route.matched
    .filter((r) => r.meta && r.meta.noAuth !== true && r.path !== '')
    .map((r) => ({
      label: t(CRUMB_KEYS[r.path] || r.meta?.title || r.path),
      to: { path: r.path.replace(/:(\w+)/g, (_, k) => route.params[k] || '') },
    }))
})
</script>

<style scoped>
.app-shell__crumbs {
  padding: 12px 16px 0;
  font-size: 13px;
}
</style>
