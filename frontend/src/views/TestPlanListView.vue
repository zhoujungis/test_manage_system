<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('plan.list') }}</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="showDialog()">{{ t('plan.list') }} / +</el-button>
      </div>
    </div>
    <div class="table-card">
    <el-table :data="plans" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" :label="t('plan.name')" show-overflow-tooltip />
      <el-table-column prop="case_count" :label="t('plan.caseCount')" width="100" />
      <el-table-column prop="status" :label="t('plan.detail') ? '' : ''" width="100">
        <template #default="{ row }">
          <el-tag :type="planStatusType(row.status)" size="small">{{ planStatusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="start_date" :label="t('plan.start')" width="120" />
      <el-table-column prop="end_date" :label="t('plan.end')" width="120" />
      <el-table-column prop="created_by_name" :label="t('case.creator')" width="120" />
      <el-table-column :label="t('common.operation')" width="300" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/projects/${projectId}/testplans/${row.id}`)">{{ t('plan.detail') }}</el-button>
          <el-button size="small" @click="$router.push(`/projects/${projectId}/testruns?plan=${row.id}`)">{{ t('run.list') }}</el-button>
          <el-button size="small" @click="showDialog(row)">{{ t('common.edit') }}</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && plans.length === 0" :description="t('common.noData')" :image-size="80" />
    </div>

    <el-dialog :title="editing.id ? t('common.edit') : t('plan.list') + ' / +'" v-model="dialogVisible" width="500px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item :label="t('plan.name')" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="t('plan.desc')">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item :label="t('plan.start')" prop="start_date">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item :label="t('plan.end')" prop="end_date">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item :label="t('run.list')" v-if="editing.id">
          <el-select v-model="form.status">
            <el-option v-for="(label, key) in planStatusLabels" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSave">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { getTestPlans, createTestPlan, updateTestPlan, deleteTestPlan } from '@/api/testplans'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFormat } from '@/composables/useFormat'

const { t } = useI18n()
const { planStatusType, planStatusLabel } = useFormat()
const planStatusLabels = computed(() => t('status.plan'))

const route = useRoute()
const projectId = route.params.id
const loading = ref(false)
const plans = ref([])
const dialogVisible = ref(false)
const editing = reactive({})
const form = reactive({ name: '', description: '', status: 'draft', start_date: null, end_date: null })

const formRef = ref(null)
const rules = computed(() => ({
  name: [{ required: true, message: t('plan.name'), trigger: 'blur' }],
  end_date: [{
    validator: (rule, value, cb) => {
      if (value && form.start_date && value < form.start_date) {
        return cb(new Error(`${t('plan.end')} ≥ ${t('plan.start')}`))
      }
      cb()
    },
    trigger: 'change',
  }],
})).value

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
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (editing.id) {
      await updateTestPlan(editing.id, form)
      ElMessage.success(t('msg.updateSuccess'))
    } else {
      await createTestPlan({ ...form, project: projectId })
      ElMessage.success(t('msg.createSuccess'))
    }
    dialogVisible.value = false
    fetchData()
  } catch {
    /* 拦截器已 toast */
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `${t('common.delete')}「${row.name}」？${row.case_count ?? 0} ${t('plan.caseCount')}`,
      t('common.confirm'),
      { type: 'warning' },
    )
  } catch { return }
  await deleteTestPlan(row.id)
  ElMessage.success(t('msg.deleteSuccess'))
  fetchData()
}

onMounted(fetchData)
</script>