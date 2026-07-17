<template>
  <div class="case-panel">
    <el-tabs v-model="activeSubTab" type="card">
      <el-tab-pane :label="t('project.caseAssignment')" name="assign">
        <div style="margin-bottom:12px;display:flex;gap:8px;align-items:center">
          <el-button type="primary" size="small" @click="showCaseDialog()">{{ t('project.assignCase') }}</el-button>
          <el-button size="small" @click="toggleAssignedTree">
            {{ assignedExpanded ? t('caseAssignment.collapseAll') : t('caseAssignment.expandAll') }}
          </el-button>
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
                <el-button size="small" @click.stop="showCaseDialog(data._raw)">{{ t('common.edit') }}</el-button>
                <el-button size="small" type="danger" @click.stop="handleDeleteCase(data._raw)">{{ t('common.delete') }}</el-button>
              </template>
            </span>
          </template>
        </el-tree>
      </el-tab-pane>

      <el-tab-pane :label="t('caseAssignment.reviewAll', { n: '' }).trim() || t('caseAssignment.reviewAll').split('(')[0]" name="review">
        <div style="margin-bottom:12px;display:flex;gap:8px;align-items:center">
          <el-button type="success" size="small" @click="batchApproveAll" :disabled="!reviewIds.length">
            {{ t('caseAssignment.reviewAll', { n: reviewIds.length }) }}
          </el-button>
          <el-button size="small" @click="toggleReviewTree">
            {{ reviewExpanded ? t('caseAssignment.collapseAll') : t('caseAssignment.expandAll') }}
          </el-button>
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
                <el-tag :type="assignmentStatusType(data._status)" size="small">{{ data._statusLabel }}</el-tag>
                <span>{{ data._assignedTo }}</span>
                <el-tag :type="approvalTagType(data._approvalRaw)" size="small">{{ approvalLabels[data._approvalRaw] }}</el-tag>
              </template>
              <span>{{ data.label }}</span>
              <span v-if="data._notes" style="color:#909399;font-size:11px">— {{ data._notes }}</span>
            </span>
          </template>
        </el-tree>
      </el-tab-pane>
    </el-tabs>

    <el-dialog :title="caseEditing.id ? t('common.edit') : t('project.assignCase')" v-model="caseDialogVisible" width="700px" @opened="onCaseDialogOpen" :close-on-click-modal="false">
      <el-input v-model="caseTreeFilter" :placeholder="t('common.search')" size="small" clearable style="margin-bottom:8px" />
      <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px">
        <el-button size="small" @click="selectAllCases">{{ t('plan.selectAll') }}</el-button>
        <el-button size="small" @click="deselectAllCases">{{ t('plan.deselectAll') }}</el-button>
        <el-checkbox v-model="filterAssignedCases" size="small" style="margin-left:auto">{{ t('plan.filterAssigned') }}</el-checkbox>
        <span style="color:#909399;font-size:12px">{{ t('caseAssignment.selected', { n: selectedCaseIds.length }) }}</span>
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
        <el-form-item :label="t('caseAssignment.linkTask')" prop="task_id">
          <el-select v-model="caseForm.task_id" :placeholder="t('task.title')" style="width:100%">
            <el-option v-for="t in openTasks" :key="t.id"
              :label="`${t.title}${t.round ? ' (' + t.round + ')' : ''}`" :value="t.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-form :model="caseForm" label-width="80px" inline>
        <el-form-item :label="t('caseAssignment.assignee')">
          <el-select v-model="caseForm.assigned_to" filterable style="width:200px">
            <el-option v-for="m in members" :key="m.user" :label="m.user_name" :value="m.user" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('caseAssignment.status')">
          <el-select v-model="caseForm.status" style="width:140px">
            <el-option v-for="(label, key) in assignmentStatusLabels" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('caseAssignment.notes')">
          <el-input v-model="caseForm.notes" style="width:220px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="savingCase" @click="handleSaveCase">
          {{ caseEditing.id ? t('common.save') : t('caseAssignment.batchAssign', { n: selectedCaseIds.length }) }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getCaseAssignments, createCaseAssignment, updateCaseAssignment,
  deleteCaseAssignment, batchApprove, getTasks, getMembers,
} from '@/api/projects'
import { useFormat } from '@/composables/useFormat'
import { Folder, Document, List } from '@element-plus/icons-vue'

const { t } = useI18n()
const { priorityType, assignmentStatusType } = useFormat()
const props = defineProps({ project: { type: Object, required: true } })
const emit = defineEmits(['change'])

const approvalLabels = computed(() => t('status.approval'))
const assignmentStatusLabels = computed(() => t('status.assignment'))
const APPROVAL_TAG = { pending: 'info', approved: 'success', rejected: 'danger' }
const approvalTagType = (s) => APPROVAL_TAG[s] || 'info'

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
        id: `task-${tKey}`,
        label: a.task_title || t('task.title'),
        type: 'task',
        children: [],
      }
    }
    tasksMap[tKey].children.push({
      id: `tc-${a.id}`, label: a.test_case_title, type: 'testcase',
      _priority: a.test_case_priority, _assignedTo: a.assigned_to_name, _notes: a.notes, _raw: a,
    })
  })
  caseAssignedTree.value = Object.values(tasksMap)
  if (assignedExpanded.value) {
    assignedExpandedKeys.value = caseAssignedTree.value.map((n) => n.id)
  }
}
function toggleAssignedTree() {
  assignedExpandedKeys.value = assignedExpanded.value ? [] : caseAssignedTree.value.map((n) => n.id)
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
        id: `task-${tKey}`,
        label: a.task_title || t('task.title'),
        type: 'task',
        children: [],
      }
    }
    tasksMap[tKey].children.push({
      id: `tc-${a.id}`, label: a.test_case_title, type: 'testcase',
      _priority: a.test_case_priority,
      _status: a.status,
      _statusLabel: assignmentStatusLabels.value[a.status] || a.status,
      _approvalRaw: a.approval_status,
      _assignedTo: a.assigned_to_name,
      _notes: a.notes,
    })
  })
  reviewTree.value = Object.values(tasksMap)
  if (reviewExpanded.value) {
    reviewExpandedKeys.value = reviewTree.value.map((n) => n.id)
  }
}
function toggleReviewTree() {
  reviewExpandedKeys.value = reviewExpanded.value ? [] : reviewTree.value.map((n) => n.id)
  reviewExpanded.value = !reviewExpanded.value
  reviewTreeKey.value++
}
async function batchApproveAll() {
  try {
    await ElMessageBox.confirm(`${t('common.confirm')} ${reviewIds.value.length}?`, t('common.confirm'), { type: 'warning' })
  } catch { return }
  const res = await batchApprove(props.project.id, reviewIds.value)
  ElMessage.success(`${t('msg.updateSuccess')}: ${res.updated || reviewIds.value.length}`)
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
const caseRules = computed(() => ({
  task_id: [{ required: true, message: t('caseAssignment.linkTask'), trigger: 'change' }],
})).value
const savingCase = ref(false)
const members = ref([])
const openTasks = computed(() => (tasks.value || []).filter((t) => t.status !== 'done'))
const tasks = ref([])

async function loadCaseTree() {
  const res = await getCaseAssignments(props.project.id, { all: 1 })
  const allIds = new Set((res.results || res).map((a) => a.test_case))
  caseTreeData.value = await fetchTestCaseTree()
  async function fetchTestCaseTree() {
    const { getTestCaseTree } = await import('@/api/testcases')
    const params = { product_line: props.project.product_line || 'camera' }
    const items = await getTestCaseTree(params).catch(() => ({ results: [] }))
    const mods = {}
    ;(items.results || []).forEach((tc) => {
      const m = tc.module_name || t('caseAssignment.notes')  // fallback 'misc'
      if (!mods[m]) mods[m] = []
      const assigned = allIds.has(tc.id) && filterAssignedCases.value
      if (filterAssignedCases.value && assigned) return
      mods[m].push({ id: `tc-${tc.id}`, label: tc.title, type: 'testcase', priority: tc.priority })
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
    if (!selectedCaseIds.value.length) { ElMessage.warning(t('caseAssignment.selectCases')); return }
    if (!caseFormRef.value) return
    const valid = await caseFormRef.value.validate().catch(() => false)
    if (!valid) return
  } else {
    if (!selectedCaseIds.value.length) { ElMessage.warning(t('caseAssignment.selectCases')); return }
    if (!caseFormRef.value) return
    const valid = await caseFormRef.value.validate().catch(() => false)
    if (!valid) return
    if (!caseForm.assigned_to) { ElMessage.warning(t('caseAssignment.selectAssignee')); return }
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
      ElMessage.success(t('msg.updateSuccess'))
    } else {
      const res = await createCaseAssignment(props.project.id, {
        test_case_ids: selectedCaseIds.value,
        task_id: caseForm.task_id,
        assigned_to: caseForm.assigned_to,
        status: caseForm.status,
        notes: caseForm.notes,
      })
      ElMessage.success(`${t('msg.createSuccess')}: ${res.created}/${res.updated}`)
    }
    caseDialogVisible.value = false
    fetchCaseAssignments()
    emit('change')
  } catch { /* 拦截器已 toast */ }
  finally { savingCase.value = false }
}

async function handleDeleteCase(row) {
  try {
    await ElMessageBox.confirm(`${t('common.delete')}「${row.test_case_title || ''}」?`, t('common.confirm'), { type: 'warning' })
  } catch { return }
  await deleteCaseAssignment(row.id)
  ElMessage.success(t('msg.deleteSuccess'))
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