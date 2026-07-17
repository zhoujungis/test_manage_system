<template>
  <div class="tasks-panel">
    <div style="margin-bottom:12px">
      <el-button type="primary" size="small" @click="taskDlg.open()">新建任务</el-button>
    </div>
    <el-table :data="tasks" v-loading="loading" stripe size="small">
      <el-table-column prop="title" label="任务名称" show-overflow-tooltip />
      <el-table-column prop="round" label="轮次" width="100" />
      <el-table-column prop="assigned_to_name" label="负责人" width="100" />
      <el-table-column prop="priority" label="优先级" width="80">
        <template #default="{ row: r }">
          <el-tag :type="priorityType(r.priority)" size="small">{{ r.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status_label" label="状态" width="90">
        <template #default="{ row: r }">
          <el-tag :type="taskStatusType(r.status)" size="small">{{ r.status_label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="due_date" label="截止日期" width="110" />
      <el-table-column label="操作" width="150">
        <template #default="{ row: r }">
          <el-button size="small" @click="taskDlg.open(r)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDeleteTask(r)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog :title="taskDlg.editing.value ? '编辑任务' : '新建任务'" v-model="taskDlg.visible.value" width="520px" :close-on-click-modal="false">
      <el-form ref="taskDlg.formRef" :model="taskDlg.form" :rules="taskDlg.rules" label-width="80px">
        <el-form-item label="任务名称" prop="title">
          <el-input v-model="taskDlg.form.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="taskDlg.form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="轮次">
          <el-input v-model="taskDlg.form.round" placeholder="如：第一轮、回归测试" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="taskDlg.form.assigned_to" filterable style="width:100%">
            <el-option v-for="m in members" :key="m.user" :label="m.user_name" :value="m.user" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="taskDlg.form.priority" style="width:100%">
            <el-option label="P0-紧急" value="P0" />
            <el-option label="P1-高" value="P1" />
            <el-option label="P2-中" value="P2" />
            <el-option label="P3-低" value="P3" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="taskDlg.form.status" style="width:100%">
            <el-option label="待开始" value="todo" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="done" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="taskDlg.form.due_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDlg.close()">取消</el-button>
        <el-button type="primary" :loading="taskDlg.submitting.value" @click="taskDlg.save()">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTasks, createTask, updateTask, deleteTask, getMembers } from '@/api/projects'
import { useCrudDialog } from '@/composables/useCrudDialog'
import { useFormat } from '@/composables/useFormat'

const props = defineProps({ project: { type: Object, required: true } })
const emit = defineEmits(['change'])

const { priorityType, taskStatusType } = useFormat()

const loading = ref(false)
const tasks = ref([])
const members = ref([])

async function fetchTasks() {
  loading.value = true
  try {
    tasks.value = await getTasks(props.project.id)
  } finally {
    loading.value = false
  }
}

async function fetchMembers() {
  try {
    const data = await getMembers(props.project.id)
    members.value = data.results || data
  } catch {
    members.value = []
  }
}

onMounted(() => {
  fetchTasks()
  fetchMembers()
})
watch(() => props.project.id, () => {
  fetchTasks()
  fetchMembers()
})

const taskDlg = useCrudDialog({
  defaults: { title: '', description: '', round: '', assigned_to: null, priority: 'P2', status: 'todo', due_date: null },
  rules: { title: [{ required: true, message: '请输入任务名称', trigger: 'blur' }] },
  create: (data) => createTask(props.project.id, data),
  update: (id, data) => updateTask(id, data),
  refresh: fetchTasks,
})

async function handleDeleteTask(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除任务「${row.title}」？该任务下的所有用例分配将被一并删除。`,
      '删除确认',
      { type: 'warning' },
    )
  } catch { return }
  await deleteTask(row.id)
  ElMessage.success('已删除')
  fetchTasks()
  emit('change')
}
</script>