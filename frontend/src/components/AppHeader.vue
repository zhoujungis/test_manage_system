<template>
  <header class="app-header">
    <div class="app-header__brand" @click="router.push('/home')">
      <div class="app-header__logo">
        <el-icon :size="20"><Monitor /></el-icon>
      </div>
      <span class="app-header__title">{{ t('common.appName') }}</span>
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
        {{ t(item.labelKey) }}
      </router-link>
    </nav>

    <div class="app-header__right">
      <!-- I18N-4: 语言切换 -->
      <el-dropdown trigger="click" @command="onLocaleChange" class="app-header__locale">
        <span class="app-header__iconbtn">
          <el-icon><Position /></el-icon>
          <span class="app-header__locale-label">{{ currentLocaleLabel }}</span>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-for="l in SUPPORTED_LOCALES" :key="l" :command="l">
              {{ t(`lang.${l === 'zh-CN' ? 'zh' : 'en'}`) }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- DARK-1: 主题切换 -->
      <el-tooltip :content="t('theme.toggle')" placement="bottom">
        <el-button text circle class="app-header__iconbtn" @click="onToggleTheme">
          <el-icon><component :is="themeIcon" /></el-icon>
        </el-button>
      </el-tooltip>

      <UserBar />
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import UserBar from './UserBar.vue'
import { useUserIdentity } from '@/composables/useUserIdentity'
import { useTheme, THEMES } from '@/composables/useTheme'
import { setLocale, SUPPORTED_LOCALES } from '@/i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { canAccessProjects, canAccessTestCaseLibrary, canAccessMyProjects, isAdmin } = useUserIdentity()
const { theme, toggleTheme } = useTheme()

const themeIcon = computed(() => (theme.value === 'dark' ? 'Moon' : 'Sunny'))
const currentLocaleLabel = computed(() => {
  // 只显示「中 / En」避免 header 太长
  return SUPPORTED_LOCALES.find((l) => l === getCurrentLocaleShort()) || '中'
})
function getCurrentLocaleShort() {
  return (typeof localStorage !== 'undefined' && localStorage.getItem('tm_locale')) || 'zh-CN'
}

function onLocaleChange(locale) {
  setLocale(locale)
}
function onToggleTheme() {
  toggleTheme()
}

const allNavItems = [
  { labelKey: 'menu.home', to: '/home', icon: 'HomeFilled', match: /^\/home$/ },
  { labelKey: 'menu.testcases', to: '/testcases/camera', icon: 'Document', match: /^\/testcases/, show: () => canAccessTestCaseLibrary.value },
  { labelKey: 'menu.projects', to: '/projects', icon: 'FolderOpened', match: /^\/projects/, show: () => canAccessProjects.value },
  { labelKey: 'menu.myProjects', to: '/tm', icon: 'User', match: /^\/tm/, show: () => canAccessMyProjects.value && !isAdmin.value },
  { labelKey: 'menu.adminPermissions', to: '/admin/permissions', icon: 'Setting', match: /^\/admin\/permissions/, show: () => isAdmin.value },
  { labelKey: 'menu.adminUsers', to: '/admin/users', icon: 'UserFilled', match: /^\/admin\/users/, show: () => isAdmin.value },
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
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.app-header__iconbtn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0 6px;
  height: 32px;
  border-radius: var(--tm-radius-sm);
  cursor: pointer;
  color: var(--tm-text-secondary);
  font-size: 13px;
}

.app-header__iconbtn:hover {
  background: var(--tm-surface-2);
  color: var(--tm-text);
}

.app-header__locale-label {
  font-weight: 500;
}

@media (max-width: 768px) {
  .app-header__nav {
    display: none;
  }
}
</style>
