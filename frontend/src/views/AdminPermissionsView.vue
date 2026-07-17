<template>
  <div class="page-container admin-perm-page">
    <div class="page-header">
      <div>
        <h2>{{ t('admin.permissions') }}</h2>
        <p class="text-muted page-header__sub">{{ t('msg.adminOnly') }}</p>
      </div>
      <el-button @click="loadData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        {{ t('common.refresh') }}
      </el-button>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="admin-perm-tip"
      :title="t('common.notice')"
      :description="t('msg.adminOnly')"
    />

    <div class="table-card" v-loading="loading">
      <el-table :data="users" stripe>
        <el-table-column prop="username" :label="t('admin.username')" width="120" />
        <el-table-column prop="email" :label="t('admin.email')" min-width="180" show-overflow-tooltip />
        <el-table-column :label="t('admin.role')" width="130">
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
            <el-icon v-if="row.permissions?.[perm.key]" :style="{ color: 'var(--tm-success)' }" :size="18"><CircleCheck /></el-icon>
            <el-icon v-else :style="{ color: 'var(--tm-text-muted)' }" :size="18"><Close /></el-icon>
          </template>
        </el-table-column>
        <el-table-column :label="t('common.operation')" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEdit(row)">{{ t('common.edit') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && users.length === 0" :description="t('common.noData')" />
    </div>

    <div v-if="admins.length" class="admin-perm-admins">
      <h3 class="admin-perm-admins__title">{{ t('admin.isAdmin') }}</h3>
      <el-space wrap>
        <el-tag v-for="a in admins" :key="a.id" type="danger" effect="plain">
          {{ a.username }} ({{ a.email }})
        </el-tag>
      </el-space>
    </div>

    <el-dialog v-model="dialogVisible" :title="`${t('admin.permissions')} — ${editing?.username}`" width="520px" destroy-on-close>
      <el-form v-if="editing" label-width="100px">
        <el-form-item :label="t('admin.role')">
          <el-select v-model="form.role" style="width:100%" @change="onRoleChange">
            <el-option v-for="r in roleChoices" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.apply_role_defaults">{{ t('msg.adminOnly') }}</el-checkbox>
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
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getAdminPermissionBoard, updateUserPermissions } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { CircleCheck, Close, Refresh } from '@element-plus/icons-vue'

const { t } = useI18n()
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
function roleTagType(role) { return ROLE_TAG[role] || 'info' }

async function loadData() {
  loading.value = true
  try {
    const res = await getAdminPermissionBoard()
    users.value = res.users || []
    admins.value = res.admins || []
    roleChoices.value = res.role_choices || []
    permissionMeta.value = res.permission_meta || []
    roleDefaults.value = res.role_defaults || {}
  } finally { loading.value = false }
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
    const payload = { role: form.role, apply_role_defaults: form.apply_role_defaults }
    if (!form.apply_role_defaults) Object.assign(payload, form.permissions)
    const updated = await updateUserPermissions(editing.value.id, payload)
    const idx = users.value.findIndex((u) => u.id === editing.value.id)
    if (idx >= 0) users.value[idx] = updated
    if (editing.value.id === auth.user?.id) await auth.fetchUser()
    ElMessage.success(t('msg.updateSuccess'))
    dialogVisible.value = false
  } finally { saving.value = false }
}

watch(() => form.apply_role_defaults, (v) => {
  if (v && roleDefaults.value[form.role]) {
    Object.assign(form.permissions, roleDefaults.value[form.role])
  }
})

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