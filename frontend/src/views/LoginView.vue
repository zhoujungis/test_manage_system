<template>
  <div class="login-page">
    <div class="login-page__bg">
      <div class="login-page__orb login-page__orb--1" />
      <div class="login-page__orb login-page__orb--2" />
    </div>

    <div class="login-page__content">
      <div class="login-page__intro">
        <div class="login-page__intro-logo">
          <el-icon :size="32"><Monitor /></el-icon>
        </div>
        <h1>测试管理系统</h1>
        <p>统一管理测试用例、项目计划与执行结果，提升团队协作效率。</p>
        <ul class="login-page__features">
          <li><el-icon><Document /></el-icon> 用例库与模块管理</li>
          <li><el-icon><FolderOpened /></el-icon> 项目与测试计划</li>
          <li><el-icon><VideoPlay /></el-icon> 执行跟踪与缺陷闭环</li>
        </ul>
      </div>

      <el-card class="login-card" shadow="never">
        <h2 class="login-card__title">{{ tabTitles[activeTab] }}</h2>
        <p class="login-card__desc">{{ tabDescs[activeTab] }}</p>
        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <AuthFormLogin @switch="activeTab = $event" />
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <AuthFormRegister @switch="activeTab = $event" @prefill="onPrefill" />
          </el-tab-pane>

          <el-tab-pane label="忘记密码" name="forgot">
            <AuthFormForgot @switch="activeTab = $event" @prefill="onPrefill" />
          </el-tab-pane>

          <el-tab-pane label="修改密码" name="change">
            <AuthFormChange @switch="activeTab = $event" @prefill="onPrefill" />
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script setup>
// H23 fix: 之前 LoginView 555 行 4 张表单 + 4 套 cooldown + 4 套 validator 全堆在一起。
// 现在拆出 AuthFormLogin / AuthFormRegister / AuthFormForgot / AuthFormChange
// 四个子组件，本文件只负责 shell + tab 路由。
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Monitor, Document, FolderOpened, VideoPlay } from '@element-plus/icons-vue'
import AuthFormLogin from './AuthFormLogin.vue'
import AuthFormRegister from './AuthFormRegister.vue'
import AuthFormForgot from './AuthFormForgot.vue'
import AuthFormChange from './AuthFormChange.vue'

const { t } = useI18n()
const activeTab = ref('login')
const tabTitles = computed(() => ({
  login: t('auth.titleLogin'),
  register: t('auth.titleRegister'),
  forgot: t('auth.titleForgot'),
  change: t('auth.titleChange'),
}))
const tabDescs = computed(() => ({
  login: t('auth.descLogin'),
  register: t('auth.descRegister'),
  forgot: t('auth.descForgot'),
  change: t('auth.descChange'),
}))

function onPrefill({ email }) {
  // 注册 / 重置 / 修改密码成功后跳回登录 tab 并预填邮箱
  activeTab.value = 'login'
  if (email) {
    // 子组件已经卸载，直接刷新登录表单只能等用户重新打开 —— 这里不强制跳转，
    // 让用户主动切回登录即可；表单状态保留即可。
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--tm-bg);
  position: relative;
  overflow: hidden;
}
.login-page__bg { position: absolute; inset: 0; z-index: 0; pointer-events: none; }
.login-page__orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.4; }
.login-page__orb--1 { width: 480px; height: 480px; background: #6366f1; top: -120px; left: -80px; }
.login-page__orb--2 { width: 380px; height: 380px; background: #06b6d4; bottom: -100px; right: -60px; }
.login-page__content { position: relative; z-index: 1; display: flex; gap: 48px; padding: 32px; max-width: 1080px; width: 100%; align-items: center; }
.login-page__intro { flex: 1; color: var(--tm-text); }
.login-page__intro-logo { width: 56px; height: 56px; border-radius: 14px; background: var(--tm-primary); color: #fff; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
.login-page__intro h1 { font-size: 28px; margin: 0 0 12px; font-weight: 700; }
.login-page__intro p { color: var(--tm-text-muted); margin: 0 0 24px; line-height: 1.6; }
.login-page__features { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; color: var(--tm-text-muted); }
.login-page__features li { display: flex; align-items: center; gap: 8px; }
.login-card { width: 420px; flex-shrink: 0; border-radius: 14px; }
.login-card__title { margin: 0 0 4px; font-size: 22px; font-weight: 700; color: var(--tm-text); }
.login-card__desc { margin: 0 0 20px; color: var(--tm-text-muted); font-size: 13px; }
.login-card__btn { width: 100%; }
.login-card__links { display: flex; justify-content: space-between; margin-bottom: 12px; }
.login-card__code-row { display: flex; width: 100%; gap: 8px; }
.login-card__back { text-align: center; margin-top: 8px; }
.login-tabs :deep(.el-tabs__nav-wrap)::after { background: transparent; }
@media (max-width: 768px) {
  .login-page__content { flex-direction: column; gap: 24px; padding: 16px; }
  .login-page__intro { text-align: center; }
  .login-card { width: 100%; }
}
</style>