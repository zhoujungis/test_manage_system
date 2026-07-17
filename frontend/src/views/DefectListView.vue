<template>
  <div class="page-container">
    <div class="page-header">
      <h2>缺陷管理</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="showDialog()">新建缺陷</el-button>
      </div>
    </div>
    <div class="filter-card">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-select v-model="filters.status" placeholder="状态筛选" clearable @change="fetchData">
            <el-option label="未处理" value="open" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="已修复" value="resolved" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.severity" placeholder="严重程度" clearable @change="fetchData">
            <el-option label="S0-致命" value="S0" />
            <el-option label="S1-严重" value="S1" />
            <el-option label="S2-一般" value="S2" />
            <el-option label="S3-轻微" value="S3" />
            <el-option label="S4-建议" value="S4" />
          </el-select>
        </el-col>
      </el-row>
    </div>
    <div class="table-card">
    <el-table :data="defects" v-loading="loading" stripe @row-click="(row) => $router.push(`/projects/${projectId}/defects/${row.id}`)">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" show-overflow-tooltip />
      <el-table-column prop="severity" label="严重程度" width="100">
        <template #default="{ row }">
          <el-tag :type="severityType(row.severity)" size="small">{{ row.severity }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="defectStatusType(row.status)" size="small">{{ defectStatusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assigned_to_name" label="处理人" width="120" />
      <el-table-column prop="created_by_name" label="创建人" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ row.created_at?.slice(0, 19).replace('T', ' ') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click.stop="showDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click.stop="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <!-- C13 fix: 空态 -->
    <el-empty v-if="!loading && defects.length === 0" description="暂无缺陷" :image-size="80" />
    </div>

    <el-dialog :title="editing.id ? '编辑缺陷' : '新建缺陷'" v-model="dialogVisible" width="600px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="严重程度">
              <el-select v-model="form.severity">
                <el-option label="S0-致命" value="S0" />
                <el-option label="S1-严重" value="S1" />
                <el-option label="S2-一般" value="S2" />
                <el-option label="S3-轻微" value="S3" />
                <el-option label="S4-建议" value="S4" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status">
                <el-option label="未处理" value="open" />
                <el-option label="处理中" value="in_progress" />
                <el-option label="已修复" value="resolved" />
                <el-option label="已关闭" value="closed" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getDefects, createDefect, updateDefect, deleteDefect } from '@/api/defects'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const projectId = route.params.id
const loading = ref(false)
const defects = ref([])
const dialogVisible = ref(false)
const editing = reactive({})
const form = reactive({ title: '', description: '', severity: 'S2', status: 'open' })
const filters = reactive({ status: '', severity: '' })
// C12 fix: 真正的表单校验，不只是 HTML required
const formRef = ref(null)
const rules = {
  title: [{ required: true, message: '请输入缺陷标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入缺陷描述', trigger: 'blur' }],
}

function severityType(s) {
  const map = { S0: 'danger', S1: 'danger', S2: 'warning', S3: 'info', S4: '' }
  return map[s] || ''
}
function defectStatusLabel(s) {
  const map = { open: '未处理', in_progress: '处理中', resolved: '已修复', closed: '已关闭' }
  return map[s] || s
}
function defectStatusType(s) {
  const map = { open: 'danger', in_progress: 'warning', resolved: 'success', closed: 'info' }
  return map[s] || 'info'
}

async function fetchData() {
  loading.value = true
  try {
    const params = { project: projectId }
    if (filters.status) params.status = filters.status
    if (filters.severity) params.severity = filters.severity
    const res = await getDefects(params)
    defects.value = res.results || res
  } finally {
    loading.value = false
  }
}

function showDialog(row) {
  if (row) {
    Object.assign(editing, row)
    form.title = row.title
    form.description = row.description
    form.severity = row.severity
    form.status = row.status
  } else {
    Object.keys(editing).forEach(k => delete editing[k])
    form.title = ''
    form.description = ''
    form.severity = 'S2'
    form.status = 'open'
  }
  dialogVisible.value = true
}

async function handleSave() {
  // C12 fix: 走真正的 validate，否则空表单也能提交
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (editing.id) {
      await updateDefect(editing.id, form)
      ElMessage.success('更新成功')
    } else {
      await createDefect({ ...form, project: projectId })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {
    /* 拦截器已 toast */
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除缺陷「${row.title}」？该操作不可撤销。`,
      '删除确认',
      { type: 'warning' },
    )
  } catch {
    return  // 用户取消
  }
  try {
    await deleteDefect(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch {
    /* 拦截器已 toast */
  }
}

onMounted(fetchData)
</script>
