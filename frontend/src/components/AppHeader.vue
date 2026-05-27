<template>
  <header class="app-header">
    <div class="app-header__brand" @click="router.push('/home')">
      <div class="app-header__logo">
        <el-icon :size="20"><Monitor /></el-icon>
      </div>
      <span class="app-header__title">测试管理系统</span>
    </div>

    <nav class="global-nav app-header__nav">
      <router-link
        v-for="item in visibleNavItems"
        :key="item.to"
        :to="item.to"
        class="global-nav__link"
        :class="{ 'is-active': isNavActive(item) }"
      >
        <el-icon :size="14"><component :is="item.icon" /></el-icon>
        {{ item.label }}
      </router-link>
    </nav>

    <div class="app-header__right">
      <UserBar />
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UserBar from './UserBar.vue'
import { useUserIdentity } from '@/composables/useUserIdentity'

const route = useRoute()
const router = useRouter()
const { canAccessProjects, canAccessTestCaseLibrary, canAccessMyProjects, isAdmin } = useUserIdentity()

const allNavItems = [
  { label: '首页', to: '/home', icon: 'HomeFilled', match: /^\/home$/ },
  { label: '测试用例库', to: '/testcases/camera', icon: 'Document', match: /^\/testcases/, show: () => canAccessTestCaseLibrary.value },
  { label: '项目管理', to: '/projects', icon: 'FolderOpened', match: /^\/projects/, show: () => canAccessProjects.value },
  { label: '我的项目', to: '/tm', icon: 'User', match: /^\/tm/, show: () => canAccessMyProjects.value && !isAdmin.value },
  { label: '权限管理', to: '/admin/permissions', icon: 'Setting', match: /^\/admin\/permissions/, show: () => isAdmin.value },
  { label: '用户管理', to: '/admin/users', icon: 'UserFilled', match: /^\/admin\/users/, show: () => isAdmin.value },
]

const visibleNavItems = computed(() => allNavItems.filter((item) => !item.show || item.show()))

function isNavActive(item) {
  return item.match.test(route.path)
}
</script>

<style scoped>
.app-header {
  height: var(--tm-header-height);
  background: var(--tm-surface);
  border-bottom: 1px solid var(--tm-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  gap: 20px;
  flex-shrink: 0;
  box-shadow: var(--tm-shadow);
  position: sticky;
  top: 0;
  z-index: 100;
}

.app-header__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex-shrink: 0;
}

.app-header__logo {
  width: 36px;
  height: 36px;
  border-radius: var(--tm-radius-sm);
  background: linear-gradient(135deg, var(--tm-primary), #818cf8);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.app-header__title {
  font-size: 16px;
  font-weight: 700;
  color: var(--tm-text);
  letter-spacing: -0.02em;
}

.app-header__nav {
  flex: 1;
  justify-content: center;
  max-width: 520px;
}

.app-header__right {
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .app-header__nav {
    display: none;
  }
}
</style>
