<template>
  <div class="page-container">
    <div class="page-header">
      <h2>计划详情: {{ plan.name }}</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="showCaseSelector">添加用例</el-button>
      </div>
    </div>
    <el-descriptions :column="2" border style="margin-bottom: 20px">
      <el-descriptions-item label="描述">{{ plan.description || '-' }}</el-descriptions-item>
      <el-descriptions-item label="用例数">{{ plan.plan_cases?.length || 0 }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="statusType(plan.status)">{{ statusLabel(plan.status) }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="日期">{{ plan.start_date || '-' }} ~ {{ plan.end_date || '-' }}</el-descriptions-item>
    </el-descriptions>
    <el-table :data="plan.plan_cases || []" stripe>
      <!-- C13 fix: 空态 -->
      <el-table-column prop="test_case_detail.id" label="用例ID" width="80" />
      <el-table-column prop="test_case_detail.title" label="用例标题" show-overflow-tooltip />
      <el-table-column prop="test_case_detail.priority" label="优先级" width="100" />
      <el-table-column prop="test_case_detail.status" label="状态" width="100">
        <template #default="{ row }">
          {{ row.test_case_detail.status === 'active' ? '活跃' : row.test_case_detail.status }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="handleRemoveCase(row)">移除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="loaded && !(plan.plan_cases || []).length" description="该计划暂无用例，点击「添加用例」加入" :image-size="80" />

    <el-dialog title="选择测试用例" v-model="caseDialogVisible" width="800px">
      <el-input v-model="caseSearch" placeholder="搜索用例标题" style="margin-bottom: 16px" />
      <el-table
        :data="filteredCases"
        @selection-change="handleSelectionChange"
        ref="caseTableRef"
        stripe
        max-height="400"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" show-overflow-tooltip />
        <el-table-column prop="priority" label="优先级" width="100" />
      </el-table>
      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddCases">添加选中</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getTestPlan, addCasesToPlan, removeCaseFromPlan } from '@/api/testplans'
import { getTestCases } from '@/api/testcases'
import { ElMessage } from 'element-plus'

const route = useRoute()
const planId = route.params.pid
const projectId = route.params.id
const plan = ref({})
const loaded = ref(false)   // C13: 区分「还在加载」和「真的空」
const caseDialogVisible = ref(false)
const allCases = ref([])
const caseSearch = ref('')
const selectedCases = ref([])
const caseTableRef = ref(null)

const filteredCases = computed(() => {
  if (!caseSearch.value) return allCases.value
  return allCases.value.filter(c => c.title?.includes(caseSearch.value))
})

function statusLabel(s) {
  const map = { draft: '草稿', active: '执行中', completed: '已完成' }
  return map[s] || s
}
function statusType(s) {
  const map = { draft: 'info', active: 'warning', completed: 'success' }
  return map[s] || 'info'
}

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
  ElMessage.success('添加成功')
  caseDialogVisible.value = false
  fetchPlan()
}

async function handleRemoveCase(row) {
  await removeCaseFromPlan(planId, row.test_case)
  ElMessage.success('移除成功')
  fetchPlan()
}

onMounted(fetchPlan)
</script>
