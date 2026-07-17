<template>
  <div class="exec-page">
    <!-- 顶栏 -->
    <header class="exec-topbar">
      <div class="exec-topbar__left">
        <el-button text @click="$router.push('/tm')">
          <el-icon><ArrowLeft /></el-icon>
          我的项目
        </el-button>
        <span class="exec-topbar__divider" />
        <h1 class="exec-topbar__title">{{ pageTitle }}</h1>
      </div>
      <div class="exec-topbar__stats">
        <span class="exec-stat exec-stat--total">共 {{ totalCases }} 条</span>
        <span class="exec-stat exec-stat--pass">Pass {{ statCounts.passed }}</span>
        <span class="exec-stat exec-stat--fail">Fail {{ statCounts.failed }}</span>
        <span class="exec-stat exec-stat--pending">待测 {{ statCounts.pending }}</span>
      </div>
    </header>

    <div class="exec-body">
      <!-- 左侧用例树 -->
      <aside class="exec-sidebar">
        <div class="exec-sidebar__toolbar">
          <el-input v-model="treeSearch" placeholder="搜索用例..." clearable size="small" prefix-icon="Search" />
          <div class="exec-sidebar__actions">
            <el-button size="small" @click="filterDialogVisible = true">
              <el-icon><Filter /></el-icon>
            </el-button>
            <el-button size="small" @click="toggleTree">{{ treeExpanded ? '收起' : '展开' }}</el-button>
          </div>
        </div>
        <el-tree
          ref="treeRef"
          :data="filteredTree"
          :props="{ children: 'children', label: 'label' }"
          node-key="id"
          highlight-current
          :filter-node-method="filterTreeNode"
          :default-expanded-keys="expandedKeys"
          :key="treeKey"
          class="exec-tree"
          @node-click="onNodeClick"
        >
          <template #default="{ data }">
            <span class="exec-tree-node" :class="{ 'is-case': data.type === 'testcase' }">
              <el-icon v-if="data.type === 'module'"><Folder /></el-icon>
              <el-icon v-else><Document /></el-icon>
              <span class="exec-tree-node__label">{{ data.label }}</span>
              <el-tag v-if="data._taskTitle" size="small" effect="plain" type="">{{ data._taskTitle }}{{ data._taskRound ? ' · ' + data._taskRound : '' }}</el-tag>
              <el-tag v-if="data._status" :type="statusTagType(data._rawStatus)" size="small" effect="light">
                {{ statusLabel(data._rawStatus) }}
              </el-tag>
            </span>
          </template>
        </el-tree>
      </aside>

      <!-- 右侧详情 -->
      <main class="exec-main" v-loading="detailLoading">
        <template v-if="fullCase && assignmentId">
          <div class="exec-main__header">
            <div>
              <h2 class="exec-case-title">{{ fullCase.title }}</h2>
              <div class="exec-case-meta">
                <el-tag :type="priorityType(fullCase.priority)" size="small">{{ fullCase.priority }}</el-tag>
                <span>{{ fullCase.module_name || '未分类' }}</span>
                <span>{{ typeLabel(fullCase.case_type) }}</span>
                <template v-if="taskInfo">
                  <span style="color:#909399">|</span>
                  <el-tag size="small" effect="plain" style="color:#409eff">{{ taskInfo }}</el-tag>
                </template>
              </div>
            </div>
            <div class="exec-status-bar">
              <span class="exec-status-bar__label">测试结果</span>
              <el-radio-group v-model="execStatus" size="small" @change="saveStatus('status')">
                <el-radio-button value="pending">待测试</el-radio-button>
                <el-radio-button value="passed">Pass</el-radio-button>
                <el-radio-button value="failed">Fail</el-radio-button>
                <el-radio-button value="not_applicable">N/A</el-radio-button>
                <el-radio-button value="not_tested">N/T</el-radio-button>
              </el-radio-group>
              <el-tag
                :type="approvalStatus === 'approved' ? 'success' : approvalStatus === 'rejected' ? 'danger' : 'info'"
                size="small"
                effect="plain"
              >
                审核：{{ approvalLabels[approvalStatus] }}
              </el-tag>
            </div>
          </div>

          <!-- 用例说明 -->
          <section class="exec-section">
            <h3 class="exec-section__title">
              <el-icon><InfoFilled /></el-icon>
              用例说明
            </h3>
            <div class="exec-info-card">
              <div v-if="fullCase.preconditions" class="exec-info-row">
                <span class="exec-info-row__label">前置条件</span>
                <p class="exec-info-row__text">{{ fullCase.preconditions }}</p>
              </div>
              <div class="exec-info-row">
                <span class="exec-info-row__label">用例描述</span>
                <p class="exec-info-row__text">{{ fullCase.description || '（无）' }}</p>
              </div>
            </div>
          </section>

          <!-- 测试步骤 -->
          <section class="exec-section">
            <h3 class="exec-section__title">
              <el-icon><List /></el-icon>
              测试步骤
              <span class="exec-section__count">{{ fullCase.steps?.length || 0 }} 步</span>
            </h3>
            <div v-if="fullCase.steps?.length" class="exec-steps">
              <div v-for="step in fullCase.steps" :key="step.step_number" class="exec-step">
                <div class="exec-step__num">{{ step.step_number }}</div>
                <div class="exec-step__body">
                  <div class="exec-step__action">
                    <span class="exec-step__tag">操作</span>
                    {{ step.action }}
                  </div>
                  <div class="exec-step__expected">
                    <span class="exec-step__tag exec-step__tag--ok">预期</span>
                    {{ step.expected_result }}
                  </div>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无测试步骤" :image-size="64" />
          </section>

          <!-- 执行说明 -->
          <section class="exec-section">
            <div class="exec-section__head">
              <h3 class="exec-section__title">
                <el-icon><EditPen /></el-icon>
                执行说明
              </h3>
              <el-button type="primary" size="small" :loading="savingNotes" @click="saveNotes">保存说明</el-button>
            </div>
            <p class="exec-section__hint">记录本次执行过程、实际结果、环境问题等，便于审核与追溯。</p>
            <el-input
              v-model="execNotes"
              type="textarea"
              :rows="5"
              placeholder="例如：按步骤操作后功能正常；第 2 步出现超时需复测…"
              maxlength="5000"
              show-word-limit
            />
          </section>

          <!-- 附件 -->
          <section class="exec-section">
            <div class="exec-section__head">
              <h3 class="exec-section__title">
                <el-icon><Paperclip /></el-icon>
                附件
                <span class="exec-section__count">{{ attachments.length }}</span>
              </h3>
              <el-upload
                ref="uploadRefEl"
                :show-file-list="false"
                :auto-upload="false"
                :disabled="uploading"
                multiple
                @change="onFileSelect"
              >
                <el-button type="primary" size="small" :loading="uploading">
                  <el-icon><Upload /></el-icon>
                  上传附件
                </el-button>
              </el-upload>
            </div>
            <p class="exec-section__hint">支持截图、日志、视频等，单文件不超过 15MB。</p>
            <div v-if="attachments.length" class="exec-attachments">
              <div v-for="att in attachments" :key="att.id" class="exec-attachment">
                <el-icon class="exec-attachment__icon"><Document /></el-icon>
                <div class="exec-attachment__info">
                  <a :href="att.file_url" target="_blank" rel="noopener" class="exec-attachment__name">
                    {{ att.original_name }}
                  </a>
                  <span class="exec-attachment__meta">
                    {{ formatSize(att.file_size) }}
                    · {{ att.uploaded_by_name || '未知' }}
                    · {{ formatTime(att.created_at) }}
                  </span>
                </div>
                <el-button text type="danger" size="small" @click="removeAttachment(att)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <el-empty v-else description="暂无附件，可上传截图或日志" :image-size="56" />
          </section>
        </template>

        <div v-else class="exec-empty">
          <el-empty description="从左侧选择一条用例开始执行">
            <template #image>
              <el-icon :size="64" color="#c0c4cc"><Pointer /></el-icon>
            </template>
          </el-empty>
        </div>
      </main>
    </div>

    <el-dialog title="筛选条件" v-model="filterDialogVisible" width="480px" append-to-body :close-on-click-modal="false">
      <el-form label-width="80px">
        <el-form-item label="任务">
          <el-select v-model="filterTask" style="width:100%" clearable placeholder="全部任务">
            <el-option v-for="t in tasks" :key="t.id"
              :label="`${t.title}${t.round ? ' (' + t.round + ')' : ''}`" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行人">
          <el-select v-model="filterAssignee" style="width:100%">
            <el-option label="我的用例" :value="auth.user?.id" />
            <el-option v-for="m in members" :key="m.user" :label="m.user_name" :value="m.user" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-checkbox-group v-model="filterPriority">
            <el-checkbox label="P0">P0</el-checkbox>
            <el-checkbox label="P1">P1</el-checkbox>
            <el-checkbox label="P2">P2</el-checkbox>
            <el-checkbox label="P3">P3</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="测试状态">
          <el-checkbox-group v-model="filterStatus">
            <el-checkbox label="passed">Pass</el-checkbox>
            <el-checkbox label="failed">Fail</el-checkbox>
            <el-checkbox label="not_applicable">N/A</el-checkbox>
            <el-checkbox label="not_tested">N/T</el-checkbox>
            <el-checkbox label="pending">待测试</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="审核状态">
          <el-checkbox-group v-model="filterApproval">
            <el-checkbox label="pending">未审核</el-checkbox>
            <el-checkbox label="approved">审核通过</el-checkbox>
            <el-checkbox label="rejected">审核不通过</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="filterDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="applyFilter">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import {
  getProject,
  getMembers,
  getTasks,
  getCaseAssignments,
  getCaseAssignment,
  updateCaseAssignment,
  uploadAssignmentAttachment,
  deleteAssignmentAttachment,
} from '@/api/projects'
import { getTestCase } from '@/api/testcases'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const auth = useAuthStore()
const projectId = route.params.id
const routeTaskId = route.query.task_id

const projectName = ref('')
const currentTaskTitle = ref('')
const pageTitle = computed(() => {
  if (currentTaskTitle.value) return `${projectName.value} · ${currentTaskTitle.value}`
  return projectName.value
})
const totalCases = ref(0)
const caseTree = ref([])
const members = ref([])
const tasks = ref([])
const treeSearch = ref('')
const treeRef = ref(null)

const filterDialogVisible = ref(false)
const filterAssignee = ref(auth.user?.id)
const filterStatus = ref(['passed', 'failed', 'not_applicable', 'not_tested', 'pending'])
const filterApproval = ref(['pending', 'approved', 'rejected'])
const filterPriority = ref(['P0', 'P1', 'P2', 'P3'])
const filterTask = ref(routeTaskId ? Number(routeTaskId) : null)

const treeExpanded = ref(true)
const treeKey = ref(0)
const expandedKeys = ref([])

const fullCase = ref(null)
const execStatus = ref('pending')
const approvalStatus = ref('pending')
const execNotes = ref('')
const attachments = ref([])
const detailLoading = ref(false)
const assignmentId = ref(null)
// F4 fix: 防御 stale response —— 切换节点后只接受最新一次请求的回包
const pendingDetail = ref(0)
const taskInfo = ref('')
const savingNotes = ref(false)
const uploading = ref(false)
const uploadRefEl = ref(null)   // C11 fix: 拿到 upload ref 才能 clearFiles()

const statCounts = ref({ passed: 0, failed: 0, pending: 0 })
// C13 fix: 区分「还在加载」和「真的空」；右侧详情面板空态
const rightPanelLoaded = ref(false)

// M21 fix: 树标签统一用中文，与右侧详情面板一致
const statusLabels = {
  pending: '待测试',
  passed: '通过',
  failed: '失败',
  not_applicable: '不适用',
  not_tested: '未测试',
  blocked: '阻塞',
  skip: '跳过',
}
// M21 fix: 之前未定义函数，模板引用了 statusLabel() —— 这里补一个同名的工具函数
function statusLabel(s) {
  return statusLabels[s] || s
}
const approvalLabels = { pending: '未审核', approved: '审核通过', rejected: '审核不通过' }

const filteredTree = computed(() => caseTree.value)

watch(treeSearch, (v) => {
  treeRef.value?.filter(v)
})

function filterTreeNode(value, data) {
  if (!value) return true
  return data.label?.toLowerCase().includes(value.toLowerCase())
}

function statusTagType(s) {
  const m = { passed: 'success', failed: 'danger', pending: 'info', not_applicable: '', not_tested: 'info' }
  return m[s] || 'info'
}

function priorityType(p) {
  const m = { P0: 'danger', P1: 'warning', P2: '', P3: 'info' }
  return m[p] || 'info'
}

function typeLabel(t) {
  const m = { functional: '功能测试', api: '接口测试', ui: 'UI测试', performance: '性能测试' }
  return m[t] || t
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatTime(iso) {
  if (!iso) return ''
  return String(iso).slice(0, 16).replace('T', ' ')
}

function computeStats(items) {
  statCounts.value = {
    passed: items.filter((a) => a.status === 'passed').length,
    failed: items.filter((a) => a.status === 'failed').length,
    pending: items.filter((a) => ['pending', 'not_tested'].includes(a.status)).length,
  }
}

async function loadData() {
  try {
    const proj = await getProject(projectId)
    projectName.value = proj.name
    const params = { assigned_to: filterAssignee.value }
    if (filterTask.value) params.task_id = filterTask.value
    // H41 fix: 反转过滤语义 —— 之前「< 5 个就不过滤」意味着「uncheck 全部 = 不过滤 = 显示全部」，
    // 反直觉。现在统一：勾选列表 = 包含；空 = 不传该 filter（不过滤）。
    if (filterStatus.value.length) params.status = filterStatus.value.join(',')
    if (filterPriority.value.length) params.priority = filterPriority.value.join(',')
    if (filterApproval.value.length) params.approval_status = filterApproval.value.join(',')
    const items = await getCaseAssignments(projectId, params)
    totalCases.value = items.length
    computeStats(items)
    const mods = {}
    items.forEach((a) => {
      const mod = a.test_case_module || '未分类'
      if (!mods[mod]) mods[mod] = []
      mods[mod].push(a)
    })
    const keys = []
    caseTree.value = Object.entries(mods).map(([mod, list]) => {
      const mk = `ex-mod-${mod}`
      keys.push(mk)
      return {
        id: mk,
        label: mod,
        type: 'module',
        children: list.map((a) => {
          const ak = `ex-case-${a.id}`
          keys.push(ak)
          return {
            id: ak,
            label: a.test_case_title,
            type: 'testcase',
            _status: statusLabels[a.status] || a.status,
            _rawStatus: a.status,
            _rawApproval: a.approval_status,
            _assignmentId: a.id,
            _tcId: a.test_case,
            _taskTitle: a.task_title,
            _taskRound: a.task_round,
          }
        }),
      }
    })
    expandedKeys.value = keys
    treeExpanded.value = true
    treeKey.value++
  } catch {
    /* */
  }
}

function applyFilter() {
  filterDialogVisible.value = false
  loadData()
}

function toggleTree() {
  if (treeExpanded.value) {
    expandedKeys.value = []
  } else {
    const keys = []
    function collect(nodes) {
      nodes.forEach((n) => {
        keys.push(n.id)
        if (n.children) collect(n.children)
      })
    }
    collect(caseTree.value)
    expandedKeys.value = keys
  }
  treeExpanded.value = !treeExpanded.value
  treeKey.value++
}

async function onNodeClick(node) {
  if (node.type !== 'testcase') return
  detailLoading.value = true
  // F4 fix: generation token 防 stale response —— 用户连点 A、B、A，三个请求同时飞回，
  // 先回来的不一定最后点的，会把上一个 case 的状态写到当前选中的 assignment。
  const reqToken = ++pendingDetail.value
  assignmentId.value = node._assignmentId
  if (node._taskTitle) {
    taskInfo.value = node._taskTitle + (node._taskRound ? ' · ' + node._taskRound : '')
  } else {
    taskInfo.value = ''
  }
  try {
    const [tc, assignment] = await Promise.all([
      getTestCase(node._tcId),
      getCaseAssignment(node._assignmentId),
    ])
    if (reqToken !== pendingDetail.value) return  // 已经有更新的请求，丢掉
    fullCase.value = tc
    execStatus.value = node._rawStatus
    approvalStatus.value = node._rawApproval
    execNotes.value = assignment.notes || ''
    attachments.value = assignment.attachments || []
  } catch {
    if (reqToken !== pendingDetail.value) return
    fullCase.value = null
    attachments.value = []
  }
  if (reqToken === pendingDetail.value) detailLoading.value = false
}

async function saveStatus(field) {
  if (!assignmentId.value) return
  const data = field === 'status' ? { status: execStatus.value } : { approval_status: approvalStatus.value }
  try {
    await updateCaseAssignment(assignmentId.value, data)
    // C15 fix: 之前还会调 loadData() → 全量重渲染 + treeKey++ → 丢展开/滚动/高亮。
    // 现在 syncTreeNode() 已经更新节点 _status；再原地重算 stats 即可。
    syncTreeNode()
    recomputeStatCounts()
    ElMessage.success('测试结果已保存')
  } catch {
    /* */
  }
}

function syncTreeNode() {
  // 同步当前节点的 status / approval_status（两个字段独立保存）
  for (const mod of caseTree.value) {
    for (const child of mod.children || []) {
      if (child._assignmentId === assignmentId.value) {
        child._status = statusLabels[execStatus.value]
        child._rawStatus = execStatus.value
        child._rawApproval = approvalStatus.value
      }
    }
  }
}

function recomputeStatCounts() {
  // 从内存中的 caseTree 重算统计，不重新拉接口
  const counts = { passed: 0, failed: 0, pending: 0, blocked: 0, skip: 0, not_tested: 0, not_applicable: 0 }
  for (const mod of caseTree.value) {
    for (const child of mod.children || []) {
      if (child._rawStatus in counts) counts[child._rawStatus] += 1
    }
  }
  statCounts.value = {
    passed: counts.passed,
    failed: counts.failed,
    pending: counts.pending + counts.not_tested + counts.not_applicable + counts.blocked + counts.skip,
  }
}

async function saveNotes() {
  if (!assignmentId.value) return
  savingNotes.value = true
  try {
    await updateCaseAssignment(assignmentId.value, { notes: execNotes.value })
    ElMessage.success('执行说明已保存')
  } finally {
    savingNotes.value = false
  }
}

async function onFileSelect(uploadFile, uploadFiles) {
  // C11 fix: <el-upload multiple> 会传 file 数组；原实现只读 uploadFile?.raw → 选 3 个只上传 1 个。
  // 同时清空 upload ref 的 fileList，否则连选同一文件不会触发 change。
  const uploadRef = uploadRefEl.value
  const list = Array.isArray(uploadFiles) && uploadFiles.length ? uploadFiles : [uploadFile]
  if (!assignmentId.value || !list.length) return
  uploading.value = true
  let success = 0
  let failed = 0
  try {
    for (const f of list) {
      const raw = f?.raw
      if (!raw) continue
      try {
        const att = await uploadAssignmentAttachment(assignmentId.value, raw)
        attachments.value = [att, ...attachments.value]
        success += 1
      } catch {
        failed += 1
      }
    }
    if (success && !failed) ElMessage.success(`已上传 ${success} 个附件`)
    else if (success && failed) ElMessage.warning(`成功 ${success} 个，失败 ${failed} 个`)
    else if (failed) ElMessage.error(`上传失败 ${failed} 个`)
  } finally {
    uploading.value = false
    // C36 fix: 清空 fileList 让用户能再次选同一文件
    if (uploadRef?.clearFiles) uploadRef.clearFiles()
  }
}

async function removeAttachment(att) {
  await ElMessageBox.confirm(`删除附件「${att.original_name}」？`, '确认', { type: 'warning' })
  try {
    await deleteAssignmentAttachment(assignmentId.value, att.id)
    attachments.value = attachments.value.filter((a) => a.id !== att.id)
    ElMessage.success('已删除')
  } catch {
    /* */
  }
}

onMounted(async () => {
  const role = auth.user?.role || auth.user?.profile?.role
  if (role !== 'tester') {
    try {
      members.value = await getMembers(projectId)
    } catch {
      /* */
    }
  }
  try {
    tasks.value = await getTasks(projectId)
    if (filterTask.value) {
      const t = tasks.value.find(t => t.id === filterTask.value)
      if (t) currentTaskTitle.value = t.round ? `${t.title} (${t.round})` : t.title
    }
  } catch {
    /* */
  }
  loadData()
})
// C17 fix: 卸载时让所有 in-flight 请求被 token guard 丢掉
onBeforeUnmount(() => {
  pendingDetail.value = -1
})
</script>

<style scoped>
.exec-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--tm-header-height));
  background: var(--tm-bg);
}

.exec-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--tm-surface);
  border-bottom: 1px solid var(--tm-border);
  flex-shrink: 0;
  gap: 16px;
  flex-wrap: wrap;
}

.exec-topbar__left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.exec-topbar__divider {
  width: 1px;
  height: 20px;
  background: var(--tm-border);
}

.exec-topbar__title {
  font-size: 18px;
  font-weight: 700;
  color: var(--tm-text);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.exec-topbar__stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.exec-stat {
  font-size: 13px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 6px;
  background: var(--tm-border-light);
  color: var(--tm-text-secondary);
}

.exec-stat--pass {
  background: #ecfdf5;
  color: #059669;
}

.exec-stat--fail {
  background: #fef2f2;
  color: #dc2626;
}

.exec-stat--pending {
  background: #eff6ff;
  color: #2563eb;
}

.exec-body {
  display: flex;
  flex: 1;
  min-height: 0;
  margin: 16px;
  gap: 0;
  background: var(--tm-surface);
  border: 1px solid var(--tm-border);
  border-radius: var(--tm-radius-lg);
  overflow: hidden;
  box-shadow: var(--tm-shadow);
}

.exec-sidebar {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--tm-border);
  background: #f8fafc;
}

.exec-sidebar__toolbar {
  padding: 12px;
  border-bottom: 1px solid var(--tm-border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.exec-sidebar__actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.exec-tree {
  flex: 1;
  overflow: auto;
  padding: 8px;
  background: transparent;
}

.exec-tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 2px 0;
  max-width: 100%;
}

.exec-tree-node__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.exec-main {
  flex: 1;
  overflow: auto;
  padding: 20px 24px;
}

.exec-main__header {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--tm-border);
}

.exec-case-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--tm-text);
  margin: 0 0 8px;
}

.exec-case-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--tm-text-secondary);
}

.exec-status-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.exec-status-bar__label {
  font-size: 13px;
  font-weight: 600;
  color: var(--tm-text-secondary);
}

.exec-section {
  margin-bottom: 28px;
}

.exec-section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.exec-section__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--tm-text);
  margin: 0 0 12px;
}

.exec-section__head .exec-section__title {
  margin-bottom: 0;
}

.exec-section__count {
  font-size: 12px;
  font-weight: 500;
  color: var(--tm-text-muted);
  margin-left: 4px;
}

.exec-section__hint {
  font-size: 13px;
  color: var(--tm-text-muted);
  margin: 0 0 12px;
  line-height: 1.5;
}

.exec-info-card {
  background: #f8fafc;
  border: 1px solid var(--tm-border);
  border-radius: var(--tm-radius);
  padding: 16px;
}

.exec-info-row {
  margin-bottom: 12px;
}

.exec-info-row:last-child {
  margin-bottom: 0;
}

.exec-info-row__label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--tm-text-muted);
  margin-bottom: 6px;
}

.exec-info-row__text {
  font-size: 14px;
  color: var(--tm-text);
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
}

.exec-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.exec-step {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  background: #f8fafc;
  border: 1px solid var(--tm-border);
  border-radius: var(--tm-radius);
}

.exec-step__num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--tm-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.exec-step__body {
  flex: 1;
  min-width: 0;
}

.exec-step__action,
.exec-step__expected {
  font-size: 14px;
  line-height: 1.6;
  color: var(--tm-text);
}

.exec-step__expected {
  margin-top: 10px;
  color: var(--tm-text-secondary);
}

.exec-step__tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background: #e2e8f0;
  color: var(--tm-text-secondary);
  margin-right: 8px;
}

.exec-step__tag--ok {
  background: #d1fae5;
  color: #047857;
}

.exec-attachments {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.exec-attachment {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: #f8fafc;
  border: 1px solid var(--tm-border);
  border-radius: var(--tm-radius);
}

.exec-attachment__icon {
  font-size: 22px;
  color: var(--tm-primary);
}

.exec-attachment__info {
  flex: 1;
  min-width: 0;
}

.exec-attachment__name {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--tm-primary);
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.exec-attachment__name:hover {
  text-decoration: underline;
}

.exec-attachment__meta {
  font-size: 12px;
  color: var(--tm-text-muted);
}

.exec-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 360px;
}
</style>
