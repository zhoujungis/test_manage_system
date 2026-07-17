<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('run.detail') }}: {{ run.name }}</h2>
      <div class="page-header__actions">
        <el-tag :type="runStatusType(run.status)" size="large">{{ runStatusLabel(run.status) }}</el-tag>
        <el-button v-if="run.status === 'pending'" type="success" @click="handleStart">{{ t('run.startAction') }}</el-button>
        <el-button v-if="run.status === 'running'" type="warning" @click="handleComplete">{{ t('run.completeAction') }}</el-button>
      </div>
    </div>
    <el-descriptions :column="2" border style="margin-bottom: 20px">
      <el-descriptions-item :label="t('run.plan')">{{ run.plan_name }}</el-descriptions-item>
      <el-descriptions-item :label="t('case.creator')">{{ run.created_by_name }}</el-descriptions-item>
    </el-descriptions>
    <el-table :data="run.results || []" stripe>
      <el-table-column type="index" label="#" width="50" />
      <el-table-column prop="test_case_detail.title" :label="t('case.title')" show-overflow-tooltip />
      <el-table-column prop="test_case_detail.priority" :label="t('case.priority')" width="80" />
      <el-table-column prop="status" :label="t('run.passRate')" width="100">
        <template #default="{ row }">
          <el-tag :type="resultType(row.status)">{{ resultLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('common.operation')" width="250" fixed="right">
        <template #default="{ row }">
          <template v-if="run.status === 'running'">
            <el-button size="small" type="success" @click="handleResult(row.id, 'pass')">{{ t('execute.passed') }}</el-button>
            <el-button size="small" type="danger" @click="handleResult(row.id, 'fail')">{{ t('execute.failed') }}</el-button>
            <el-button size="small" type="warning" @click="handleResult(row.id, 'blocked')">{{ t('execute.blocked') }}</el-button>
            <el-button size="small" type="info" @click="handleResult(row.id, 'skip')">{{ t('execute.skipped') }}</el-button>
          </template>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="loaded && !(run.results || []).length" :description="t('common.noData')" :image-size="80" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { getTestRun, startTestRun, completeTestRun, updateTestResult } from '@/api/testruns'
import { ElMessage } from 'element-plus'
import { useFormat } from '@/composables/useFormat'

const { t } = useI18n()
const { runStatusType, runStatusLabel } = useFormat()
const route = useRoute()
const runId = route.params.rid
const run = ref({})
const loaded = ref(false)

const RESULT_TAG = { pending: 'info', pass: 'success', fail: 'danger', blocked: 'warning', skip: '' }
function resultType(s) { return RESULT_TAG[s] || '' }
function resultLabel(s) { return t(`execute.${s === 'pass' ? 'passed' : s === 'fail' ? 'failed' : s === 'pending' ? 'todo' : s}`) || s }

async function fetchRun() {
  run.value = await getTestRun(runId)
  loaded.value = true
}

async function handleStart() {
  await startTestRun(runId)
  ElMessage.success(t('run.start'))
  fetchRun()
}

async function handleComplete() {
  await completeTestRun(runId)
  ElMessage.success(t('run.complete'))
  fetchRun()
}

async function handleResult(resultId, status) {
  await updateTestResult(runId, { result_id: resultId, status })
  await fetchRun()
  const results = run.value.results || []
  const allDone = results.length > 0 && results.every((r) => r.status && r.status !== 'pending')
  if (allDone && run.value.status === 'running') {
    ElMessage.info(t('run.autoCompleteHint'))
  }
}

onMounted(fetchRun)
</script>