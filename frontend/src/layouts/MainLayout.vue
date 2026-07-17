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
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'

const route = useRoute()

const isFlush = computed(() => route.meta?.flushMain === true)

// 路径 → 中文标签的映射。matched 链能拿到模板字符串如 '/projects/:id'，
// 用它做 key，再查表出 label。
const CRUMB_LABELS = {
  '/': '首页',
  '/home': '工作台',
  '/projects': '项目管理',
  '/projects/:id': '项目详情',
  '/projects/:id/modules': '模块管理',
  '/projects/:id/testcases': '测试用例',
  '/projects/:id/testplans': '测试计划',
  '/projects/:id/testplans/:pid': '计划详情',
  '/projects/:id/testruns': '测试执行',
  '/projects/:id/testruns/:rid': '执行详情',
  '/projects/:id/defects': '缺陷管理',
  '/projects/:id/defects/:did': '缺陷详情',
  '/testcases': '用例库',
  '/testcases/:product_line': '用例库',
  '/testcases/:product_line/new': '新建用例',
  '/testcases/:product_line/:tid': '用例详情',
  '/tm': '我的项目',
  '/tm/:id/execute': '我的执行',
  '/admin/users': '用户管理',
  '/admin/permissions': '权限管理',
}

const crumbs = computed(() => {
  return route.matched
    .filter((r) => r.meta && r.meta.noAuth !== true && r.path !== '')
    .map((r) => ({
      label: CRUMB_LABELS[r.path] || r.meta?.title || r.path,
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
