<template>
  <div class="page-container">
    <div class="page-header">
      <h2>项目管理</h2>
      <div class="page-header__actions">
        <el-button v-if="canWriteProjects" type="primary" @click="projectDlg.open()">
          <el-icon><Plus /></el-icon>
          新建项目
        </el-button>
      </div>
    </div>

    <!-- 项目列表 -->
    <div class="table-card">
      <el-table :data="projects" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="项目名称" show-overflow-tooltip />
        <el-table-column prop="created_by_name" label="负责人" width="100" />
        <el-table-column prop="product_line" label="产品线" width="90">
          <template #default="{ row }">
            <el-tag size="small">{{ productLineLabel(row.product_line) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="planned_start_date" label="计划开始" width="110" />
        <el-table-column prop="planned_end_date" label="计划结束" width="110" />
        <el-table-column prop="member_count" label="成员数" width="80" />
        <el-table-column prop="task_count" label="任务数" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="projectStatusType(row.status)" size="small">{{ projectStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="selectProject(row)">查看详情</el-button>
            <el-button v-if="canWriteProjects" size="small" @click="projectDlg.open(row)">编辑</el-button>
            <el-button v-if="canWriteProjects" size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && projects.length === 0" description="暂无项目，点击上方按钮新建" />
    </div>

    <!-- 选中项目的详情面板 -->
    <template v-if="selectedProject">
      <el-divider />
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
        <div style="display:flex;align-items:center;gap:8px">
          <span style="font-size:16px;font-weight:700">{{ selectedProject.name }}</span>
          <el-tag :type="projectStatusType(selectedProject.status)" size="small">{{ projectStatusLabel(selectedProject.status) }}</el-tag>
          <span style="color:#909399;font-size:13px">负责人：{{ selectedProject.created_by_name || '-' }}</span>
        </div>
        <el-button text type="danger" @click="selectedProject = null">关闭详情</el-button>
      </div>
      <el-tabs v-model="activeTab" type="border-card">
        <!-- ==== 项目信息 ==== -->
        <el-tab-pane label="项目信息" name="info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="负责人">{{ selectedProject.created_by_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDateTime(selectedProject.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="计划开始日期">
              <template v-if="editingDate">
                <el-date-picker v-model="editForm.planned_start_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:160px" />
              </template>
              <template v-else>{{ selectedProject.planned_start_date || '未设置' }}</template>
            </el-descriptions-item>
            <el-descriptions-item label="计划结束日期">
              <template v-if="editingDate">
                <el-date-picker v-model="editForm.planned_end_date" type="date" value-format="YYYY-MM-DD" size="small" style="width:160px" />
              </template>
              <template v-else>{{ selectedProject.planned_end_date || '未设置' }}</template>
            </el-descriptions-item>
            <el-descriptions-item label="参与人数">{{ selectedProject.member_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="任务数">{{ selectedProject.task_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">{{ selectedProject.description || '-' }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top:12px">
            <template v-if="editingDate">
              <el-button type="primary" size="small" @click="saveDates">保存测试时间</el-button>
              <el-button size="small" @click="editingDate = false">取消</el-button>
            </template>
            <template v-else>
              <el-button size="small" type="primary" @click="startEditDate">规划测试时间</el-button>
            </template>
          </div>
        </el-tab-pane>

        <!-- ==== 参与人员 (extracted to ProjectMembersPanel) ==== -->
        <el-tab-pane label="参与人员" name="members">
          <ProjectMembersPanel :project="selectedProject" @change="onSubPanelChange" />
        </el-tab-pane>

        <!-- ==== 任务分配 (extracted to ProjectTasksPanel) ==== -->
        <el-tab-pane label="任务分配" name="tasks">
          <ProjectTasksPanel :project="selectedProject" @change="onSubPanelChange" />
        </el-tab-pane>

        <!-- ==== 用例分配 + 审核 (extracted to CaseAssignmentPanel) ==== -->
        <el-tab-pane label="用例分配" name="caseAssignments">
          <CaseAssignmentPanel :project="selectedProject" @change="onSubPanelChange" />
        </el-tab-pane>
      </el-tabs>
    </template>

    <!-- 项目新建/编辑对话框 -->
    <el-dialog :title="projectDlg.editing.value ? '编辑项目' : '新建项目'" v-model="projectDlg.visible.value" width="560px" :close-on-click-modal="false">
      <el-form ref="projectDlg.formRef" :model="projectDlg.form" :rules="projectDlg.rules" label-width="100px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="projectDlg.form.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="产品线">
          <el-select v-model="projectDlg.form.product_line">
            <el-option label="摄像头" value="camera" />
            <el-option label="门铃" value="doorbell" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="projectDlg.form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="计划开始日期">
          <el-date-picker v-model="projectDlg.form.planned_start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="计划结束日期">
          <el-date-picker v-model="projectDlg.form.planned_end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="状态" v-if="projectDlg.editing.value">
          <el-select v-model="projectDlg.form.status">
            <el-option label="活跃" value="active" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="projectDlg.close()">取消</el-button>
        <el-button type="primary" :loading="projectDlg.submitting.value" @click="handleSaveProject">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
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

const { canWriteProjects } = useUserIdentity()
const { projectStatusType, projectStatusLabel, productLineLabel } = useFormat()

const loading = ref(false)
const projects = ref([])
const selectedProject = ref(null)
const activeTab = ref('info')

// ---- 项目列表 ----
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

// ---- 项目 CRUD ----
const projectDlg = useCrudDialog({
  defaults: {
    name: '', description: '', status: 'active', product_line: 'camera',
    planned_start_date: null, planned_end_date: null,
  },
  rules: { name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }] },
  create: (data) => createProject(data),
  update: (id, data) => updateProject(id, data),
  refresh: async () => {
    await fetchProjects()
    if (!projectDlg.editing.value) {
      // 新建成功后选中新建的项目
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
  // H40 fix: 提示级联影响
  const counts = []
  if (row.testplan_count) counts.push(`${row.testplan_count} 个测试计划`)
  if (row.testcase_count) counts.push(`${row.testcase_count} 条测试用例`)
  if (row.task_count) counts.push(`${row.task_count} 个任务`)
  if (row.member_count) counts.push(`${row.member_count} 名成员`)
  const cascadeHint = counts.length ? `\n该项目下的 ${counts.join('、')} 也会被一并删除。` : ''
  try {
    await ElMessageBox.confirm(
      `确定删除项目「${row.name}」？${cascadeHint}`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
    )
  } catch { return }
  await deleteProject(row.id)
  ElMessage.success('删除成功')
  if (selectedProject.value?.id === row.id) selectedProject.value = null
  fetchProjects()
}

// ---- 项目日期编辑 ----
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
  ElMessage.success('测试时间已更新')
  editingDate.value = false
  fetchProjects()
}

function onSubPanelChange() {
  // 子面板发生增删改 → 拉新项目列表刷新计数
  fetchProjects()
}

onMounted(fetchProjects)
</script>