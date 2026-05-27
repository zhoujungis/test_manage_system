<template>
  <div class="page-container admin-users-page">
    <div class="page-header">
      <div>
        <h2>用户管理</h2>
        <p class="text-muted page-header__sub">仅管理员可访问，新增或删除用户</p>
      </div>
      <div class="page-header__actions">
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新增用户
        </el-button>
      </div>
    </div>

    <div class="table-card" v-loading="loading">
      <el-table :data="users" stripe>
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="email" label="邮箱" min-width="200" show-overflow-tooltip />
        <el-table-column label="角色" width="130">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">{{ row.role_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.date_joined) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              link
              :disabled="row.id === auth.user?.id || row.role === 'admin'"
              :loading="deletingId === row.id"
              @click="confirmDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && users.length === 0" description="暂无用户" />
    </div>

    <el-dialog v-model="dialogVisible" title="新增用户" width="460px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="user@glazero.com" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="留空则自动使用邮箱前缀" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width:100%">
            <el-option
              v-for="r in roleChoices"
              :key="r.value"
              :label="r.label"
              :value="r.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitCreate">确认创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { createUser, deleteUser, getUserList } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const deletingId = ref(null)
const users = ref([])
const dialogVisible = ref(false)
const formRef = ref(null)

const roleChoices = [
  { value: 'tester', label: '测试工程师' },
  { value: 'developer', label: '测试开发工程师' },
  { value: 'viewer', label: '观察者' },
  { value: 'admin', label: '管理员' },
]

const ROLE_TAG = { tester: 'success', developer: 'warning', viewer: 'info', admin: 'danger' }

const form = reactive({
  email: '',
  username: '',
  password: '',
  role: 'tester',
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

function roleTagType(role) {
  return ROLE_TAG[role] || 'info'
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
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
    ElMessage.success('用户创建成功')
    dialogVisible.value = false
  } finally {
    saving.value = false
  }
}

async function confirmDelete(row) {
  if (row.id === auth.user?.id) {
    ElMessage.warning('不能删除当前登录账号')
    return
  }
  if (row.role === 'admin') {
    ElMessage.warning('不能删除管理员账号')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除用户「${row.username}」？此操作不可恢复。`,
      '删除用户',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  deletingId.value = row.id
  try {
    await deleteUser(row.id)
    users.value = users.value.filter((u) => u.id !== row.id)
    ElMessage.success('用户已删除')
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
