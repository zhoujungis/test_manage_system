<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('menu.myProjects') }}</h2>
    </div>

    <div class="table-card">
    <el-table :data="myProjects" v-loading="loading" stripe @row-click="selectProject"
      highlight-current-row :row-class-name="rowClass">
      <el-table-column prop="name" :label="t('project.name')" />
      <el-table-column prop="created_by_name" :label="t('task.owner')" width="100" />
      <el-table-column :label="t('project.productLine')" width="90">
        <template #default="{ row }">
          <el-tag size="small">{{ productLineLabel(row.product_line) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="planned_start_date" :label="t('project.plannedStart')" width="110" />
      <el-table-column prop="planned_end_date" :label="t('project.plannedEnd')" width="110" />
      <el-table-column prop="member_count" :label="t('project.members')" width="80" />
      <el-table-column :label="t('project.status')" width="80">
        <template #default="{ row }">
          <el-tag :type="projectStatusType(row.status)" size="small">
            {{ projectStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('common.operation')" width="80">
        <template #default="{ row }">
          <el-button size="small" @click.stop="selectProject(row)">{{ t('crumb.project') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && myProjects.length === 0" :description="t('common.noData')" />
    </div>

    <template v-if="selectedProject">
      <el-divider />
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
        <span style="font-size:16px;font-weight:700">{{ selectedProject.name }}</span>
        <el-button text type="danger" @click="closeProject">{{ t('common.back') }}</el-button>
      </div>
      <el-table :data="projectTasks" v-loading="loadingTasks" stripe size="small">
        <el-table-column prop="title" :label="t('task.title')" show-overflow-tooltip />
        <el-table-column prop="round" :label="t('task.round')" width="100" />
        <el-table-column prop="assigned_to_name" :label="t('task.owner')" width="100" />
        <el-table-column :label="t('task.priority')" width="80">
          <template #default="{ row: r }">
            <el-tag :type="priorityType(r.priority)" size="small">{{ r.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('task.status')" width="90">
          <template #default="{ row: r }">
            <el-tag :type="taskStatusType(r.status)" size="small">{{ r.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('common.operation')" width="140">
          <template #default="{ row: r }">
            <el-button size="small" type="primary" :disabled="r.status === 'done'"
              @click="$router.push(`/tm/${selectedProject.id}/execute?task_id=${r.id}`)">
              {{ t('run.startAction') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loadingTasks && projectTasks.length === 0" :description="t('common.noData')" />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getProjects, getTasks } from '@/api/projects'
import { useFormat } from '@/composables/useFormat'

const { t } = useI18n()
const { projectStatusType, projectStatusLabel, productLineLabel, priorityType, taskStatusType } = useFormat()

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
  try { projectTasks.value = await getTasks(row.id) } catch { projectTasks.value = [] }
  finally { loadingTasks.value = false }
}

function closeProject() {
  selectedProject.value = null
  projectTasks.value = []
}

function rowClass({ row }) {
  return selectedProject.value?.id === row.id ? 'selected-row' : ''
}

onMounted(fetchMyProjects)
</script>