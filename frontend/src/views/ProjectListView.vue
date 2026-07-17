<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('project.list') }}</h2>
      <div class="page-header__actions">
        <el-button v-if="canWriteProjects" type="primary" @click="projectDlg.open()">
          <el-icon><Plus /></el-icon>
          {{ t('project.new') }}
        </el-button>
      </div>
    </div>

    <!-- 项目列表 -->
    <div class="table-card">
      <el-table :data="projects" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" :label="t('project.name')" show-overflow-tooltip />
        <el-table-column prop="created_by_name" :label="t('member.username')" width="100" />
        <el-table-column :label="t('project.productLine')" width="90">
          <template #default="{ row }">
            <el-tag size="small">{{ productLineLabel(row.product_line) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="planned_start_date" :label="t('project.plannedStart')" width="110" />
        <el-table-column prop="planned_end_date" :label="t('project.plannedEnd')" width="110" />
        <el-table-column prop="member_count" :label="t('project.members')" width="80" />
        <el-table-column prop="task_count" :label="t('project.tasks')" width="80" />
        <el-table-column :label="t('project.status')" width="80">
          <template #default="{ row }">
            <el-tag :type="projectStatusType(row.status)" size="small">{{ projectStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('common.operation')" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="selectProject(row)">{{ t('crumb.project') }}</el-button>
            <el-button v-if="canWriteProjects" size="small" @click="projectDlg.open(row)">{{ t('common.edit') }}</el-button>
            <el-button v-if="canWriteProjects" size="small" type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && projects.length === 0" :description="t('project.emptyProjects')" />
    </div>

    <!-- 选中项目的详情面板 -->
    <template v-if="selectedProject">
      <el-divider />
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
        <div style="display:flex;align-items:center;gap:8px">
          <span style="font-size:16px;font-weight:700">{{ selectedProject.name }}</span>
          <el-tag :type="projectStatusType(selectedProject.status)" size="small">{{ projectStatusLabel(selectedProject.status) }}</el-tag>
          <span style="color:#909399;font-size:13px">{{ t('member.username') }}: {{ selectedProject.created_by_name || '-' }}</span>
        </div>
        <el-button text type="danger" @click="selectedProject = null">{{ t('common.back') }}</el-button>
      </div>
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane :label="t('crumb.project')" name="info">
          <el-descriptions :column="2" border>
            <el-descriptions-item :label="t('task.owner')">{{ selectedProject.created_by_name || '-' }}</el-descriptions-item>
            <el-descriptions-item :label="t('case.createdAt')">{{ formatDateTime(selectedProject.created_at) }}</el-descriptions-item>
            <el-descriptions-item :label="t('project.plannedStart')">
              <template v-if="editingDate">
                <el-date-picker v-model="editForm.planned_start_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:160px" />
              </template>
              <template v-else>{{ selectedProject.planned_start_date || t('common.unknown') }}</template>
            </el-descriptions-item>
            <el-descriptions-item :label="t('project.plannedEnd')">
              <template v-if="editingDate">
                <el-date-picker v-model="editForm.planned_end_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:160px" />
              </template>
              <template v-else>{{ selectedProject.planned_end_date || t('common.unknown') }}</template>
            </el-descriptions-item>
            <el-descriptions-item :label="t('project.members')">{{ selectedProject.member_count || 0 }}</el-descriptions-item>
            <el-descriptions-item :label="t('project.tasks')">{{ selectedProject.task_count || 0 }}</el-descriptions-item>
            <el-descriptions-item :label="t('project.desc')" :span="2">{{ selectedProject.description || '-' }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top:12px">
            <template v-if="editingDate">
              <el-button type="primary" size="small" @click="saveDates">{{ t('project.savePlan') }}</el-button>
              <el-button size="small" @click="editingDate = false">{{ t('project.cancelPlan') }}</el-button>
            </template>
            <template v-else>
              <el-button size="small" type="primary" @click="startEditDate">{{ t('project.setPlan') }}</el-button>
            </template>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="t('project.members')" name="members">
          <ProjectMembersPanel :project="selectedProject" @change="onSubPanelChange" />
        </el-tab-pane>

        <el-tab-pane :label="t('project.tasks')" name="tasks">
          <ProjectTasksPanel :project="selectedProject" @change="onSubPanelChange" />
        </el-tab-pane>

        <el-tab-pane :label="t('project.caseAssignment')" name="caseAssignments">
          <CaseAssignmentPanel :project="selectedProject" @change="onSubPanelChange" />
        </el-tab-pane>
      </el-tabs>
    </template>

    <!-- 项目新建/编辑对话框 -->
    <el-dialog :title="projectDlg.editing.value ? t('project.edit') : t('project.new')" v-model="projectDlg.visible.value" width="560px" :close-on-click-modal="false">
      <el-form ref="projectDlg.formRef" :model="projectDlg.form" :rules="projectDlg.rules" label-width="100px">
        <el-form-item :label="t('project.name')" prop="name">
          <el-input v-model="projectDlg.form.name" :placeholder="t('project.name')" />
        </el-form-item>
        <el-form-item :label="t('project.productLine')">
          <el-select v-model="projectDlg.form.product_line">
            <el-option :label="t('project.productCamera')" value="camera" />
            <el-option :label="t('project.productDoorbell')" value="doorbell" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('project.desc')">
          <el-input v-model="projectDlg.form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="t('project.plannedStart')">
          <el-date-picker v-model="projectDlg.form.planned_start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('project.plannedEnd')">
          <el-date-picker v-model="projectDlg.form.planned_end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('project.status')" v-if="projectDlg.editing.value">
          <el-select v-model="projectDlg.form.status">
            <el-option :label="t('status.project.active')" value="active" />
            <el-option :label="t('status.project.archived')" value="archived" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="projectDlg.close()">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="projectDlg.submitting.value" @click="handleSaveProject">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getProjects, createProject, updateProject, deleteProject } from '@/api/projects'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserIdentity } from '@/composables/useUserIdentity'
import { useCrudDialog } from '@/composables/useCrudDialog'
import { useFormat } from '@/composables/useFormat'
import { formatDateTime } from '@/utils/dateFormat'
import { Plus } from '@element-plus/icons-vue'
import ProjectMembersPanel from './ProjectMembersPanel.vue'
import ProjectTasksPanel from './ProjectTasksPanel.vue'
import CaseAssignmentPanel from './CaseAssignmentPanel.vue'

const { t } = useI18n()
const { canWriteProjects } = useUserIdentity()
const { projectStatusType, projectStatusLabel, productLineLabel } = useFormat()

const loading = ref(false)
const projects = ref([])
const selectedProject = ref(null)
const activeTab = ref('info')

async function fetchProjects() {
  loading.value = true
  try {
    const params = canWriteProjects.value ? { led: 1 } : {}
    const res = await getProjects(params)
    projects.value = res.results || res
    if (selectedProject.value) {
      const found = projects.value.find(p => p.id === selectedProject.value.id)
      if (found) selectedProject.value = found
    }
  } finally { loading.value = false }
}

function selectProject(row) {
  selectedProject.value = row
  activeTab.value = 'info'
}

const projectDlg = useCrudDialog({
  defaults: {
    name: '', description: '', status: 'active', product_line: 'camera',
    planned_start_date: null, planned_end_date: null,
  },
  rules: computed(() => ({
    name: [{ required: true, message: t('project.name'), trigger: 'blur' }],
  })).value,
  create: (data) => createProject(data),
  update: (id, data) => updateProject(id, data),
  refresh: async () => {
    await fetchProjects()
    if (!projectDlg.editing.value) {
      const created = projects.value.find((p) => p.name === projectDlg.form.name)
      if (created) {
        selectedProject.value = created
        activeTab.value = 'info'
      }
    }
  },
})

async function handleSaveProject() {
  await projectDlg.save()
}

async function handleDelete(row) {
  const counts = []
  if (row.testplan_count) counts.push(`${row.testplan_count} ${t('plan.list')}`)
  if (row.testcase_count) counts.push(`${row.testcase_count} ${t('case.list')}`)
  if (row.task_count) counts.push(`${row.task_count} ${t('project.tasks')}`)
  if (row.member_count) counts.push(`${row.member_count} ${t('project.members')}`)
  const cascadeHint = counts.length ? `\n${t('common.delete')} ${counts.join(', ')}` : ''
  try {
    await ElMessageBox.confirm(
      `${t('common.delete')}「${row.name}」?${cascadeHint}`,
      t('common.confirm'),
      { type: 'warning', confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel') },
    )
  } catch { return }
  await deleteProject(row.id)
  ElMessage.success(t('msg.deleteSuccess'))
  if (selectedProject.value?.id === row.id) selectedProject.value = null
  fetchProjects()
}

const editingDate = ref(false)
const editForm = reactive({ planned_start_date: null, planned_end_date: null })

function startEditDate() {
  editForm.planned_start_date = selectedProject.value.planned_start_date
  editForm.planned_end_date = selectedProject.value.planned_end_date
  editingDate.value = true
}

async function saveDates() {
  await updateProject(selectedProject.value.id, {
    name: selectedProject.value.name,
    description: selectedProject.value.description,
    status: selectedProject.value.status,
    planned_start_date: editForm.planned_start_date,
    planned_end_date: editForm.planned_end_date,
  })
  ElMessage.success(t('msg.updateSuccess'))
  editingDate.value = false
  fetchProjects()
}

function onSubPanelChange() {
  fetchProjects()
}

onMounted(fetchProjects)
</script>