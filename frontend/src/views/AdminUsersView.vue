<template>
  <div class="page-container admin-users-page">
    <div class="page-header">
      <div>
        <h2>{{ t('admin.users') }}</h2>
        <p class="text-muted page-header__sub">{{ t('msg.adminOnly') }}</p>
      </div>
      <div class="page-header__actions">
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          {{ t('common.refresh') }}
        </el-button>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          {{ t('admin.create') }}
        </el-button>
      </div>
    </div>

    <div class="table-card" v-loading="loading">
      <el-table :data="users" stripe>
        <el-table-column prop="username" :label="t('admin.username')" width="140" />
        <el-table-column prop="email" :label="t('admin.email')" min-width="200" show-overflow-tooltip />
        <el-table-column :label="t('admin.role')" width="130">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">{{ row.role_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('admin.joined')" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.date_joined) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('common.operation')" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              link
              :disabled="row.id === auth.user?.id || row.role === 'admin'"
              :loading="deletingId === row.id"
              @click="confirmDelete(row)"
            >
              {{ t('common.delete') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && users.length === 0" :description="t('common.noData')" />
    </div>

    <el-dialog v-model="dialogVisible" :title="t('admin.create')" width="460px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item :label="t('admin.email')" prop="email">
          <el-input v-model="form.email" placeholder="user@glazero.com" />
        </el-form-item>
        <el-form-item :label="t('admin.username')" prop="username">
          <el-input v-model="form.username" :placeholder="t('admin.username')" />
        </el-form-item>
        <el-form-item :label="t('member.role')" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('admin.role')" prop="role">
          <el-select v-model="form.role" style="width:100%">
            <el-option
              v-for="(label, key) in roleLabels"
              :key="key"
              :label="label"
              :value="key === 'admin' ? 'admin' : key"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="submitCreate">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { createUser, deleteUser, getUserList } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTime } from '@/utils/dateFormat'

const { t } = useI18n()
const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const deletingId = ref(null)
const users = ref([])
const dialogVisible = ref(false)
const formRef = ref(null)

const roleLabels = computed(() => t('admin.roleLabels'))

const ROLE_TAG = { tester: 'success', developer: 'warning', viewer: 'info', admin: 'danger' }

const form = reactive({ email: '', username: '', password: '', role: 'tester' })

const rules = computed(() => ({
  email: [
    { required: true, message: t('admin.email'), trigger: 'blur' },
    { type: 'email', message: t('admin.email'), trigger: 'blur' },
  ],
  password: [
    { required: true, message: t('admin.email'), trigger: 'blur' },
    { min: 6, message: t('admin.email'), trigger: 'blur' },
  ],
  role: [{ required: true, message: t('admin.role'), trigger: 'change' }],
})).value

function roleTagType(role) {
  return ROLE_TAG[role] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    users.value = await getUserList()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.email = ''
  form.username = ''
  form.password = ''
  form.role = 'tester'
  dialogVisible.value = true
}

async function submitCreate() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const user = await createUser({
      email: form.email,
      username: form.username || undefined,
      password: form.password,
      role: form.role,
    })
    users.value.unshift(user)
    ElMessage.success(t('msg.createSuccess'))
    dialogVisible.value = false
  } finally {
    saving.value = false
  }
}

async function confirmDelete(row) {
  if (row.id === auth.user?.id) {
    ElMessage.warning(t('admin.cantDeleteSelf'))
    return
  }
  if (row.role === 'admin') {
    ElMessage.warning(t('admin.cantDeleteAdmin'))
    return
  }
  try {
    await ElMessageBox.confirm(
      `${t('common.delete')}「${row.username}」?`,
      t('admin.delete'),
      { type: 'warning', confirmButtonText: t('common.delete'), cancelButtonText: t('common.cancel') },
    )
  } catch { return }
  deletingId.value = row.id
  try {
    await deleteUser(row.id)
    users.value = users.value.filter((u) => u.id !== row.id)
    ElMessage.success(t('msg.deleteSuccess'))
  } finally {
    deletingId.value = null
  }
}

onMounted(loadData)
</script>

<style scoped>
.admin-users-page {
  max-width: 1000px;
}
.page-header__actions {
  display: flex;
  gap: 10px;
}
</style>