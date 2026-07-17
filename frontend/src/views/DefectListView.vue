<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('defect.list') }}</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="showDialog()">{{ t('defect.new') }}</el-button>
      </div>
    </div>
    <div class="filter-card">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-select v-model="filters.status" :placeholder="t('defect.filterStatus')" clearable @change="fetchData">
            <el-option :label="t('status.defect.open')" value="open" />
            <el-option :label="t('status.defect.in_progress')" value="in_progress" />
            <el-option :label="t('status.defect.resolved')" value="resolved" />
            <el-option :label="t('status.defect.closed')" value="closed" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.severity" :placeholder="t('defect.severity')" clearable @change="fetchData">
            <el-option v-for="(label, key) in severityLabels" :key="key" :label="label" :value="key" />
          </el-select>
        </el-col>
      </el-row>
    </div>
    <div class="table-card">
    <el-table :data="defects" v-loading="loading" stripe @row-click="(row) => $router.push(`/projects/${projectId}/defects/${row.id}`)">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" :label="t('defect.title')" show-overflow-tooltip />
      <el-table-column prop="severity" :label="t('defect.severity')" width="100">
        <template #default="{ row }">
          <el-tag :type="severityType(row.severity)" size="small">{{ row.severity }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('defect.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="defectStatusType(row.status)" size="small">{{ defectStatusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assigned_to_name" :label="t('defect.assignee')" width="120" />
      <el-table-column prop="created_by_name" :label="t('defect.creator')" width="120" />
      <el-table-column prop="created_at" :label="t('defect.createdAt')" width="170">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column :label="t('common.operation')" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click.stop="showDialog(row)">{{ t('common.edit') }}</el-button>
          <el-button size="small" type="danger" @click.stop="handleDelete(row)">{{ t('common.delete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && defects.length === 0" :description="t('common.noData')" :image-size="80" />
    </div>

    <el-dialog :title="editing.id ? t('common.edit') + t('defect.list') : t('defect.new')" v-model="dialogVisible" width="600px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item :label="t('defect.title')" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item :label="t('defect.description')" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="t('defect.severity')">
              <el-select v-model="form.severity">
                <el-option v-for="(label, key) in severityLabels" :key="key" :label="label" :value="key" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="t('defect.status')">
              <el-select v-model="form.status">
                <el-option v-for="(label, key) in statusLabels" :key="key" :label="label" :value="key" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSave">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { getDefects, createDefect, updateDefect, deleteDefect } from '@/api/defects'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFormat } from '@/composables/useFormat'
import { formatDateTime } from '@/utils/dateFormat'

const { t } = useI18n()
const { severityType, defectStatusType, defectStatusLabel } = useFormat()
const route = useRoute()
const projectId = route.params.id
const loading = ref(false)
const defects = ref([])
const dialogVisible = ref(false)
const editing = reactive({})
const form = reactive({ title: '', description: '', severity: 'S2', status: 'open' })
const filters = reactive({ status: '', severity: '' })

const formRef = ref(null)
const rules = computed(() => ({
  title: [{ required: true, message: t('defect.title'), trigger: 'blur' }],
  description: [{ required: true, message: t('defect.description'), trigger: 'blur' }],
})).value

const severityLabels = computed(() => t('defect.severityLabels'))
const statusLabels = computed(() => t('status.defect'))

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
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (editing.id) {
      await updateDefect(editing.id, form)
      ElMessage.success(t('msg.updateSuccess'))
    } else {
      await createDefect({ ...form, project: projectId })
      ElMessage.success(t('msg.createSuccess'))
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
      `${t('common.delete')}${t('defect.list')}「${row.title}」？${t('defect.title') === '标题' ? '该操作不可撤销。' : ''}`,
      t('common.confirm'),
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await deleteDefect(row.id)
    ElMessage.success(t('msg.deleteSuccess'))
    fetchData()
  } catch {
    /* 拦截器已 toast */
  }
}

onMounted(fetchData)
</script>