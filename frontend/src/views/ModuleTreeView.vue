<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('module.title') }}</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="showDialog()">+ {{ t('module.title') }}</el-button>
      </div>
    </div>
    <div class="table-card">
    <el-table :data="modules" v-loading="loading" row-key="id" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" :label="t('module.name')" />
      <el-table-column prop="description" :label="t('module.desc')" show-overflow-tooltip />
      <el-table-column :label="t('common.operation')" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">{{ t('common.edit') }}</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && modules.length === 0" :description="t('module.empty')" :image-size="80" />
    </div>

    <el-dialog :title="editing.id ? t('common.edit') + ' / ' + t('module.name') : t('module.title')" v-model="dialogVisible" width="500px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item :label="t('module.name')" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="t('module.desc')">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item :label="t('module.parent')">
          <el-select v-model="form.parent" clearable :placeholder="t('module.noParent')">
            <el-option v-for="m in modules" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
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
import { getModules, createModule, updateModule, deleteModule } from '@/api/projects'
import { ElMessage, ElMessageBox } from 'element-plus'

const { t } = useI18n()
const route = useRoute()
const projectId = route.params.id
const loading = ref(false)
const modules = ref([])
const dialogVisible = ref(false)
const editing = reactive({})
const form = reactive({ name: '', description: '', parent: null })

const formRef = ref(null)
const rules = computed(() => ({
  name: [{ required: true, message: t('module.name'), trigger: 'blur' }],
})).value

async function fetchModules() {
  loading.value = true
  try {
    modules.value = await getModules(projectId)
  } finally {
    loading.value = false
  }
}

function showDialog(row) {
  if (row) {
    Object.assign(editing, row)
    form.name = row.name
    form.description = row.description
    form.parent = row.parent
  } else {
    Object.keys(editing).forEach(k => delete editing[k])
    form.name = ''
    form.description = ''
    form.parent = null
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (editing.id) {
      await updateModule(editing.id, { name: form.name, description: form.description, parent: form.parent })
      ElMessage.success(t('msg.updateSuccess'))
    } else {
      await createModule(projectId, { name: form.name, description: form.description, parent: form.parent })
      ElMessage.success(t('msg.createSuccess'))
    }
    dialogVisible.value = false
    fetchModules()
  } catch {
    /* 拦截器已 toast */
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `${t('common.delete')}「${row.name}」?`,
      t('common.confirm'),
      { type: 'warning' },
    )
  } catch { return }
  await deleteModule(row.id)
  ElMessage.success(t('msg.deleteSuccess'))
  fetchModules()
}

onMounted(fetchModules)
</script>