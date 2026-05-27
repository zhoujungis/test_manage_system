<template>
  <div class="identity-card page-panel" v-loading="!isLoaded">
    <div class="identity-card__head">
      <el-avatar :size="48" class="identity-card__avatar">{{ avatarLetter }}</el-avatar>
      <div>
        <div class="identity-card__name">{{ displayName }}</div>
        <el-tag v-if="roleLabel" :type="roleTagType" size="small" effect="light">{{ roleLabel }}</el-tag>
      </div>
    </div>
    <el-descriptions :column="2" border size="small" class="identity-card__desc">
      <el-descriptions-item label="用户名">{{ displayName }}</el-descriptions-item>
      <el-descriptions-item label="邮箱">{{ email || '—' }}</el-descriptions-item>
      <el-descriptions-item label="角色">{{ roleLabel || '—' }}</el-descriptions-item>
      <el-descriptions-item label="手机">{{ phone || '—' }}</el-descriptions-item>
      <el-descriptions-item label="用户 ID">{{ userId || '—' }}</el-descriptions-item>
      <el-descriptions-item label="注册时间">{{ joinedAt || '—' }}</el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<script setup>
import { useUserIdentity } from '@/composables/useUserIdentity'

const {
  displayName,
  roleLabel,
  roleTagType,
  email,
  phone,
  userId,
  joinedAt,
  avatarLetter,
  isLoaded,
} = useUserIdentity()
</script>

<style scoped>
.identity-card__head {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.identity-card__avatar {
  background: linear-gradient(135deg, var(--tm-primary), #818cf8);
  color: #fff;
  font-weight: 700;
  font-size: 20px;
}

.identity-card__name {
  font-size: 18px;
  font-weight: 700;
  color: var(--tm-text);
  margin-bottom: 6px;
}

.identity-card__desc {
  margin-top: 4px;
}
</style>
