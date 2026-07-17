<template>
  <div class="members-panel">
    <div style="margin-bottom:12px">
      <el-button type="primary" size="small" @click="memberDlg.open()">{{ t('project.addMember') }}</el-button>
    </div>
    <el-table :data="members" v-loading="loading" stripe size="small">
      <el-table-column prop="user_name" :label="t('member.username')" width="150" />
      <el-table-column prop="role_label" :label="t('member.role')" width="150">
        <template #default="{ row: r }">
          <el-tag :type="memberRoleType(r.role)" size="small">{{ r.role_label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="joined_at" :label="t('member.joinedAt')" width="180">
        <template #default="{ row: r }">{{ formatDateTime(r.joined_at) }}</template>
      </el-table-column>
      <el-table-column :label="t('common.operation')">
        <template #default="{ row: r }">
          <el-button size="small" type="danger" @click="handleRemoveMember(r)">{{ t('common.delete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog :title="t('project.addMember')" v-model="memberDlg.visible.value" width="450px" :close-on-click-modal="false">
      <el-form ref="memberDlg.formRef" :model="memberDlg.form" :rules="memberDlg.rules" label-width="80px">
        <el-form-item :label="t('project.selectUser')" prop="user">
          <el-select v-model="memberDlg.form.user" filterable :placeholder="t('common.search')" style="width:100%">
            <el-option v-for="u in userList" :key="u.id" :label="`${u.username} (${u.email})`" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('project.role')" prop="role">
          <el-select v-model="memberDlg.form.role" style="width:100%">
            <el-option v-for="(label, key) in memberRoles" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="memberDlg.close()">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="memberDlg.submitting.value" @click="handleSaveMember">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMembers, addMember, removeMember, getUserList } from '@/api/projects'
import { useCrudDialog } from '@/composables/useCrudDialog'
import { formatDateTime } from '@/utils/dateFormat'

const { t } = useI18n()
const props = defineProps({ project: { type: Object, required: true } })
const emit = defineEmits(['change'])

const loading = ref(false)
const members = ref([])
const userList = ref([])

const memberRoles = computed(() => ({
  leader: t('project.roleLeader'),
  tester: t('project.roleTester'),
  developer: t('project.roleDeveloper'),
}))
const ROLE_TAG = { leader: 'danger', tester: 'success', developer: 'warning' }
function memberRoleType(role) { return ROLE_TAG[role] || 'info' }

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
  try { userList.value = await getUserList() } catch { userList.value = [] }
}

onMounted(() => { fetchMembers(); fetchUserList() })
watch(() => props.project.id, () => fetchMembers())

const memberDlg = useCrudDialog({
  defaults: { user: null, role: 'tester' },
  rules: computed(() => ({
    user: [{ required: true, message: t('project.selectUser'), trigger: 'change' }],
    role: [{ required: true, message: t('project.role'), trigger: 'change' }],
  })).value,
  create: (data) => addMember(props.project.id, data),
  update: () => Promise.reject(new Error('edit member not supported')),
  refresh: fetchMembers,
})

async function handleSaveMember() {
  if (!memberDlg.editing.value) {
    await memberDlg.save()
    emit('change')
  }
}

async function handleRemoveMember(row) {
  try {
    await ElMessageBox.confirm(`${t('common.delete')} ${row.user_name}?`, t('common.confirm'), { type: 'warning' })
  } catch { return }
  await removeMember(props.project.id, row.user)
  ElMessage.success(t('msg.deleteSuccess'))
  fetchMembers()
  emit('change')
}
</script>