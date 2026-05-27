<template>
  <div class="page-container">
    <div class="page-header">
      <h2>测试计划</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="showDialog()">新建计划</el-button>
      </div>
    </div>
    <div class="table-card">
    <el-table :data="plans" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="计划名称" show-overflow-tooltip />
      <el-table-column prop="case_count" label="用例数" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="开始日期" width="120" />
      <el-table-column prop="end_date" label="结束日期" width="120" />
      <el-table-column prop="created_by_name" label="创建人" width="120" />
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/projects/${projectId}/testplans/${row.id}`)">详情</el-button>
          <el-button size="small" @click="$router.push(`/projects/${projectId}/testruns?plan=${row.id}`)">执行</el-button>
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <el-dialog :title="editing.id ? '编辑计划' : '新建计划'" v-model="dialogVisible" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="状态" v-if="editing.id">
          <el-select v-model="form.status">
            <el-option label="草稿" value="draft" />
            <el-option label="执行中" value="active" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getTestPlans, createTestPlan, updateTestPlan, deleteTestPlan } from '@/api/testplans'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const projectId = route.params.id
const loading = ref(false)
const plans = ref([])
const dialogVisible = ref(false)
const editing = reactive({})
const form = reactive({ name: '', description: '', status: 'draft', start_date: null, end_date: null })

function statusLabel(s) {
  const map = { draft: '草稿', active: '执行中', completed: '已完成' }
  return map[s] || s
}
function statusType(s) {
  const map = { draft: 'info', active: 'warning', completed: 'success' }
  return map[s] || 'info'
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getTestPlans({ project: projectId })
    plans.value = res.results || res
  } finally {
    loading.value = false
  }
}

function showDialog(row) {
  if (row) {
    Object.assign(editing, row)
    form.name = row.name
    form.description = row.description
    form.start_date = row.start_date
    form.end_date = row.end_date
    form.status = row.status
  } else {
    Object.keys(editing).forEach(k => delete editing[k])
    form.name = ''
    form.description = ''
    form.start_date = null
    form.end_date = null
    form.status = 'draft'
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (editing.id) {
    await updateTestPlan(editing.id, form)
    ElMessage.success('更新成功')
  } else {
    await createTestPlan({ ...form, project: projectId })
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  fetchData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除该计划？', '提示', { type: 'warning' })
  await deleteTestPlan(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(fetchData)
</script>
