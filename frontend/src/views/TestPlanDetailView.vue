<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('plan.detail') }}: {{ plan.name }}</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="showCaseSelector">{{ t('plan.addCase') }}</el-button>
      </div>
    </div>
    <el-descriptions :column="2" border style="margin-bottom: 20px">
      <el-descriptions-item :label="t('plan.desc')">{{ plan.description || '-' }}</el-descriptions-item>
      <el-descriptions-item :label="t('plan.caseCount')">{{ plan.plan_cases?.length || 0 }}</el-descriptions-item>
      <el-descriptions-item :label="t('run.detail')">
        <el-tag :type="planStatusType(plan.status)">{{ planStatusLabel(plan.status) }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item :label="t('plan.start')">{{ plan.start_date || '-' }} ~ {{ plan.end_date || '-' }}</el-descriptions-item>
    </el-descriptions>
    <el-table :data="plan.plan_cases || []" stripe>
      <el-table-column prop="test_case_detail.id" label="ID" width="80" />
      <el-table-column prop="test_case_detail.title" :label="t('case.title')" show-overflow-tooltip />
      <el-table-column prop="test_case_detail.priority" :label="t('case.priority')" width="100" />
      <el-table-column prop="test_case_detail.status" :label="t('case.status')" width="100">
        <template #default="{ row }">
          {{ row.test_case_detail.status === 'active' ? t('status.testcase.active') : row.test_case_detail.status }}
        </template>
      </el-table-column>
      <el-table-column :label="t('common.operation')" width="100">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="handleRemoveCase(row)">{{ t('common.delete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="loaded && !(plan.plan_cases || []).length" :description="t('common.noData')" :image-size="80" />

    <el-dialog :title="t('plan.selectCase')" v-model="caseDialogVisible" width="800px" :close-on-click-modal="false">
      <el-input v-model="caseSearch" :placeholder="t('common.search')" style="margin-bottom: 16px" />
      <el-table :data="filteredCases" @selection-change="handleSelectionChange" ref="caseTableRef" stripe max-height="400">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" :label="t('case.title')" show-overflow-tooltip />
        <el-table-column prop="priority" :label="t('case.priority')" width="100" />
      </el-table>
      <template #footer>
        <el-button @click="caseDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddCases">{{ t('plan.addCase') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { getTestPlan, addCasesToPlan, removeCaseFromPlan } from '@/api/testplans'
import { getTestCases } from '@/api/testcases'
import { ElMessage } from 'element-plus'
import { useFormat } from '@/composables/useFormat'

const { t } = useI18n()
const { planStatusType, planStatusLabel } = useFormat()
const route = useRoute()
const planId = route.params.pid
const projectId = route.params.id
const plan = ref({})
const loaded = ref(false)
const caseDialogVisible = ref(false)
const allCases = ref([])
const caseSearch = ref('')
const selectedCases = ref([])
const caseTableRef = ref(null)

const filteredCases = computed(() => {
  if (!caseSearch.value) return allCases.value
  return allCases.value.filter(c => c.title?.includes(caseSearch.value))
})

async function fetchPlan() {
  plan.value = await getTestPlan(planId)
  loaded.value = true
}

async function showCaseSelector() {
  const res = await getTestCases({ project: projectId, status: 'active', all: 1 })
  allCases.value = res.results || res
  caseDialogVisible.value = true
}

function handleSelectionChange(val) {
  selectedCases.value = val
}

async function handleAddCases() {
  const ids = selectedCases.value.map(c => c.id)
  if (ids.length === 0) return
  await addCasesToPlan(planId, ids)
  ElMessage.success(t('msg.createSuccess'))
  caseDialogVisible.value = false
  fetchPlan()
}

async function handleRemoveCase(row) {
  await removeCaseFromPlan(planId, row.test_case)
  ElMessage.success(t('msg.deleteSuccess'))
  fetchPlan()
}

onMounted(fetchPlan)
</script>