<template>
  <div class="page-container">
    <div class="page-header">
      <h2>测试用例</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="$router.push(`/projects/${projectId}/testcases/new`)">新建用例</el-button>
      </div>
    </div>
    <div class="filter-card">
      <el-row :gutter="16">
        <el-col :span="4">
          <el-input v-model="searchText" placeholder="搜索标题" clearable />
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.module" placeholder="模块筛选" clearable @change="fetchData">
            <el-option v-for="m in modules" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.status" placeholder="状态筛选" clearable @change="onFilterChange">
            <el-option label="草稿" value="draft" />
            <el-option label="活跃" value="active" />
            <el-option label="已废弃" value="deprecated" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.priority" placeholder="优先级筛选" clearable @change="onFilterChange">
            <el-option label="P0-最高" value="P0" />
            <el-option label="P1-高" value="P1" />
            <el-option label="P2-中" value="P2" />
            <el-option label="P3-低" value="P3" />
            <el-option label="P4-最低" value="P4" />
          </el-select>
        </el-col>
      </el-row>
    </div>
    <div class="table-card">
    <el-table :data="testcases" v-loading="loading" stripe @row-click="(row) => $router.push(`/projects/${projectId}/testcases/${row.id}`)" style="cursor: pointer">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" show-overflow-tooltip />
      <el-table-column prop="module_name" label="模块" width="120" />
      <el-table-column prop="priority" label="优先级" width="100">
        <template #default="{ row }">
          <el-tag :type="priorityType(row.priority)" size="small">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="case_type" label="类型" width="100">
        <template #default="{ row }">
          {{ typeLabel(row.case_type) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_by_name" label="创建人" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ row.created_at?.slice(0, 19).replace('T', ' ') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click.stop="$router.push(`/projects/${projectId}/testcases/${row.id}`)">编辑</el-button>
          <el-button size="small" type="danger" @click.stop="handleDelete(row)">删除</el-button>
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
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getTestCases, deleteTestCase } from '@/api/testcases'
import { getModules } from '@/api/projects'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useDebounce } from '@/composables/useDebounce'

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

watch(debouncedSearch, (val) => {
  filters.search = val
  page.value = 1
  fetchData()
})

// M27 fix: 任何 filter 变化都重置 page=1 —— 之前只有 search 改时会复位，
// 状态/优先级切换不会，导致新数据可能落在空页
function onFilterChange() {
  page.value = 1
  fetchData()
}

function typeLabel(t) {
  const map = { functional: '功能测试', api: '接口测试', ui: 'UI测试', performance: '性能测试' }
  return map[t] || t
}
function statusLabel(s) {
  const map = { draft: '草稿', active: '活跃', deprecated: '已废弃' }
  return map[s] || s
}
function statusType(s) {
  const map = { draft: 'info', active: 'success', deprecated: 'warning' }
  return map[s] || 'info'
}
function priorityType(p) {
  const map = { P0: 'danger', P1: 'danger', P2: 'warning', P3: 'info', P4: '' }
  return map[p] || ''
}

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
  await ElMessageBox.confirm('确定删除该用例？', '提示', { type: 'warning' })
  await deleteTestCase(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(async () => {
  modules.value = await getModules(projectId)
  fetchData()
})
</script>
