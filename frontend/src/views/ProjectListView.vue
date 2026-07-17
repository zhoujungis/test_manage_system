<template>
  <div class="page-container">
    <div class="page-header">
      <h2>项目管理</h2>
      <div class="page-header__actions">
        <el-button v-if="canWriteProjects" type="primary" @click="showDialog()">
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
          <el-tag size="small">{{ row.product_line === 'doorbell' ? '门铃' : '摄像头' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="planned_start_date" label="计划开始" width="110" />
      <el-table-column prop="planned_end_date" label="计划结束" width="110" />
      <el-table-column prop="member_count" label="成员数" width="80" />
      <el-table-column prop="task_count" label="任务数" width="80" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
            {{ row.status === 'active' ? '活跃' : '归档' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="selectProject(row)">查看详情</el-button>
          <el-button v-if="canWriteProjects" size="small" @click="showDialog(row)">编辑</el-button>
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
          <el-tag :type="selectedProject.status === 'active' ? 'success' : 'info'" size="small">
            {{ selectedProject.status === 'active' ? '活跃' : '归档' }}
          </el-tag>
          <span style="color:#909399;font-size:13px">负责人：{{ selectedProject.created_by_name || '-' }}</span>
        </div>
        <el-button text type="danger" @click="selectedProject = null">关闭详情</el-button>
      </div>
      <el-tabs v-model="activeTab" type="border-card" @tab-change="onTabChange">
        <!-- ==== 项目信息 ==== -->
        <el-tab-pane label="项目信息" name="info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="负责人">{{ selectedProject.created_by_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ selectedProject.created_at?.slice(0, 19).replace('T', ' ') }}</el-descriptions-item>
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

        <!-- ==== 参与人员 ==== -->
        <el-tab-pane label="参与人员" name="members">
          <div style="margin-bottom:12px">
            <el-button type="primary" size="small" @click="showMemberDialog()">添加成员</el-button>
          </div>
          <el-table :data="members" v-loading="loadingMembers" stripe size="small">
            <el-table-column prop="user_name" label="用户名" width="150" />
            <el-table-column prop="role_label" label="角色" width="150">
              <template #default="{ row: r }">
                <el-tag :type="r.role === 'leader' ? 'danger' : r.role === 'tester' ? 'success' : 'warning'" size="small">{{ r.role_label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="joined_at" label="加入时间" width="180">
              <template #default="{ row: r }">{{ r.joined_at?.slice(0, 19).replace('T', ' ') }}</template>
            </el-table-column>
            <el-table-column label="操作">
              <template #default="{ row: r }">
                <el-button size="small" type="danger" @click="handleRemoveMember(r)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ==== 任务分配 ==== -->
        <el-tab-pane label="任务分配" name="tasks">
          <div style="margin-bottom:12px">
            <el-button type="primary" size="small" @click="showTaskDialog()">新建任务</el-button>
          </div>
          <el-table :data="tasks" v-loading="loadingTasks" stripe size="small">
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
            <el-table-column prop="due_date" label="截止日期" width="110" />
            <el-table-column label="操作" width="150">
              <template #default="{ row: r }">
                <el-button size="small" @click="showTaskDialog(r)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDeleteTask(r)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ==== 用例分配 ==== -->
        <el-tab-pane label="用例分配" name="caseAssignments">
          <div style="margin-bottom:12px;display:flex;gap:8px;align-items:center">
            <el-button type="primary" size="small" @click="showCaseDialog()">分配用例</el-button>
            <el-button size="small" @click="toggleAssignedTree">{{ assignedExpanded ? '收起全部' : '展开全部' }}</el-button>
          </div>
          <el-tree :data="caseAssignedTree" :props="{ children: 'children', label: 'label' }"
            node-key="id" style="max-height:500px;overflow:auto" ref="assignedTreeRef"
            :default-expanded-keys="assignedExpandedKeys" :key="assignedTreeKey"
            @node-expand="onAssignedExpand" @node-collapse="onAssignedCollapse">
            <template #default="{ data }">
              <span style="font-size:13px;display:flex;align-items:center;gap:6px">
                <el-icon v-if="data.type==='task'"><List /></el-icon>
                <el-icon v-else-if="data.type==='module'"><Folder /></el-icon>
                <template v-else>
                  <el-tag :type="data._priority==='P0'?'danger':data._priority==='P1'?'warning':'info'" size="small">{{ data._priority }}</el-tag>
                  <span>{{ data._assignedTo }}</span>
                </template>
                <span>{{ data.label }}</span>
                <span v-if="data._notes" style="color:#909399;font-size:11px">— {{ data._notes }}</span>
                <template v-if="data.type==='testcase'">
                  <el-button size="small" @click.stop="showCaseDialog(data._raw)">编辑</el-button>
                  <el-button size="small" type="danger" @click.stop="handleDeleteCase(data._raw)">删除</el-button>
                </template>
              </span>
            </template>
          </el-tree>
        </el-tab-pane>

        <!-- ==== 用例审核 ==== -->
        <el-tab-pane label="用例审核" name="review">
          <div style="margin-bottom:12px;display:flex;gap:8px;align-items:center">
            <el-button type="success" size="small" @click="batchApproveAll" :disabled="!reviewIds.length">
              一键审核通过 ({{ reviewIds.length }})
            </el-button>
            <el-button size="small" @click="toggleReviewTree">{{ reviewExpanded ? '收起全部' : '展开全部' }}</el-button>
          </div>
          <el-tree :data="reviewTree" :props="{ children: 'children', label: 'label' }"
            node-key="id" style="max-height:500px;overflow:auto" ref="reviewTreeRef"
            :default-expanded-keys="reviewExpandedKeys" :key="reviewTreeKey">
            <template #default="{ data }">
              <span style="font-size:13px;display:flex;align-items:center;gap:6px">
                <el-icon v-if="data.type==='task'"><List /></el-icon>
                <el-icon v-else-if="data.type==='module'"><Folder /></el-icon>
                <template v-else>
                  <el-tag :type="data._priority==='P0'?'danger':data._priority==='P1'?'warning':'info'" size="small">{{ data._priority }}</el-tag>
                  <el-tag :type="data._status==='passed'?'success':data._status==='failed'?'danger':'info'" size="small">{{ data._statusLabel }}</el-tag>
                  <span>{{ data._assignedTo }}</span>
                  <el-tag :type="data._approvalRaw==='approved'?'success':data._approvalRaw==='rejected'?'danger':'info'" size="small">{{ approvalLabels[data._approvalRaw] }}</el-tag>
                </template>
                <span>{{ data.label }}</span>
                <span v-if="data._notes" style="color:#909399;font-size:11px">— {{ data._notes }}</span>
              </span>
            </template>
          </el-tree>
        </el-tab-pane>
      </el-tabs>
    </template>

    <!-- 对话框们 -->
    <el-dialog :title="editing.id ? '编辑项目' : '新建项目'" v-model="dialogVisible" width="560px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="产品线">
          <el-select v-model="form.product_line">
            <el-option label="摄像头" value="camera" />
            <el-option label="门铃" value="doorbell" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="计划开始日期">
          <el-date-picker v-model="form.planned_start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="计划结束日期">
          <el-date-picker v-model="form.planned_end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="状态" v-if="editing.id">
          <el-select v-model="form.status">
            <el-option label="活跃" value="active" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员对话框 -->
    <el-dialog title="添加成员" v-model="memberDialogVisible" width="450px">
      <el-form :model="memberForm" label-width="80px">
        <el-form-item label="选择用户">
          <el-select v-model="memberForm.user" filterable placeholder="搜索用户" style="width:100%">
            <el-option v-for="u in userList" :key="u.id" :label="`${u.username} (${u.email})`" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="memberForm.role" style="width:100%">
            <el-option label="项目负责人" value="leader" />
            <el-option label="测试人员" value="tester" />
            <el-option label="开发人员" value="developer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="memberDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddMember">确定</el-button>
      </template>
    </el-dialog>

    <!-- 任务对话框 -->
    <el-dialog :title="taskEditing.id ? '编辑任务' : '新建任务'" v-model="taskDialogVisible" width="520px" :close-on-click-modal="false">
      <el-form ref="taskFormRef" :model="taskForm" :rules="taskRules" label-width="80px">
        <el-form-item label="任务名称" prop="title">
          <el-input v-model="taskForm.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="taskForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="轮次">
          <el-input v-model="taskForm.round" placeholder="如：第一轮、回归测试" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="taskForm.assigned_to" filterable style="width:100%">
            <el-option v-for="m in members" :key="m.user" :label="m.user_name" :value="m.user" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="taskForm.priority" style="width:100%">
            <el-option label="P0-紧急" value="P0" />
            <el-option label="P1-高" value="P1" />
            <el-option label="P2-中" value="P2" />
            <el-option label="P3-低" value="P3" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="taskForm.status" style="width:100%">
            <el-option label="待开始" value="todo" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="done" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="taskForm.due_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveTask">保存</el-button>
      </template>
    </el-dialog>

    <!-- 用例分配对话框 -->
    <el-dialog :title="caseEditing.id ? '编辑用例分配' : '分配测试用例'" v-model="caseDialogVisible" width="700px" @opened="onCaseDialogOpen">
      <el-input v-model="caseTreeFilter" placeholder="搜索用例..." size="small" clearable style="margin-bottom:8px" />
      <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px">
        <el-button size="small" @click="selectAllCases">全选</el-button>
        <el-button size="small" @click="deselectAllCases">全不选</el-button>
        <el-checkbox v-model="filterAssignedCases" size="small" style="margin-left:auto">过滤已选用例</el-checkbox>
        <span style="color:#909399;font-size:12px">已选 {{ selectedCaseIds.length }} 个用例</span>
      </div>
      <el-tree :data="caseTreeData" :props="{ children: 'children', label: 'label' }"
        node-key="id" show-checkbox :filter-node-method="filterCaseNode"
        @check="onCaseTreeCheck" ref="caseTreeRef" style="max-height:400px;overflow:auto">
        <template #default="{ data }">
          <span style="font-size:13px;display:flex;align-items:center;gap:4px">
            <el-icon v-if="data.type==='module'"><Folder /></el-icon>
            <el-icon v-else><Document /></el-icon>
            <span>{{ data.label }}</span>
            <el-tag v-if="data.priority" :type="data.priority==='P0'?'danger':data.priority==='P1'?'warning':'info'" size="small">{{ data.priority }}</el-tag>
          </span>
        </template>
      </el-tree>
      <el-divider style="margin:12px 0" />
      <el-form ref="caseFormRef" :model="caseForm" :rules="caseRules" label-width="80px">
        <el-form-item label="关联任务" prop="task_id">
          <el-select v-model="caseForm.task_id" placeholder="选择任务" style="width:100%">
            <el-option v-for="t in tasks.filter(t => t.status !== 'done')" :key="t.id"
              :label="`${t.title}${t.round ? ' (' + t.round + ')' : ''}`" :value="t.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-form :model="caseForm" label-width="80px" inline>
        <el-form-item label="执行人">
          <el-select v-model="caseForm.assigned_to" filterable style="width:200px">
            <el-option v-for="m in members" :key="m.user" :label="m.user_name" :value="m.user" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="caseForm.status" style="width:140px">
            <el-option label="待测试" value="pending" />
            <el-option label="测试中" value="in_progress" />
            <el-option label="已通过" value="passed" />
            <el-option label="未通过" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="caseForm.notes" style="width:220px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveCase">
          {{ caseEditing.id ? '保存' : `批量分配 (${selectedCaseIds.length})` }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { getProjects, createProject, updateProject, deleteProject, getModules, getMembers, addMember, removeMember, getTasks, createTask, updateTask, deleteTask, getCaseAssignments, createCaseAssignment, updateCaseAssignment, deleteCaseAssignment, batchApprove } from '@/api/projects'
import { getTestCases } from '@/api/testcases'
import { getUserList } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserIdentity } from '@/composables/useUserIdentity'

const { canWriteProjects } = useUserIdentity()
const loading = ref(false)
const projects = ref([])
const selectedProject = ref(null)
const activeTab = ref('info')
const userList = ref([])

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
  onTabChange('info')
}

// ---- 项目新建/编辑对话框 ----
const dialogVisible = ref(false)
const editing = reactive({})
const form = reactive({ name: '', description: '', status: 'active', product_line: 'camera', planned_start_date: null, planned_end_date: null })
// C12 fix: 真正的表单校验
const formRef = ref(null)
const rules = { name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }] }

function showDialog(row) {
  if (row) {
    Object.assign(editing, row)
    Object.assign(form, { name: row.name, description: row.description, status: row.status, product_line: row.product_line, planned_start_date: row.planned_start_date, planned_end_date: row.planned_end_date })
  } else {
    Object.keys(editing).forEach(k => delete editing[k])
    Object.assign(form, { name: '', description: '', status: 'active', product_line: 'camera', planned_start_date: null, planned_end_date: null })
  }
  dialogVisible.value = true
}

async function handleSave() {
  // C12 fix: 走真正的 validate
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (editing.id) {
      await updateProject(editing.id, form)
      ElMessage.success('更新成功')
    } else {
      const res = await createProject(form)
      ElMessage.success('创建成功')
      selectedProject.value = res
      activeTab.value = 'info'
    }
    dialogVisible.value = false
    fetchProjects()
  } catch {
    /* 拦截器已 toast */
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除该项目？', '提示', { type: 'warning' })
  await deleteProject(row.id)
  ElMessage.success('删除成功')
  if (selectedProject.value?.id === row.id) selectedProject.value = null
  fetchProjects()
}

// ---- 项目信息：日期编辑 ----
const editingDate = ref(false)
const editForm = reactive({ planned_start_date: null, planned_end_date: null })

function startEditDate() {
  editForm.planned_start_date = selectedProject.value.planned_start_date
  editForm.planned_end_date = selectedProject.value.planned_end_date
  editingDate.value = true
}

async function saveDates() {
  await updateProject(selectedProject.value.id, {
    name: selectedProject.value.name, description: selectedProject.value.description, status: selectedProject.value.status,
    planned_start_date: editForm.planned_start_date, planned_end_date: editForm.planned_end_date,
  })
  ElMessage.success('测试时间已更新')
  editingDate.value = false
  fetchProjects()
}

// ---- 参与人员 ----
const loadingMembers = ref(false)
const members = ref([])
const memberDialogVisible = ref(false)
const memberForm = reactive({ user: null, role: 'tester' })

async function fetchMembers() {
  if (!selectedProject.value) return
  loadingMembers.value = true
  try { members.value = await getMembers(selectedProject.value.id) } finally { loadingMembers.value = false }
}

async function fetchUsers() {
  try { userList.value = await getUserList() } catch { /* */ }
}

function showMemberDialog() {
  memberForm.user = null
  memberForm.role = 'tester'
  memberDialogVisible.value = true
}

async function handleAddMember() {
  if (!memberForm.user) { ElMessage.warning('请选择用户'); return }
  try {
    await addMember(selectedProject.value.id, { user: memberForm.user, role: memberForm.role })
    ElMessage.success('添加成功')
    memberDialogVisible.value = false
    fetchMembers()
    fetchProjects()
  } catch { /* */ }
}

async function handleRemoveMember(row) {
  await ElMessageBox.confirm(`确定移除 ${row.user_name}？`, '提示', { type: 'warning' })
  await removeMember(row.id)
  ElMessage.success('移除成功')
  fetchMembers()
  fetchProjects()
}

// ---- 任务分配 ----
const loadingTasks = ref(false)
const tasks = ref([])
const taskDialogVisible = ref(false)
const taskEditing = reactive({})
const taskForm = reactive({ title: '', description: '', round: '', assigned_to: null, priority: 'P2', status: 'todo', due_date: null })
// C12 fix
const taskFormRef = ref(null)
const taskRules = { title: [{ required: true, message: '请输入任务名称', trigger: 'blur' }] }

async function fetchTasks() {
  if (!selectedProject.value) return
  loadingTasks.value = true
  try { tasks.value = await getTasks(selectedProject.value.id) } finally { loadingTasks.value = false }
}

function showTaskDialog(row) {
  if (row) {
    Object.assign(taskEditing, row)
    Object.assign(taskForm, { title: row.title, description: row.description, round: row.round || '', assigned_to: row.assigned_to, priority: row.priority, status: row.status, due_date: row.due_date })
  } else {
    Object.keys(taskEditing).forEach(k => delete taskEditing[k])
    Object.assign(taskForm, { title: '', description: '', round: '', assigned_to: null, priority: 'P2', status: 'todo', due_date: null })
  }
  taskDialogVisible.value = true
}

async function handleSaveTask() {
  // C12 fix: 走真正的 validate
  if (!taskFormRef.value) return
  const valid = await taskFormRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (taskEditing.id) {
      await updateTask(taskEditing.id, taskForm)
      ElMessage.success('更新成功')
    } else {
      await createTask(selectedProject.value.id, taskForm)
      ElMessage.success('任务创建成功')
    }
    taskDialogVisible.value = false
    fetchTasks()
    fetchProjects()
  } catch {
    /* 拦截器已 toast */
  }
}

async function handleDeleteTask(row) {
  await ElMessageBox.confirm('确定删除该任务？', '提示', { type: 'warning' })
  await deleteTask(row.id)
  ElMessage.success('删除成功')
  fetchTasks()
  fetchProjects()
}

// ---- 用例分配 ----
const caseAssignedTree = ref([])
const assignedTreeRef = ref(null)
const assignedExpandedKeys = ref([])
const assignedExpanded = ref(true)
const assignedTreeKey = ref(0)
const caseDialogVisible = ref(false)
const caseEditing = reactive({})
const caseForm = reactive({ task_id: null, assigned_to: null, status: 'pending', notes: '' })
// C12 fix
const caseFormRef = ref(null)
const caseRules = { task_id: [{ required: true, message: '请选择关联任务', trigger: 'change' }] }

const caseTreeData = ref([])
const caseTreeRef = ref(null)
const caseTreeFilter = ref('')
const selectedCaseIds = ref([])
const filterAssignedCases = ref(false)
const assignedTestCaseIds = ref([])
const _fullCaseTreeData = ref([])

const statusMap = { pending: '待测试', passed: 'Pass', failed: 'Fail', not_applicable: 'N/A', not_tested: 'N/T' }
const approvalLabels = { pending: '未审核', approved: '审核通过', rejected: '审核不通过' }

// ---- Shared assignment data cache ----
const assignmentCache = ref(null)

async function loadAssignments(params = {}) {
  if (!selectedProject.value) return []
  // H45 fix: cache key 必须含 projectId —— 否则切项目后旧 cache 会命中，
  // 显示上一个项目的分配数据。
  const key = `${selectedProject.value.id}::${JSON.stringify(params)}`
  if (assignmentCache.value?.key === key) return assignmentCache.value.data
  try {
    const data = await getCaseAssignments(selectedProject.value.id, params)
    assignmentCache.value = { key, data }
    return data
  } catch { return [] }
}

function clearAssignmentCache() {
  assignmentCache.value = null
}

function buildTree(items, prefix, includeRaw = true, groupBy = 'module') {
  const groups = {}
  items.forEach(a => {
    let key
    if (groupBy === 'task') {
      key = a.task_title ? `${a.task_title}${a.task_round ? ' · ' + a.task_round : ''}` : '未关联任务'
    } else {
      key = a.test_case_module || '未分类'
    }
    if (!groups[key]) groups[key] = []
    groups[key].push(a)
  })
  const keys = []
  const tree = Object.entries(groups).map(([group, items]) => {
    const gk = `${prefix}-grp-${group}`
    keys.push(gk)
    return {
      id: gk, label: `${group} (${items.length})`, type: groupBy === 'task' ? 'task' : 'module',
      children: items.map(a => {
        const ak = `${prefix}-${a.id}`
        keys.push(ak)
        const node = {
          id: ak, label: a.test_case_title, type: 'testcase',
          _priority: a.test_case_priority,
          _status: a.status,
          _statusLabel: statusMap[a.status] || a.status,
          _approvalRaw: a.approval_status || 'pending',
          _assignedTo: a.assigned_to_name || '未分配',
          _taskTitle: a.task_title,
          _taskRound: a.task_round,
          _notes: a.notes,
        }
        if (includeRaw) node._raw = a
        return node
      }),
    }
  })
  return { tree, keys }
}

// ---- 用例审核 ----
const reviewTree = ref([])
const reviewIds = ref([])
const reviewExpanded = ref(true)
const reviewTreeKey = ref(0)
const reviewExpandedKeys = ref([])
const reviewTreeRef = ref(null)

async function fetchReviewCases() {
  if (!selectedProject.value) return
  try {
    const items = await loadAssignments({ status: 'passed,failed,not_applicable,not_tested' })
    reviewIds.value = items.map(a => a.id)
    const { tree, keys } = buildTree(items, 'rev', false, 'task')
    reviewTree.value = tree
    reviewExpandedKeys.value = keys
    reviewExpanded.value = true
  } catch { reviewTree.value = [] }
}

function toggleReviewTree() {
  if (reviewExpanded.value) {
    reviewExpandedKeys.value = []
  } else {
    const keys = []
    function collect(nodes) { nodes.forEach(n => { keys.push(n.id); if (n.children) collect(n.children) }) }
    collect(reviewTree.value)
    reviewExpandedKeys.value = keys
  }
  reviewExpanded.value = !reviewExpanded.value
  reviewTreeKey.value++
}

async function batchApproveAll() {
  try {
    const res = await batchApprove(selectedProject.value.id, reviewIds.value)
    ElMessage.success(`已审核通过 ${res.updated} 条用例`)
    clearAssignmentCache()
    fetchReviewCases()
  } catch { /* */ }
}

async function fetchCaseAssignments() {
  if (!selectedProject.value) return
  try {
    const items = await loadAssignments()
    assignedTestCaseIds.value = items.map(a => a.test_case)
    const { tree, keys } = buildTree(items, 'ass', true, 'task')
    caseAssignedTree.value = tree
    assignedExpandedKeys.value = keys
    assignedExpanded.value = true
  } catch { caseAssignedTree.value = [] }
}

async function loadCaseTree() {
  try {
    const pl = selectedProject.value?.product_line
    const params = { all: 1 }
    if (pl) params.product_line = pl
    const res = await getTestCases(params)
    const cases = Array.isArray(res) ? res : (res.results || [])
    const mods = {}
    cases.forEach(tc => {
      const mod = tc.module_name || '未分类'
      if (!mods[mod]) mods[mod] = []
      mods[mod].push(tc)
    })
    _fullCaseTreeData.value = Object.entries(mods).map(([mod, cases]) => ({
      id: `mod-${mod}`,
      label: `${mod} (${cases.length})`,
      type: 'module',
      _modName: mod,
      children: cases.map(tc => ({
        id: `tc-${tc.id}`,
        label: tc.title,
        type: 'testcase',
        priority: tc.priority,
        _tcId: tc.id,
      })),
    }))
    applyCaseTreeFilter()
  } catch { /* */ }
}

function applyCaseTreeFilter() {
  if (!filterAssignedCases.value || !assignedTestCaseIds.value.length) {
    caseTreeData.value = _fullCaseTreeData.value
    return
  }
  const ids = new Set(assignedTestCaseIds.value)
  const prevSelected = new Set(selectedCaseIds.value)
  caseTreeData.value = _fullCaseTreeData.value
    .map(mod => {
      const filtered = mod.children.filter(tc => !ids.has(tc._tcId))
      if (!filtered.length) return null
      return { ...mod, label: `${mod._modName} (${filtered.length})`, children: filtered }
    })
    .filter(Boolean)
  nextTick(() => {
    prevSelected.forEach(id => {
      if (!ids.has(id)) caseTreeRef.value?.setChecked(`tc-${id}`, true, false)
    })
    selectedCaseIds.value = selectedCaseIds.value.filter(id => !ids.has(id))
    if (caseTreeFilter.value) caseTreeRef.value?.filter(caseTreeFilter.value)
  })
}

function filterCaseNode(value, data) {
  if (!value) return true
  return data.label.toLowerCase().includes(value.toLowerCase())
}

function onCaseTreeCheck(data, info) {
  selectedCaseIds.value = (info.checkedNodes || []).filter(n => n._tcId).map(n => n._tcId)
}

function selectAllCases() {
  const ids = []
  function collect(nodes) {
    nodes.forEach(n => {
      if (n._tcId) { ids.push(n._tcId); caseTreeRef.value?.setChecked(n.id, true, false) }
      if (n.children) collect(n.children)
    })
  }
  collect(caseTreeData.value)
  selectedCaseIds.value = ids
}

function deselectAllCases() {
  caseTreeRef.value?.setCheckedKeys([])
  selectedCaseIds.value = []
}

watch(filterAssignedCases, () => {
  applyCaseTreeFilter()
})

async function fetchTaskAssignedIds(taskId) {
  if (!taskId || !selectedProject.value) {
    assignedTestCaseIds.value = []
    if (filterAssignedCases.value) applyCaseTreeFilter()
    return
  }
  try {
    const items = await getCaseAssignments(selectedProject.value.id, { task_id: taskId })
    assignedTestCaseIds.value = items.map(a => a.test_case)
  } catch {
    assignedTestCaseIds.value = []
  }
  if (filterAssignedCases.value) applyCaseTreeFilter()
}

watch(() => caseForm.task_id, (newVal) => {
  fetchTaskAssignedIds(newVal)
})

function showCaseDialog(row) {
  caseTreeFilter.value = ''
  caseTreeData.value = []
  selectedCaseIds.value = []
  filterAssignedCases.value = false
  assignedTestCaseIds.value = []
  if (row) {
    Object.assign(caseEditing, row)
    Object.assign(caseForm, { task_id: row.task, assigned_to: row.assigned_to, status: row.status, notes: row.notes || '' })
  } else {
    Object.keys(caseEditing).forEach(k => delete caseEditing[k])
    Object.assign(caseForm, { task_id: null, assigned_to: null, status: 'pending', notes: '' })
  }
  caseDialogVisible.value = true
}

async function onCaseDialogOpen() {
  await loadCaseTree()
  if (caseEditing.id) {
    // Pre-check the existing test case
    caseTreeRef.value?.setChecked(`tc-${caseEditing.test_case}`, true, false)
  }
}

async function handleSaveCase() {
  // C12 fix: 真正的表单校验 + 选人/选用例校验
  if (caseEditing.id) {
    if (!selectedCaseIds.value.length) { ElMessage.warning('请选择用例'); return }
    if (!caseFormRef.value) return
    const valid = await caseFormRef.value.validate().catch(() => false)
    if (!valid) return
  } else {
    if (!selectedCaseIds.value.length) { ElMessage.warning('请勾选用例'); return }
    if (!caseFormRef.value) return
    const valid = await caseFormRef.value.validate().catch(() => false)
    if (!valid) return
    if (!caseForm.assigned_to) { ElMessage.warning('请选择执行人'); return }
  }
  try {
    if (caseEditing.id) {
      await updateCaseAssignment(caseEditing.id, {
        test_case: selectedCaseIds.value[0],
        task: caseForm.task_id,
        assigned_to: caseForm.assigned_to,
        status: caseForm.status,
        notes: caseForm.notes,
      })
      ElMessage.success('更新成功')
    } else {
      const res = await createCaseAssignment(selectedProject.value.id, {
        test_case_ids: selectedCaseIds.value,
        task_id: caseForm.task_id,
        assigned_to: caseForm.assigned_to,
        status: caseForm.status,
        notes: caseForm.notes,
      })
      ElMessage.success(`分配完成：新增 ${res.created}，更新 ${res.updated}`)
    }
    caseDialogVisible.value = false
    clearAssignmentCache()
    fetchCaseAssignments()
  } catch {
    /* 拦截器已 toast */
  }
}

async function handleDeleteCase(row) {
  await ElMessageBox.confirm('确定删除该分配？', '提示', { type: 'warning' })
  await deleteCaseAssignment(row.id)
  ElMessage.success('删除成功')
  clearAssignmentCache()
  fetchCaseAssignments()
}

async function updateApproval(raw, val) {
  try {
    await updateCaseAssignment(raw.id, { approval_status: val })
    ElMessage.success('审核状态已更新')
  } catch { /* */ }
}

function toggleAssignedTree() {
  if (assignedExpanded.value) {
    assignedExpandedKeys.value = []
    assignedTreeKey.value++
  } else {
    const keys = []
    function collect(nodes) { nodes.forEach(n => { keys.push(n.id); if (n.children) collect(n.children) }) }
    collect(caseAssignedTree.value)
    assignedExpandedKeys.value = keys
    assignedTreeKey.value++
  }
  assignedExpanded.value = !assignedExpanded.value
}

function onAssignedExpand() { assignedExpanded.value = true }
function onAssignedCollapse() { assignedExpanded.value = false }

// ---- Tab 切换 ----
function onTabChange(tab) {
  if (tab === 'members') fetchMembers()
  if (tab === 'tasks') fetchTasks()
  if (tab === 'caseAssignments') { Promise.all([fetchMembers(), fetchTasks(), fetchCaseAssignments()]) }
  if (tab === 'review') { fetchReviewCases() }
}

watch(caseTreeFilter, (val) => {
  caseTreeRef.value?.filter(val)
})

onMounted(() => {
  fetchProjects()
  fetchUsers()
})
</script>

<style scoped>
:deep(.selected-row) { background-color: #ecf5ff !important; }
</style>
