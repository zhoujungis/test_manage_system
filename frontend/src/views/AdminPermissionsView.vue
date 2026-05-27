<template>
  <div class="page-container admin-perm-page">
    <div class="page-header">
      <div>
        <h2>权限管理</h2>
        <p class="text-muted page-header__sub">仅管理员可访问，配置非管理员账号的功能权限</p>
      </div>
      <el-button @click="loadData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="admin-perm-tip"
      title="说明"
      description="修改后立即生效。切换角色时会自动应用该角色默认权限，也可勾选「应用角色默认权限」手动恢复。观察者默认可浏览各模块，不可新建/编辑。管理员不在此列表。如需删除用户请前往用户管理页面。"
    />

    <div class="table-card" v-loading="loading">
      <el-table :data="users" stripe>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column label="角色" width="130">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">{{ row.role_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          v-for="perm in permissionMeta"
          :key="perm.key"
          :label="perm.label"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-icon v-if="row.permissions?.[perm.key]" color="#10b981" :size="18"><CircleCheck /></el-icon>
            <el-icon v-else color="#cbd5e1" :size="18"><Close /></el-icon>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEdit(row)">配置</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && users.length === 0" description="暂无待配置用户" />
    </div>

    <div v-if="admins.length" class="admin-perm-admins">
      <h3 class="admin-perm-admins__title">系统管理员</h3>
      <el-space wrap>
        <el-tag v-for="a in admins" :key="a.id" type="danger" effect="plain">
          {{ a.username }} ({{ a.email }})
        </el-tag>
      </el-space>
    </div>

    <el-dialog v-model="dialogVisible" :title="`配置权限 — ${editing?.username}`" width="520px" destroy-on-close>
      <el-form v-if="editing" label-width="100px">
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%" @change="onRoleChange">
            <el-option v-for="r in roleChoices" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.apply_role_defaults">应用角色默认权限</el-checkbox>
        </el-form-item>
        <el-divider />
        <el-form-item v-for="perm in permissionMeta" :key="perm.key" :label="perm.label">
          <div class="perm-row">
            <el-switch v-model="form.permissions[perm.key]" :disabled="form.apply_role_defaults" />
            <span class="perm-row__desc">{{ perm.desc }}</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, watch, onMounted } from 'vue'
import { getAdminPermissionBoard, updateUserPermissions } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const users = ref([])
const admins = ref([])
const roleChoices = ref([])
const permissionMeta = ref([])
const roleDefaults = ref({})

const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive({
  role: 'tester',
  apply_role_defaults: false,
  permissions: {
    can_access_projects: true,
    can_access_testcase_library: true,
    can_manage_testcase_library: true,
    can_access_my_projects: true,
  },
})

const ROLE_TAG = { tester: 'success', developer: 'warning', viewer: 'info' }

function roleTagType(role) {
  return ROLE_TAG[role] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    const res = await getAdminPermissionBoard()
    users.value = res.users || []
    admins.value = res.admins || []
    roleChoices.value = res.role_choices || []
    permissionMeta.value = res.permission_meta || []
    roleDefaults.value = res.role_defaults || {}
  } finally {
    loading.value = false
  }
}

function openEdit(row) {
  editing.value = row
  form.role = row.role
  form.apply_role_defaults = false
  Object.assign(form.permissions, { ...row.permissions })
  dialogVisible.value = true
}

function onRoleChange(role) {
  if (form.apply_role_defaults && roleDefaults.value[role]) {
    Object.assign(form.permissions, roleDefaults.value[role])
  }
}

async function saveEdit() {
  if (!editing.value) return
  saving.value = true
  try {
    const payload = {
      role: form.role,
      apply_role_defaults: form.apply_role_defaults,
    }
    if (!form.apply_role_defaults) {
      Object.assign(payload, form.permissions)
    }
    const updated = await updateUserPermissions(editing.value.id, payload)
    const idx = users.value.findIndex((u) => u.id === editing.value.id)
    if (idx >= 0) users.value[idx] = updated
    if (editing.value.id === auth.user?.id) {
      await auth.fetchUser()
    }
    ElMessage.success('权限已更新')
    dialogVisible.value = false
  } finally {
    saving.value = false
  }
}

watch(
  () => form.apply_role_defaults,
  (v) => {
    if (v && roleDefaults.value[form.role]) {
      Object.assign(form.permissions, roleDefaults.value[form.role])
    }
  }
)

onMounted(loadData)
</script>

<style scoped>
.admin-perm-page {
  max-width: 1200px;
}

.admin-perm-tip {
  margin-bottom: 20px;
}

.admin-perm-admins {
  margin-top: 28px;
  padding: 16px 20px;
  background: var(--tm-surface);
  border: 1px solid var(--tm-border);
  border-radius: var(--tm-radius-lg);
}

.admin-perm-admins__title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 12px;
  color: var(--tm-text);
}

.perm-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.perm-row__desc {
  font-size: 12px;
  color: var(--tm-text-muted);
  line-height: 1.4;
}
</style>
