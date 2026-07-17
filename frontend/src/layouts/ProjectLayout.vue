<template>
  <el-container class="project-layout">
    <!-- H38 fix: 移动端 sidebar 收起成 drawer；桌面端正常显示 -->
    <el-aside
      v-if="projectId"
      :width="`${sidebarWidth}px`"
      class="project-sidebar"
      :class="{ 'project-sidebar--collapsed': isMobile && !mobileOpen }"
    >
      <div class="project-sidebar__head" @click="$router.push('/projects')">
        <el-icon :size="18"><Folder /></el-icon>
        <span v-if="!isMobile" class="project-sidebar__name">{{ project?.name || '项目' }}</span>
      </div>
      <el-menu :default-active="activeMenu" class="project-sidebar__menu" router>
        <el-menu-item :index="`/projects/${projectId}/modules`">
          <el-icon><Grid /></el-icon>
          <template #title>模块管理</template>
        </el-menu-item>
        <el-menu-item :index="`/projects/${projectId}/testcases`">
          <el-icon><Collection /></el-icon>
          <template #title>项目用例</template>
        </el-menu-item>
        <el-menu-item :index="`/projects/${projectId}/testplans`">
          <el-icon><List /></el-icon>
          <template #title>测试计划</template>
        </el-menu-item>
        <el-menu-item :index="`/projects/${projectId}/testruns`">
          <el-icon><VideoPlay /></el-icon>
          <template #title>测试执行</template>
        </el-menu-item>
        <el-menu-item :index="`/projects/${projectId}/defects`">
          <el-icon><WarningFilled /></el-icon>
          <template #title>缺陷管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 移动端浮动按钮 + drawer overlay -->
    <template v-if="isMobile">
      <el-button class="project-mobile-burger" type="primary" circle @click="mobileOpen = true">
        <el-icon :size="20"><Menu /></el-icon>
      </el-button>
      <div v-if="mobileOpen" class="project-mobile-mask" @click="mobileOpen = false" />
    </template>

    <el-main class="project-layout__content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed, watch, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import request from '@/utils/request'
import { Menu } from '@element-plus/icons-vue'

const route = useRoute()
const projectId = computed(() => route.params.id)
const project = ref(null)

// H38 fix: 768px 以下认为是移动端
const isMobile = ref(false)
const mobileOpen = ref(false)

function handleResize() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) mobileOpen.value = false
}
onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => window.removeEventListener('resize', handleResize))

// 路由变化关闭移动端 drawer
watch(() => route.path, () => { mobileOpen.value = false })

const sidebarWidth = computed(() => (isMobile.value ? 0 : 220))

const activeMenu = computed(() => {
  // 按路径 segment 精确匹配 —— 旧 includes() 会让 /testcase-templates 命中 testcases
  const segs = route.path.split('/').filter(Boolean)
  // /projects/:id/<tab>
  if (segs[2]) return `/projects/${projectId.value}/${segs[2]}`
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
  transition: width 0.2s, transform 0.2s;
}

.project-sidebar--collapsed {
  width: 0 !important;
  overflow: hidden;
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

.project-mobile-burger {
  position: fixed;
  left: 12px;
  bottom: 24px;
  z-index: 100;
}

.project-mobile-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 99;
}

/* 移动端：sidebar 实际宽度为 0 时被遮住，点 burger → 临时打开 drawer */
@media (max-width: 768px) {
  .project-sidebar {
    position: fixed;
    left: 0;
    top: var(--tm-header-height);
    bottom: 0;
    z-index: 100;
    width: 220px !important;
  }
  .project-sidebar--collapsed {
    transform: translateX(-100%);
    width: 220px !important;
  }
  .project-layout__content {
    padding: 12px;
  }
}
</style>
