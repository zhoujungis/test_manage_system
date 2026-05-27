<template>
  <div class="page-container">
    <div class="page-header">
      <h2>测试执行</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="showCreateDialog">新建测试执行</el-button>
      </div>
    </div>
    <div class="table-card">
    <el-table :data="runs" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="执行名称" show-overflow-tooltip />
      <el-table-column prop="plan_name" label="所属计划" width="180" />
      <el-table-column label="通过率" width="200">
        <template #default="{ row }">
          <span>{{ row.passed }}/{{ row.total }}</span>
          <el-progress
            :percentage="row.total > 0 ? Math.round(row.passed / row.total * 100) : 0"
            :stroke-width="6"
            style="width: 100px; display: inline-block; margin-left: 8px"
          />
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="$router.push(`/projects/${projectId}/testruns/${row.id}`)">
            {{ row.status === 'completed' ? '查看' : '执行' }}
          </el-button>
          <el-button size="small" v-if="row.status === 'pending'" type="success" @click="handleStart(row)">开始</el-button>
          <el-button size="small" v-if="row.status === 'running'" type="warning" @click="handleComplete(row)">完成</el-button>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <el-dialog title="新建测试执行" v-model="dialogVisible" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="执行名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="所属计划" required>
          <el-select v-model="form.test_plan" style="width: 100%">
            <el-option v-for="p in plans" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getTestRuns, createTestRun, startTestRun, completeTestRun } from '@/api/testruns'
import { getTestPlans } from '@/api/testplans'
import { ElMessage } from 'element-plus'

const route = useRoute()
const projectId = route.params.id
const planFilter = route.query.plan
const loading = ref(false)
const runs = ref([])
const plans = ref([])
const dialogVisible = ref(false)
const form = reactive({ name: '', test_plan: '' })

function statusLabel(s) {
  const map = { pending: '待执行', running: '执行中', completed: '已完成' }
  return map[s] || s
}
function statusType(s) {
  const map = { pending: 'info', running: 'warning', completed: 'success' }
  return map[s] || 'info'
}

async function fetchData() {
  loading.value = true
  try {
    const params = { project: projectId }
    if (planFilter) params.plan = planFilter
    const res = await getTestRuns(params)
    runs.value = res.results || res
  } finally {
    loading.value = false
  }
}

async function showCreateDialog() {
  const res = await getTestPlans({ project: projectId })
  plans.value = res.results || res
  if (planFilter) form.test_plan = planFilter
  form.name = ''
  dialogVisible.value = true
}

async function handleCreate() {
  await createTestRun({ ...form })
  ElMessage.success('创建成功，已自动关联计划中的用例')
  dialogVisible.value = false
  fetchData()
}

async function handleStart(row) {
  await startTestRun(row.id)
  ElMessage.success('测试已开始')
  fetchData()
}

async function handleComplete(row) {
  await completeTestRun(row.id)
  ElMessage.success('测试已完成')
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>
