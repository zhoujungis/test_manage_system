<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('case.list') }}</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="$router.push(`/projects/${projectId}/testcases/new`)">{{ t('case.new') }}</el-button>
      </div>
    </div>
    <div class="filter-card">
      <el-row :gutter="16">
        <el-col :span="4">
          <el-input v-model="searchText" :placeholder="t('case.title')" clearable />
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.module" :placeholder="t('case.module')" clearable @change="fetchData">
            <el-option v-for="m in modules" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.status" :placeholder="t('case.status')" clearable @change="onFilterChange">
            <el-option v-for="(label, key) in statusLabels" :key="key" :label="label" :value="key" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.priority" :placeholder="t('case.priority')" clearable @change="onFilterChange">
            <el-option v-for="key in ['P0','P1','P2','P3','P4']" :key="key" :label="priorityLabel(key)" :value="key" />
          </el-select>
        </el-col>
      </el-row>
    </div>
    <div class="table-card">
    <el-table :data="testcases" v-loading="loading" stripe @row-click="(row) => $router.push(`/projects/${projectId}/testcases/${row.id}`)" style="cursor: pointer">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" :label="t('case.title')" show-overflow-tooltip />
      <el-table-column prop="module_name" :label="t('case.module')" width="120" />
      <el-table-column prop="priority" :label="t('case.priority')" width="100">
        <template #default="{ row }">
          <el-tag :type="priorityType(row.priority)" size="small">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="case_type" :label="t('case.type')" width="100">
        <template #default="{ row }">{{ typeLabel(row.case_type) }}</template>
      </el-table-column>
      <el-table-column prop="status" :label="t('case.status')" width="90">
        <template #default="{ row }">
          <el-tag :type="testCaseStatusType(row.status)" size="small">{{ testCaseStatusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_by_name" :label="t('case.creator')" width="120" />
      <el-table-column prop="created_at" :label="t('case.createdAt')" width="170">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column :label="t('common.operation')" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click.stop="$router.push(`/projects/${projectId}/testcases/${row.id}`)">{{ t('common.edit') }}</el-button>
          <el-button size="small" type="danger" @click.stop="handleDelete(row)">{{ t('common.delete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    </div>
    <el-pagination
      v-if="total > 20"
      class="table-pagination"
      background
      layout="total, prev, pager, next"
      :total="total"
      :page-size="20"
      v-model:current-page="page"
      @current-change="fetchData"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { getTestCases, deleteTestCase } from '@/api/testcases'
import { getModules } from '@/api/projects'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useDebounce } from '@/composables/useDebounce'
import { useFormat } from '@/composables/useFormat'
import { formatDateTime } from '@/utils/dateFormat'

const { t } = useI18n()
const { priorityType, priorityLabel, testCaseStatusType, testCaseStatusLabel } = useFormat()

const route = useRoute()
const projectId = route.params.id
const loading = ref(false)
const testcases = ref([])
const modules = ref([])
const page = ref(1)
const total = ref(0)
const filters = reactive({ search: '', module: '', status: '', priority: '' })
const searchText = ref('')
const debouncedSearch = useDebounce(searchText, 300)

const statusLabels = computed(() => t('status.testcase'))

watch(debouncedSearch, (val) => {
  filters.search = val
  page.value = 1
  fetchData()
})

function onFilterChange() {
  page.value = 1
  fetchData()
}

const typeLabel = (v) => t(`case.typeLabels.${v}`) || v

async function fetchData() {
  loading.value = true
  try {
    const params = { project: projectId, page: page.value }
    if (filters.search) params.search = filters.search
    if (filters.module) params.module = filters.module
    if (filters.status) params.status = filters.status
    if (filters.priority) params.priority = filters.priority
    const res = await getTestCases(params)
    testcases.value = res.results || res
    total.value = res.count || 0
  } finally {
    loading.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`${t('common.delete')}「${row.title}」?`, t('common.confirm'), { type: 'warning' })
  await deleteTestCase(row.id)
  ElMessage.success(t('msg.deleteSuccess'))
  fetchData()
}

onMounted(async () => {
  modules.value = await getModules(projectId)
  fetchData()
})
</script>