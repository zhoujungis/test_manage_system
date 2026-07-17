<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('run.list') }}</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="showCreateDialog">{{ t('run.new') }}</el-button>
      </div>
    </div>
    <div class="table-card">
    <el-table :data="runs" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" :label="t('run.name')" show-overflow-tooltip />
      <el-table-column prop="plan_name" :label="t('run.plan')" width="180" />
      <el-table-column :label="t('run.passRate')" width="200">
        <template #default="{ row }">
          <span>{{ row.passed }}/{{ row.total }}</span>
          <el-progress
            :percentage="row.total > 0 ? Math.round(row.passed / row.total * 100) : 0"
            :stroke-width="6"
            style="width: 100px; display: inline-block; margin-left: 8px"
          />
        </template>
      </el-table-column>
      <el-table-column prop="status" :label="t('run.detail')" width="100">
        <template #default="{ row }">
          <el-tag :type="runStatusType(row.status)" size="small">{{ runStatusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('common.operation')" width="250" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="$router.push(`/projects/${projectId}/testruns/${row.id}`)">
            {{ row.status === 'completed' ? t('common.confirm') : t('run.start') }}
          </el-button>
          <el-button size="small" v-if="row.status === 'pending'" type="success" @click="handleStart(row)">{{ t('run.start') }}</el-button>
          <el-button size="small" v-if="row.status === 'running'" type="warning" @click="handleComplete(row)">{{ t('run.complete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && runs.length === 0" :description="t('common.noData')" :image-size="80" />
    </div>

    <el-dialog :title="t('run.new')" v-model="dialogVisible" width="500px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item :label="t('run.name')" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="t('run.plan')" prop="test_plan">
          <el-select v-model="form.test_plan" style="width: 100%">
            <el-option v-for="p in plans" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleCreate">{{ t('common.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { getTestRuns, createTestRun, startTestRun, completeTestRun } from '@/api/testruns'
import { getTestPlans } from '@/api/testplans'
import { ElMessage } from 'element-plus'
import { useFormat } from '@/composables/useFormat'

const { t } = useI18n()
const { runStatusType, runStatusLabel } = useFormat()
const route = useRoute()
const projectId = route.params.id
const planFilter = route.query.plan
const loading = ref(false)
const runs = ref([])
const plans = ref([])
const dialogVisible = ref(false)
const form = reactive({ name: '', test_plan: '' })

const formRef = ref(null)
const rules = computed(() => ({
  name: [{ required: true, message: t('run.name'), trigger: 'blur' }],
  test_plan: [{ required: true, message: t('run.plan'), trigger: 'change' }],
})).value

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
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    await createTestRun({ ...form })
    ElMessage.success(t('msg.createSuccess'))
    dialogVisible.value = false
    fetchData()
  } catch {
    /* 拦截器已 toast */
  }
}

async function handleStart(row) {
  await startTestRun(row.id)
  ElMessage.success(t('run.start'))
  fetchData()
}

async function handleComplete(row) {
  await completeTestRun(row.id)
  ElMessage.success(t('run.complete'))
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>