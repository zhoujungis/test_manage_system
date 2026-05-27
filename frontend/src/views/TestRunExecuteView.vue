<template>
  <div class="page-container">
    <div class="page-header">
      <h2>测试执行: {{ run.name }}</h2>
      <div class="page-header__actions">
        <el-tag :type="statusType(run.status)" size="large">{{ statusLabel(run.status) }}</el-tag>
        <el-button v-if="run.status === 'pending'" type="success" @click="handleStart">开始执行</el-button>
        <el-button v-if="run.status === 'running'" type="warning" @click="handleComplete">完成执行</el-button>
      </div>
    </div>
    <el-descriptions :column="2" border style="margin-bottom: 20px">
      <el-descriptions-item label="计划">{{ run.plan_name }}</el-descriptions-item>
      <el-descriptions-item label="执行人">{{ run.created_by_name }}</el-descriptions-item>
    </el-descriptions>
    <el-table :data="run.results || []" stripe>
      <el-table-column type="index" label="#" width="50" />
      <el-table-column prop="test_case_detail.title" label="用例" show-overflow-tooltip />
      <el-table-column prop="test_case_detail.priority" label="优先级" width="80" />
      <el-table-column prop="status" label="结果" width="100">
        <template #default="{ row }">
          <el-tag :type="resultType(row.status)">{{ resultLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <template v-if="run.status === 'running'">
            <el-button size="small" type="success" @click="handleResult(row.id, 'pass')">通过</el-button>
            <el-button size="small" type="danger" @click="handleResult(row.id, 'fail')">失败</el-button>
            <el-button size="small" type="warning" @click="handleResult(row.id, 'blocked')">阻塞</el-button>
            <el-button size="small" type="info" @click="handleResult(row.id, 'skip')">跳过</el-button>
          </template>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getTestRun, startTestRun, completeTestRun, updateTestResult } from '@/api/testruns'
import { ElMessage } from 'element-plus'

const route = useRoute()
const runId = route.params.rid
const run = ref({})

function statusLabel(s) {
  const map = { pending: '待执行', running: '执行中', completed: '已完成' }
  return map[s] || s
}
function statusType(s) {
  const map = { pending: 'info', running: 'warning', completed: 'success' }
  return map[s] || 'info'
}
function resultLabel(s) {
  const map = { pending: '待执行', pass: '通过', fail: '失败', blocked: '阻塞', skip: '跳过' }
  return map[s] || s
}
function resultType(s) {
  const map = { pending: 'info', pass: 'success', fail: 'danger', blocked: 'warning', skip: '' }
  return map[s] || ''
}

async function fetchRun() {
  run.value = await getTestRun(runId)
}

async function handleStart() {
  await startTestRun(runId)
  ElMessage.success('已开始')
  fetchRun()
}

async function handleComplete() {
  await completeTestRun(runId)
  ElMessage.success('已完成')
  fetchRun()
}

async function handleResult(resultId, status) {
  await updateTestResult(runId, { result_id: resultId, status })
  fetchRun()
}

onMounted(fetchRun)
</script>
