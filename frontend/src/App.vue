<template>
  <!-- M22 fix: 组件渲染错误兜底。Suspense + 自定义 error slot 给用户友好提示。 -->
  <router-view v-slot="{ Component, error }">
    <Suspense>
      <component :is="Component" v-if="!error" />
      <template #fallback>
        <div class="app-error-fallback">
          <el-result icon="warning" title="页面加载失败" sub-title="组件渲染异常，请刷新或返回首页">
            <template #extra>
              <el-button type="primary" @click="$router.push('/home')">返回首页</el-button>
              <el-button @click="reload">重新加载</el-button>
            </template>
          </el-result>
        </div>
      </template>
    </Suspense>
    <div v-if="error" class="app-error-fallback">
      <el-result icon="error" :title="error?.message || '未知错误'" sub-title="组件渲染抛出异常">
        <template #extra>
          <el-button type="primary" @click="$router.push('/home')">返回首页</el-button>
        </template>
      </el-result>
    </div>
  </router-view>
</template>

<script setup>
function reload() {
  window.location.reload()
}
</script>

<style scoped>
.app-error-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--tm-header-height));
  padding: 40px;
}
</style>