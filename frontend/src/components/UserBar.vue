<template>
  <div class="user-bar" v-loading="!isLoaded && !!auth.token">
    <el-dropdown v-if="isLoaded" trigger="click" @command="onCommand">
      <div class="user-bar__trigger">
        <el-avatar :size="32" class="user-bar__avatar">{{ avatarLetter }}</el-avatar>
        <div class="user-bar__info">
          <span class="user-bar__name">{{ displayName }}</span>
          <el-tag v-if="roleLabel" :type="roleTagType" size="small" effect="light" class="user-bar__role">
            {{ roleLabel }}
          </el-tag>
        </div>
        <el-icon class="user-bar__arrow"><ArrowDown /></el-icon>
      </div>
      <template #dropdown>
        <el-dropdown-menu class="user-bar__menu">
          <el-dropdown-item disabled>
            <div class="user-bar__panel">
              <div class="user-bar__panel-name">{{ displayName }}</div>
              <div class="user-bar__panel-row">
                <span class="user-bar__panel-label">邮箱</span>
                <span>{{ email || '—' }}</span>
              </div>
              <div class="user-bar__panel-row">
                <span class="user-bar__panel-label">角色</span>
                <el-tag :type="roleTagType" size="small">{{ roleLabel || '—' }}</el-tag>
              </div>
              <div v-if="phone" class="user-bar__panel-row">
                <span class="user-bar__panel-label">手机</span>
                <span>{{ phone }}</span>
              </div>
              <div v-if="userId" class="user-bar__panel-row">
                <span class="user-bar__panel-label">用户 ID</span>
                <span>{{ userId }}</span>
              </div>
            </div>
          </el-dropdown-item>
          <el-dropdown-item divided command="logout">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useUserIdentity } from '@/composables/useUserIdentity'

const auth = useAuthStore()
const {
  displayName,
  roleLabel,
  roleTagType,
  email,
  phone,
  userId,
  avatarLetter,
  isLoaded,
} = useUserIdentity()

function onCommand(cmd) {
  if (cmd === 'logout') auth.logout()
}
</script>

<style scoped>
.user-bar__trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 10px 4px 4px;
  border-radius: var(--tm-radius);
  transition: background 0.15s;
}

.user-bar__trigger:hover {
  background: var(--tm-border-light);
}

.user-bar__avatar {
  background: linear-gradient(135deg, var(--tm-primary), #818cf8);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.user-bar__info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  min-width: 0;
}

.user-bar__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--tm-text);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}

.user-bar__role {
  height: 18px;
  padding: 0 6px;
  font-size: 11px;
}

.user-bar__arrow {
  color: var(--tm-text-muted);
  font-size: 12px;
  flex-shrink: 0;
}

.user-bar__panel {
  padding: 4px 0;
  min-width: 200px;
}

.user-bar__panel-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--tm-text);
  margin-bottom: 10px;
}

.user-bar__panel-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  color: var(--tm-text-secondary);
  margin-bottom: 6px;
}

.user-bar__panel-row:last-child {
  margin-bottom: 0;
}

.user-bar__panel-label {
  color: var(--tm-text-muted);
  flex-shrink: 0;
}
</style>
