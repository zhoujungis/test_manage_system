<template>
  <div class="tasks-panel">
    <div style="margin-bottom:12px">
      <el-button type="primary" size="small" @click="taskDlg.open()">{{ t('project.newTask') }}</el-button>
    </div>
    <el-table :data="tasks" v-loading="loading" stripe size="small">
      <el-table-column prop="title" :label="t('task.title')" show-overflow-tooltip />
      <el-table-column prop="round" :label="t('task.round')" width="100" />
      <el-table-column prop="assigned_to_name" :label="t('task.owner')" width="100" />
      <el-table-column prop="priority" :label="t('task.priority')" width="80">
        <template #default="{ row: r }">
          <el-tag :type="priorityType(r.priority)" size="small">{{ r.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status_label" :label="t('task.status')" width="90">
        <template #default="{ row: r }">
          <el-tag :type="taskStatusType(r.status)" size="small">{{ r.status_label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="due_date" :label="t('task.dueDate')" width="110" />
      <el-table-column :label="t('common.operation')" width="150">
        <template #default="{ row: r }">
          <el-button size="small" @click="taskDlg.open(r)">{{ t('common.edit') }}</el-button>
          <el-button size="small" type="danger" @click="handleDeleteTask(r)">{{ t('common.delete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog :title="taskDlg.editing.value ? t('common.edit') : t('project.newTask')" v-model="taskDlg.visible.value" width="520px" :close-on-click-modal="false">
      <el-form ref="taskDlg.formRef" :model="taskDlg.form" :rules="taskDlg.rules" label-width="80px">
        <el-form-item :label="t('task.title')" prop="title">
          <el-input v-model="taskDlg.form.title" />
        </el-form-item>
        <el-form-item :label="t('project.desc')">
          <el-input v-model="taskDlg.form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item :label="t('task.round')">
          <el-input v-model="taskDlg.form.round" />
        </el-form-item>
        <el-form-item :label="t('task.owner')">
          <el-select v-model="taskDlg.form.assigned_to" filterable style="width:100%">
            <el-option v-for="m in members" :key="m.user" :label="m.user_name" :value="m.user" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('task.priority')">
          <el-select v-model="taskDlg.form.priority" style="width:100%">
            <el-option v-for="key in ['P0','P1','P2','P3','P4']" :key="key" :label="priorityLabel(key)" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('task.status')">
          <el-select v-model="taskDlg.form.status" style="width:100%">
            <el-option v-for="(label, key) in taskStatusLabels" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('task.dueDate')">
          <el-date-picker v-model="taskDlg.form.due_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDlg.close()">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="taskDlg.submitting.value" @click="taskDlg.save()">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTasks, createTask, updateTask, deleteTask, getMembers } from '@/api/projects'
import { useCrudDialog } from '@/composables/useCrudDialog'
import { useFormat } from '@/composables/useFormat'

const { t } = useI18n()
const { priorityType, priorityLabel, taskStatusType } = useFormat()
const taskStatusLabels = computed(() => t('status.assignment'))  // 复用 assignment 的 4 个状态

const props = defineProps({ project: { type: Object, required: true } })
const emit = defineEmits(['change'])

const loading = ref(false)
const tasks = ref([])
const members = ref([])

async function fetchTasks() {
  loading.value = true
  try { tasks.value = await getTasks(props.project.id) } finally { loading.value = false }
}
async function fetchMembers() {
  try {
    const data = await getMembers(props.project.id)
    members.value = data.results || data
  } catch { members.value = [] }
}

onMounted(() => { fetchTasks(); fetchMembers() })
watch(() => props.project.id, () => { fetchTasks(); fetchMembers() })

const taskDlg = useCrudDialog({
  defaults: { title: '', description: '', round: '', assigned_to: null, priority: 'P2', status: 'todo', due_date: null },
  rules: computed(() => ({
    title: [{ required: true, message: t('task.title'), trigger: 'blur' }],
  })).value,
  create: (data) => createTask(props.project.id, data),
  update: (id, data) => updateTask(id, data),
  refresh: fetchTasks,
})

async function handleDeleteTask(row) {
  try {
    await ElMessageBox.confirm(
      `${t('common.delete')}「${row.title}」?`,
      t('common.confirm'),
      { type: 'warning' },
    )
  } catch { return }
  await deleteTask(row.id)
  ElMessage.success(t('msg.deleteSuccess'))
  fetchTasks()
  emit('change')
}
</script>