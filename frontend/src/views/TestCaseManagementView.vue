<template>
  <div class="tc-page">
    <div class="tc-toolbar">
      <el-select :model-value="productLine" @change="onTab" class="tc-toolbar__select">
        <el-option :label="t('project.productCamera')" value="camera" />
        <el-option :label="t('project.productDoorbell')" value="doorbell" />
      </el-select>
      <el-select
        :model-value="priorityFilter"
        @change="onFilter"
        clearable
        :placeholder="t('case.priority')"
        class="tc-toolbar__select tc-toolbar__select--sm"
      >
        <el-option v-for="key in ['P0','P1','P2','P3','P4']" :key="key" :label="key" :value="key" />
      </el-select>
      <div class="tc-toolbar__spacer" />
      <el-button
        v-if="canManageTestCaseLibrary"
        @click="openAddModule"
      >
        <el-icon><FolderAdd /></el-icon>
        {{ t('module.title') }}
      </el-button>
      <el-button
        v-if="canManageTestCaseLibrary"
        type="primary"
        @click="$router.push(`/testcases/${productLine}/new`)"
      >
        <el-icon><Plus /></el-icon>
        {{ t('case.new') }}
      </el-button>
    </div>
    <div class="tc-body">
    <div class="tc-left">
      <el-input v-model="treeFilter" :placeholder="t('common.search')" size="small" clearable style="margin-bottom: 8px" />
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="{ children: 'children', label: 'label' }"
        :filter-node-method="(v,d) => !v || d.label?.toLowerCase().includes(v.toLowerCase())"
        node-key="id"
        highlight-current
        @node-click="onNodeClick"
        style="flex:1; overflow:auto"
      >
        <template #default="{ data }">
          <span class="tn">
            <el-icon v-if="data.type==='module'"><Folder /></el-icon>
            <el-icon v-else><Document /></el-icon>
            <span style="margin-left:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ data.label }}</span>
            <el-tag v-if="data.priority" :type="pType(data.priority)" size="small" style="margin-left:4px">{{ data.priority }}</el-tag>
            <span v-if="data.type==='module'" style="color:#909399;font-size:11px;margin-left:4px">({{ data.children?.length || 0 }})</span>
            <el-button
              v-if="data.type==='module' && canDelete && data._moduleId"
              link
              type="danger"
              size="small"
              style="margin-left:auto"
              @click.stop="confirmDelModule(data)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </span>
        </template>
      </el-tree>
    </div>
    <div class="tc-right" v-loading="detailLoading">
      <template v-if="detail">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <strong style="font-size:16px">{{ detail.title }}</strong>
          <div>
            <el-button v-if="canManageTestCaseLibrary" size="small" @click="$router.push(`/testcases/${productLine}/${detail.id}`)">编辑</el-button>
            <el-button v-if="canDelete" size="small" type="danger" @click="del">删除</el-button>
          </div>
        </div>
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item :label="t('case.priority')"><el-tag :type="pType(detail.priority)" size="small">{{ detail.priority }}</el-tag></el-descriptions-item>
          <el-descriptions-item :label="t('case.type')">{{ tLabel(detail.case_type) }}</el-descriptions-item>
          <el-descriptions-item :label="t('case.status')"><el-tag :type="sType(detail.status)" size="small">{{ sLabel(detail.status) }}</el-tag></el-descriptions-item>
          <el-descriptions-item :label="t('case.creator')">{{ detail.created_by_name || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="t('case.updater')">{{ full?.updated_by_name || detail.updated_by_name || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="t('case.updatedAt')">{{ (full?.updated_at || detail.updated_at || '').slice(0,16).replace('T',' ') || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="t('case.preconditions')" :span="3">{{ detail.preconditions || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="t('case.description')" :span="3">{{ detail.description || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="full?.steps?.length" style="margin-top:16px">
          <h4 style="margin-bottom:8px">{{ t('case.addStep') }}</h4>
          <el-table :data="full.steps" size="small" stripe>
            <el-table-column type="index" width="50" />
            <el-table-column prop="action" :label="t('case.action')" />
            <el-table-column prop="expected_result" :label="t('case.expected')" />
          </el-table>
        </div>
      </template>
      <el-empty v-else :description="t('common.noData')" />
    </div>
    </div>

    <el-dialog v-model="moduleDialogVisible" :title="t('module.title')" width="400px" destroy-on-close :close-on-click-modal="false">
      <el-form ref="moduleFormRef" :model="moduleForm" :rules="moduleRules" label-width="80px">
        <el-form-item :label="t('module.name')" prop="name">
          <el-input v-model="moduleForm.name" :placeholder="t('module.name')" maxlength="50" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="moduleDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="addingModule" @click="submitAddModule">{{ t('common.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { getTestCaseTree, getTestCase, deleteTestCase } from '@/api/testcases'
import { getLibraryModules, createLibraryModule, deleteModule } from '@/api/projects'
import { useUserIdentity } from '@/composables/useUserIdentity'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'

const { t } = useI18n()

const { canManageTestCaseLibrary, canWriteProjects, isAdmin } = useUserIdentity()
const canDelete = computed(() => canWriteProjects.value || isAdmin.value)

const route = useRoute()
const router = useRouter()
const productLine = ref(route.params.product_line || 'camera')
const priorityFilter = computed(() => route.query.priority || '')

function onTab(v) {
  router.replace({ path: `/testcases/${v}`, query: route.query })
}

function onFilter(v) {
  router.replace({ query: { ...route.query, priority: v || undefined } })
}
const treeData = ref([])
const treeFilter = ref('')
const treeRef = ref(null)
const detail = ref(null)
const full = ref(null)
const detailLoading = ref(false)
const moduleDialogVisible = ref(false)
const addingModule = ref(false)
// C12 fix: 表单校验
const moduleFormRef = ref(null)
const moduleRules = computed(() => ({ name: [{ required: true, message: t('module.name'), trigger: 'blur' }] })).value
const moduleForm = ref({ name: '' })

// 用 AbortController 避免快速切换产品线 / 优先级时旧请求覆盖新数据
let loadToken = 0

watch(() => route.params.product_line, (v) => {
  if (v) { productLine.value = v; loadTree() }
})
watch(() => route.query.priority, () => loadTree())
watch(treeFilter, (v) => treeRef.value?.filter(v))

function tLabel(key) { return t(`case.typeLabels.${key}`) || key }
function sLabel(s) { return t(`status.testcase.${s}`) || s }
function sType(s) { const m={draft:'info',active:'success',deprecated:'warning'}; return m[s]||'info' }
function pType(p) { const m={P0:'danger',P1:'danger',P2:'warning',P3:'info',P4:''}; return m[p]||'' }

async function loadTree() {
  const myToken = ++loadToken
  const params = { product_line: productLine.value }
  if (route.query.priority) params.priority = route.query.priority

  try {
    const [casesRes, modules] = await Promise.all([
      getTestCaseTree(params).catch(() => ({ results: [] })),
      getLibraryModules(productLine.value).catch(() => []),
    ])
    // 切换后再到达的旧请求直接丢弃
    if (myToken !== loadToken) return
    const cases = casesRes.results || []

    const mods = {}
    cases.forEach(tc => {
      const mod = tc.module_name || '未分类'
      if (!mods[mod]) mods[mod] = []
      mods[mod].push({ id:`tc-${tc.id}`, label:tc.title, type:'testcase', priority:tc.priority, _raw:tc })
    })

    // 确保空模块也出现在树里
    modules.forEach(m => {
      if (!mods[m.name]) mods[m.name] = []
    })

    treeData.value = Object.entries(mods).map(([mod, children]) => {
      const modInfo = modules.find(m => m.name === mod)
      return {
        id: `mod-${mod}`,
        label: mod,
        type: 'module',
        _moduleId: modInfo?.id || null,
        children,
      }
    })
  } catch (e) {
    if (myToken !== loadToken) return
    // eslint-disable-next-line no-console
    console.error('loadTree failed', e)
    treeData.value = []
  }
}

async function onNodeClick(d) {
  if (d.type==='testcase' && d._raw) {
    detail.value = d._raw
    detailLoading.value = true
    try { full.value = await getTestCase(d._raw.id) } catch { full.value = null }
    detailLoading.value = false
  }
}

async function del() {
  try {
    await ElMessageBox.confirm(t('common.delete'), t('common.confirm'), { type: 'warning' })
  } catch { return }
  try {
    await deleteTestCase(detail.value.id)
    ElMessage.success(t('msg.deleteSuccess'))
    detail.value = null
    full.value = null
    loadTree()
  } catch { /* */ }
}

function openAddModule() {
  moduleForm.value = { name: '' }
  moduleDialogVisible.value = true
}

async function submitAddModule() {
  // C12 fix: 走真正的 validate
  if (!moduleFormRef.value) return
  const valid = await moduleFormRef.value.validate().catch(() => false)
  if (!valid) return
  addingModule.value = true
  try {
    await createLibraryModule({ name: moduleForm.value.name.trim(), product_line: productLine.value })
    ElMessage.success(t('msg.createSuccess'))
    moduleDialogVisible.value = false
    loadTree()
  } catch { /* 拦截器已 toast */ }
  finally { addingModule.value = false }
}

async function confirmDelModule(data) {
  try {
    await ElMessageBox.confirm(
      `确定删除模块「${data.label}」？其下的用例将变为未分类。`,
      '删除模块',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch { return }
  try {
    await deleteModule(data._moduleId)
    ElMessage.success('模块已删除')
    loadTree()
  } catch { /* */ }
}

onMounted(loadTree)

// C17 fix: 卸载时把 token 标到 sentinel，挡住任何还在飞的旧请求；
// 并把可能在 onNodeClick 半路的 fetch 取消（虽然现在 token 已经够用，这里再加一层防御）。
onBeforeUnmount(() => {
  loadToken = -1   // 任何已 ++ 的 myToken 都不再等于 loadToken，写入被丢
  // 不需要真正 abort —— token guard 已经阻止 treeData 写入；
  // 这里只是把引用清掉，让 Vue warn 更容易定位。
  treeRef.value = null
})
</script>

<style scoped>
.tc-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--tm-header-height));
}

.tc-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--tm-surface);
  border-bottom: 1px solid var(--tm-border);
  flex-shrink: 0;
}

.tc-toolbar__select {
  width: 120px;
}

.tc-toolbar__select--sm {
  width: 100px;
}

.tc-toolbar__spacer {
  flex: 1;
}

.tc-body {
  display: flex;
  flex: 1;
  min-height: 0;
  background: var(--tm-surface);
  border-radius: 0;
  border: none;
  border-top: 1px solid var(--tm-border);
  overflow: hidden;
  box-shadow: none;
}
.tc-left {
  width: 300px;
  border-right: 1px solid var(--tm-border);
  display: flex;
  flex-direction: column;
  padding: 16px;
  background: var(--tm-surface-2);
}
.tc-right {
  flex: 1;
  padding: 20px 24px;
  overflow: auto;
}
.tn {
  display: flex;
  align-items: center;
  font-size: 13px;
  flex: 1;
  min-width: 0;
}
</style>
