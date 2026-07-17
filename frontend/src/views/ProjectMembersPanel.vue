<template>
  <div class="members-panel">
    <div style="margin-bottom:12px">
      <el-button type="primary" size="small" @click="memberDlg.open()">添加成员</el-button>
    </div>
    <el-table :data="members" v-loading="loading" stripe size="small">
      <el-table-column prop="user_name" label="用户名" width="150" />
      <el-table-column prop="role_label" label="角色" width="150">
        <template #default="{ row: r }">
          <el-tag :type="r.role === 'leader' ? 'danger' : r.role === 'tester' ? 'success' : 'warning'" size="small">{{ r.role_label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="joined_at" label="加入时间" width="180">
        <template #default="{ row: r }">{{ formatDateTime(r.joined_at) }}</template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="{ row: r }">
          <el-button size="small" type="danger" @click="handleRemoveMember(r)">移除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog :title="memberDlg.editing.value ? '编辑成员' : '添加成员'" v-model="memberDlg.visible.value" width="450px" :close-on-click-modal="false">
      <el-form ref="memberDlg.formRef" :model="memberDlg.form" :rules="memberDlg.rules" label-width="80px">
        <el-form-item label="选择用户" prop="user">
          <el-select v-model="memberDlg.form.user" filterable placeholder="搜索用户" style="width:100%">
            <el-option v-for="u in userList" :key="u.id" :label="`${u.username} (${u.email})`" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="memberDlg.form.role" style="width:100%">
            <el-option label="项目负责人" value="leader" />
            <el-option label="测试人员" value="tester" />
            <el-option label="开发人员" value="developer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="memberDlg.close()">取消</el-button>
        <el-button type="primary" :loading="memberDlg.submitting.value" @click="handleSaveMember">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMembers, addMember, removeMember, getUserList } from '@/api/projects'
import { useCrudDialog } from '@/composables/useCrudDialog'
import { formatDateTime } from '@/utils/dateFormat'

const props = defineProps({ project: { type: Object, required: true } })
const emit = defineEmits(['change'])

const loading = ref(false)
const members = ref([])
const userList = ref([])

async function fetchMembers() {
  loading.value = true
  try {
    const data = await getMembers(props.project.id)
    members.value = data.results || data
  } finally {
    loading.value = false
  }
}

async function fetchUserList() {
  try {
    userList.value = await getUserList()
  } catch {
    userList.value = []
  }
}

onMounted(() => {
  fetchMembers()
  fetchUserList()
})
watch(() => props.project.id, () => fetchMembers())

const memberDlg = useCrudDialog({
  defaults: { user: null, role: 'tester' },
  rules: {
    user: [{ required: true, message: '请选择用户', trigger: 'change' }],
    role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  },
  create: (data) => addMember(props.project.id, data),
  update: (id, data) => Promise.reject(new Error('编辑成员请使用移除+添加')),
  refresh: fetchMembers,
})

async function handleSaveMember() {
  // 新建走 create
  if (!memberDlg.editing.value) {
    await memberDlg.save()
    emit('change')
  }
}

async function handleRemoveMember(row) {
  try {
    await ElMessageBox.confirm(`确定移除 ${row.user_name}？`, '删除确认', { type: 'warning' })
  } catch { return }
  await removeMember(props.project.id, row.user)
  ElMessage.success('已移除')
  fetchMembers()
  emit('change')
}
</script>