<template>
  <div class="page-container">
    <div class="page-header">
      <h2>我的项目</h2>
    </div>

    <div class="table-card">
    <el-table :data="myProjects" v-loading="loading" stripe @row-click="selectProject"
      highlight-current-row :row-class-name="rowClass">
      <el-table-column prop="name" label="项目名称" />
      <el-table-column prop="created_by_name" label="负责人" width="100" />
      <el-table-column prop="product_line" label="产品线" width="90">
        <template #default="{ row }">
          <el-tag size="small">{{ row.product_line === 'doorbell' ? '门铃' : '摄像头' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="planned_start_date" label="计划开始" width="110" />
      <el-table-column prop="planned_end_date" label="计划结束" width="110" />
      <el-table-column prop="member_count" label="成员数" width="80" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
            {{ row.status === 'active' ? '活跃' : '归档' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{ row }">
          <el-button size="small" @click.stop="selectProject(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && myProjects.length === 0" description="暂无参与的项目" />
    </div>

    <!-- 选中项目的任务列表 -->
    <template v-if="selectedProject">
      <el-divider />
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
        <span style="font-size:16px;font-weight:700">{{ selectedProject.name }}</span>
        <el-button text type="danger" @click="selectedProject = null; projectTasks = []">关闭</el-button>
      </div>
      <el-table :data="projectTasks" v-loading="loadingTasks" stripe size="small">
        <el-table-column prop="title" label="任务名称" show-overflow-tooltip />
        <el-table-column prop="round" label="轮次" width="100" />
        <el-table-column prop="assigned_to_name" label="负责人" width="100" />
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row: r }">
            <el-tag :type="r.priority === 'P0' ? 'danger' : r.priority === 'P1' ? 'warning' : 'info'" size="small">{{ r.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status_label" label="状态" width="90">
          <template #default="{ row: r }">
            <el-tag :type="r.status === 'done' ? 'success' : r.status === 'in_progress' ? 'warning' : 'info'" size="small">{{ r.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row: r }">
            <el-button size="small" type="primary" :disabled="r.status === 'done'"
              @click="$router.push(`/tm/${selectedProject.id}/execute?task_id=${r.id}`)">
              执行测试
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loadingTasks && projectTasks.length === 0" description="该项目暂无任务" />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProjects, getTasks } from '@/api/projects'

const loading = ref(false)
const loadingTasks = ref(false)
const myProjects = ref([])
const selectedProject = ref(null)
const projectTasks = ref([])

async function fetchMyProjects() {
  loading.value = true
  try {
    const res = await getProjects({ my: 1 })
    myProjects.value = res.results || res
  } finally { loading.value = false }
}

async function selectProject(row) {
  selectedProject.value = row
  loadingTasks.value = true
  try {
    projectTasks.value = await getTasks(row.id)
  } catch {
    projectTasks.value = []
  } finally { loadingTasks.value = false }
}

function rowClass({ row }) {
  return selectedProject.value?.id === row.id ? 'selected-row' : ''
}

onMounted(fetchMyProjects)
</script>

<!-- M36 fix: .selected-row 全局唯一来源已在 style.css 定义，
     这里不用再 :deep() 重复。Element Plus 的 row-class-name 会自动注入到 tr。-->
