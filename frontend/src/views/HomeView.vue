<template>
  <div class="page-container home-page">
    <UserIdentityCard />

    <div class="home-section">
      <h2 class="home-section__title">功能入口</h2>
      <p class="text-muted home-section__sub">{{ sectionSub }}</p>
    </div>

    <div class="home-grid">
      <router-link
        v-for="card in modules"
        :key="card.to"
        :to="card.to"
        class="home-card"
      >
        <div class="home-card__icon" :style="{ background: card.gradient }">
          <el-icon :size="28"><component :is="card.icon" /></el-icon>
        </div>
        <div class="home-card__body">
          <h3>{{ card.title }}</h3>
          <p>{{ card.desc }}</p>
        </div>
        <el-icon class="home-card__arrow"><ArrowRight /></el-icon>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import UserIdentityCard from '@/components/UserIdentityCard.vue'
import { useUserIdentity } from '@/composables/useUserIdentity'

const auth = useAuthStore()
const { canAccessProjects, canAccessTestCaseLibrary, canAccessMyProjects, isAdmin } = useUserIdentity()

onMounted(() => {
  if (auth.token && !auth.user) auth.fetchUser()
})

const allModules = [
  {
    title: '测试用例库',
    desc: '按产品线管理摄像头、门铃等通用测试用例',
    to: '/testcases/camera',
    icon: 'Document',
    gradient: 'linear-gradient(135deg, #4f6ef7, #818cf8)',
    show: () => canAccessTestCaseLibrary.value,
  },
  {
    title: '项目管理',
    desc: '创建项目，管理模块、计划、执行与缺陷',
    to: '/projects',
    icon: 'FolderOpened',
    gradient: 'linear-gradient(135deg, #10b981, #34d399)',
    show: () => canAccessProjects.value,
  },
  {
    title: '我的项目',
    desc: '查看参与的项目并执行分配的测试任务',
    to: '/tm',
    icon: 'User',
    gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
    show: () => canAccessMyProjects.value,
  },
  {
    title: '权限管理',
    desc: '配置非管理员用户的功能访问权限',
    to: '/admin/permissions',
    icon: 'Setting',
    gradient: 'linear-gradient(135deg, #ef4444, #f87171)',
    show: () => isAdmin.value,
  },
]

const modules = computed(() => allModules.filter((m) => m.show()))

const sectionSub = computed(() => '选择模块进入对应功能')
</script>

<style scoped>
.home-page {
  max-width: 960px;
}

.home-page .identity-card {
  margin-bottom: 28px;
}

.home-section {
  margin-bottom: 16px;
}

.home-section__title {
  font-size: 18px;
  font-weight: 600;
  color: var(--tm-text);
  margin-bottom: 4px;
}

.home-section__sub {
  font-size: 14px;
}

.home-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.home-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  background: var(--tm-surface);
  border: 1px solid var(--tm-border);
  border-radius: var(--tm-radius-lg);
  box-shadow: var(--tm-shadow);
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}

.home-card:hover {
  border-color: var(--tm-primary);
  box-shadow: var(--tm-shadow-md);
  transform: translateY(-2px);
}

.home-card__icon {
  width: 56px;
  height: 56px;
  border-radius: var(--tm-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.home-card__body {
  flex: 1;
  min-width: 0;
}

.home-card__body h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--tm-text);
  margin-bottom: 6px;
}

.home-card__body p {
  font-size: 14px;
  color: var(--tm-text-secondary);
  line-height: 1.5;
}

.home-card__arrow {
  color: var(--tm-text-muted);
  flex-shrink: 0;
  transition: color 0.2s, transform 0.2s;
}

.home-card:hover .home-card__arrow {
  color: var(--tm-primary);
  transform: translateX(4px);
}
</style>
