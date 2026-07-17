<template>
  <div class="case-panel">
    <el-tabs v-model="activeSubTab" type="card">
      <!-- 用例分配 -->
      <el-tab-pane label="用例分配" name="assign">
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
                <el-tag :type="priorityType(data._priority)" size="small">{{ data._priority }}</el-tag>
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

      <!-- 用例审核 -->
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
                <el-tag :type="priorityType(data._priority)" size="small">{{ data._priority }}</el-tag>
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

    <!-- 分配对话框 -->
    <el-dialog :title="caseEditing.id ? '编辑用例分配' : '分配测试用例'" v-model="caseDialogVisible" width="700px" @opened="onCaseDialogOpen" :close-on-click-modal="false">
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
            <el-tag v-if="data.priority" :type="priorityType(data.priority)" size="small">{{ data.priority }}</el-tag>
          </span>
        </template>
      </el-tree>
      <el-divider style="margin:12px 0" />
      <el-form ref="caseFormRef" :model="caseForm" :rules="caseRules" label-width="80px">
        <el-form-item label="关联任务" prop="task_id">
          <el-select v-model="caseForm.task_id" placeholder="选择任务" style="width:100%">
            <el-option v-for="t in openTasks" :key="t.id"
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
        <el-button type="primary" :loading="savingCase" @click="handleSaveCase">
          {{ caseEditing.id ? '保存' : `批量分配 (${selectedCaseIds.length})` }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getCaseAssignments, createCaseAssignment, updateCaseAssignment,
  deleteCaseAssignment, batchApprove, getTasks, getMembers,
} from '@/api/projects'
import { useFormat } from '@/composables/useFormat'
import { formatDateTime } from '@/utils/dateFormat'
import { Folder, Document, List } from '@element-plus/icons-vue'

const props = defineProps({ project: { type: Object, required: true } })
const emit = defineEmits(['change'])

const { priorityType } = useFormat()
const approvalLabels = { pending: '未审核', approved: '审核通过', rejected: '审核不通过' }
const activeSubTab = ref('assign')

// ---- 分配树 ----
const caseAssignedTree = ref([])
const assignedTreeRef = ref(null)
const assignedExpandedKeys = ref([])
const assignedExpanded = ref(true)
const assignedTreeKey = ref(0)
async function fetchCaseAssignments() {
  try {
    const items = await getCaseAssignments(props.project.id)
    buildAssignmentTree(items)
    reviewIds.value = items.map((a) => a.id)
  } catch { /* */ }
}
function buildAssignmentTree(items) {
  const tasksMap = {}
  items.forEach((a) => {
    const tKey = a.task || 'no-task'
    if (!tasksMap[tKey]) {
      tasksMap[tKey] = {
        id: `task-${tKey}`, label: a.task_title || '无任务', type: 'task', children: [],
      }
    }
    tasksMap[tKey].children.push({
      id: `tc-${a.id}`,
      label: a.test_case_title,
      type: 'testcase',
      _priority: a.test_case_priority,
      _assignedTo: a.assigned_to_name,
      _notes: a.notes,
      _raw: a,
    })
  })
  caseAssignedTree.value = Object.values(tasksMap)
  if (assignedExpanded.value) {
    assignedExpandedKeys.value = caseAssignedTree.value.map((n) => n.id)
  }
}
function toggleAssignedTree() {
  if (assignedExpanded.value) {
    assignedExpandedKeys.value = []
  } else {
    assignedExpandedKeys.value = caseAssignedTree.value.map((n) => n.id)
  }
  assignedExpanded.value = !assignedExpanded.value
  assignedTreeKey.value++
}
function onAssignedExpand(node) {
  if (!assignedExpandedKeys.value.includes(node.id)) assignedExpandedKeys.value.push(node.id)
}
function onAssignedCollapse(node) {
  const i = assignedExpandedKeys.value.indexOf(node.id)
  if (i >= 0) assignedExpandedKeys.value.splice(i, 1)
}

// ---- 审核树 ----
const reviewTree = ref([])
const reviewTreeRef = ref(null)
const reviewExpandedKeys = ref([])
const reviewExpanded = ref(true)
const reviewTreeKey = ref(0)
const reviewIds = ref([])
function buildReviewTree(items) {
  const tasksMap = {}
  items.forEach((a) => {
    const tKey = a.task || 'no-task'
    if (!tasksMap[tKey]) {
      tasksMap[tKey] = {
        id: `task-${tKey}`, label: a.task_title || '无任务', type: 'task', children: [],
      }
    }
    tasksMap[tKey].children.push({
      id: `tc-${a.id}`,
      label: a.test_case_title,
      type: 'testcase',
      _priority: a.test_case_priority,
      _assignedTo: a.assigned_to_name,
      _status: a.status,
      _statusLabel: assignmentStatusLabel(a.status),
      _approvalRaw: a.approval_status,
      _notes: a.notes,
    })
  })
  reviewTree.value = Object.values(tasksMap)
  if (reviewExpanded.value) {
    reviewExpandedKeys.value = reviewTree.value.map((n) => n.id)
  }
}
function assignmentStatusLabel(s) {
  return { pending: '待测试', in_progress: '测试中', passed: '通过', failed: '失败' }[s] || s
}
function toggleReviewTree() {
  if (reviewExpanded.value) {
    reviewExpandedKeys.value = []
  } else {
    reviewExpandedKeys.value = reviewTree.value.map((n) => n.id)
  }
  reviewExpanded.value = !reviewExpanded.value
  reviewTreeKey.value++
}
async function batchApproveAll() {
  try {
    await ElMessageBox.confirm(`一键通过 ${reviewIds.value.length} 个分配？`, '审核确认', { type: 'warning' })
  } catch { return }
  const res = await batchApprove(props.project.id, reviewIds.value)
  ElMessage.success(`已通过 ${res.updated || reviewIds.value.length} 个`)
  fetchCaseAssignments()
  emit('change')
}

// ---- 分配对话框 ----
const caseDialogVisible = ref(false)
const caseEditing = reactive({})
const caseTreeFilter = ref('')
const caseTreeData = ref([])
const caseTreeRef = ref(null)
const caseFormRef = ref(null)
const filterAssignedCases = ref(false)
const selectedCaseIds = ref([])
const caseForm = reactive({ task_id: null, assigned_to: null, status: 'pending', notes: '' })
const caseRules = { task_id: [{ required: true, message: '请选择关联任务', trigger: 'change' }] }
const savingCase = ref(false)
const members = ref([])
const openTasks = computed(() => (tasks.value || []).filter((t) => t.status !== 'done'))
const tasks = ref([])

async function loadCaseTree() {
  const res = await getCaseAssignments(props.project.id, { all: 1 })
  const allIds = new Set((res.results || res).map((a) => a.test_case))
  caseTreeData.value = await fetchTestCaseTree()
  // 简化：直接返回树
  async function fetchTestCaseTree() {
    const { getTestCaseTree } = await import('@/api/testcases')
    const params = { product_line: props.project.product_line || 'camera' }
    const items = await getTestCaseTree(params).catch(() => ({ results: [] }))
    const mods = {}
    ;(items.results || []).forEach((tc) => {
      const m = tc.module_name || '未分类'
      if (!mods[m]) mods[m] = []
      const assigned = allIds.has(tc.id) && filterAssignedCases.value
      if (filterAssignedCases.value && assigned) return
      mods[m].push({
        id: `tc-${tc.id}`, label: tc.title, type: 'testcase', priority: tc.priority,
      })
    })
    return Object.entries(mods).map(([m, children]) => ({
      id: `mod-${m}`, label: m, type: 'module', children,
    }))
  }
}
async function fetchTasksAndMembers() {
  try {
    tasks.value = await getTasks(props.project.id)
    const m = await getMembers(props.project.id)
    members.value = m.results || m
  } catch { /* */ }
}

function selectAllCases() {
  caseTreeData.value.forEach((m) => {
    m.children?.forEach((c) => caseTreeRef.value?.setChecked(c.id, true, false))
  })
}
function deselectAllCases() {
  caseTreeRef.value?.setCheckedKeys([])
}
function filterCaseNode(value, data) {
  if (!value) return true
  return data.label?.includes(value)
}
function onCaseTreeCheck() {
  const checked = caseTreeRef.value?.getCheckedNodes?.() || []
  selectedCaseIds.value = checked.filter((n) => n.type === 'testcase').map((n) => Number(n.id.replace('tc-', '')))
}

async function onCaseDialogOpen() {
  await loadCaseTree()
  await fetchTasksAndMembers()
  if (caseEditing.id) {
    caseTreeRef.value?.setChecked(`tc-${caseEditing.test_case}`, true, false)
  }
}

function showCaseDialog(row) {
  if (row) {
    Object.assign(caseEditing, row)
    caseForm.task_id = row.task
    caseForm.assigned_to = row.assigned_to
    caseForm.status = row.status
    caseForm.notes = row.notes
  } else {
    Object.keys(caseEditing).forEach((k) => delete caseEditing[k])
    caseForm.task_id = null
    caseForm.assigned_to = null
    caseForm.status = 'pending'
    caseForm.notes = ''
  }
  caseDialogVisible.value = true
}

async function handleSaveCase() {
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
  savingCase.value = true
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
      const res = await createCaseAssignment(props.project.id, {
        test_case_ids: selectedCaseIds.value,
        task_id: caseForm.task_id,
        assigned_to: caseForm.assigned_to,
        status: caseForm.status,
        notes: caseForm.notes,
      })
      ElMessage.success(`分配完成：新增 ${res.created}，更新 ${res.updated}`)
    }
    caseDialogVisible.value = false
    fetchCaseAssignments()
    emit('change')
  } catch { /* 拦截器已 toast */ }
  finally { savingCase.value = false }
}

async function handleDeleteCase(row) {
  try {
    await ElMessageBox.confirm(`确定删除用例分配「${row.test_case_title || ''}」？`, '删除确认', { type: 'warning' })
  } catch { return }
  await deleteCaseAssignment(row.id)
  ElMessage.success('已删除')
  fetchCaseAssignments()
  emit('change')
}

onMounted(() => {
  fetchCaseAssignments()
  fetchTasksAndMembers()
})
watch(() => props.project.id, () => {
  fetchCaseAssignments()
  fetchTasksAndMembers()
})
</script>