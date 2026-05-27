<template>
  <el-container class="project-layout">
    <el-aside v-if="projectId" :width="`${sidebarWidth}px`" class="project-sidebar">
      <div class="project-sidebar__head" @click="$router.push('/projects')">
        <el-icon :size="18"><Folder /></el-icon>
        <span class="project-sidebar__name">{{ project?.name || '项目' }}</span>
      </div>
      <el-menu :default-active="activeMenu" class="project-sidebar__menu" router>
        <el-menu-item :index="`/projects/${projectId}/modules`">
          <el-icon><Grid /></el-icon>
          <span>模块管理</span>
        </el-menu-item>
        <el-menu-item :index="`/projects/${projectId}/testcases`">
          <el-icon><Collection /></el-icon>
          <span>项目用例</span>
        </el-menu-item>
        <el-menu-item :index="`/projects/${projectId}/testplans`">
          <el-icon><List /></el-icon>
          <span>测试计划</span>
        </el-menu-item>
        <el-menu-item :index="`/projects/${projectId}/testruns`">
          <el-icon><VideoPlay /></el-icon>
          <span>测试执行</span>
        </el-menu-item>
        <el-menu-item :index="`/projects/${projectId}/defects`">
          <el-icon><WarningFilled /></el-icon>
          <span>缺陷管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main class="project-layout__content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed, watch, ref } from 'vue'
import { useRoute } from 'vue-router'
import request from '@/utils/request'

const route = useRoute()
const projectId = computed(() => route.params.id)
const project = ref(null)
const sidebarWidth = 220

const activeMenu = computed(() => {
  const p = route.path
  if (p.includes('/modules')) return `/projects/${projectId.value}/modules`
  if (p.includes('/testcases')) return `/projects/${projectId.value}/testcases`
  if (p.includes('/testplans')) return `/projects/${projectId.value}/testplans`
  if (p.includes('/testruns')) return `/projects/${projectId.value}/testruns`
  if (p.includes('/defects')) return `/projects/${projectId.value}/defects`
  return ''
})

watch(projectId, async (id) => {
  if (id) {
    try { project.value = await request.get(`/projects/${id}/`) }
    catch { project.value = null }
  } else {
    project.value = null
  }
}, { immediate: true })
</script>

<style scoped>
.project-layout {
  min-height: calc(100vh - var(--tm-header-height));
  background: var(--tm-bg);
}

.project-sidebar {
  background: var(--tm-sidebar);
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(15, 23, 42, 0.06);
}

.project-sidebar__head {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 16px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  transition: background 0.15s;
}

.project-sidebar__head:hover {
  background: var(--tm-sidebar-hover);
}

.project-sidebar__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-sidebar__menu {
  border-right: none !important;
  background: transparent !important;
  padding: 8px;
  flex: 1;
}

.project-sidebar__menu :deep(.el-menu-item) {
  color: var(--tm-sidebar-text) !important;
  border-radius: var(--tm-radius-sm);
  margin-bottom: 2px;
  height: 44px;
}

.project-sidebar__menu :deep(.el-menu-item:hover) {
  background: var(--tm-sidebar-hover) !important;
  color: var(--tm-sidebar-text-active) !important;
}

.project-sidebar__menu :deep(.el-menu-item.is-active) {
  background: var(--tm-sidebar-active) !important;
  color: var(--tm-sidebar-text-active) !important;
  font-weight: 600;
}

.project-layout__content {
  padding: 24px;
  background: var(--tm-bg);
}
</style>
