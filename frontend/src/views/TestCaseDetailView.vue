<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ isNew ? t('case.new') : t('common.edit') + ' / ' + t('case.list') }}</h2>
    </div>
    <el-card v-loading="loading">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="t('case.title')" prop="title" required>
              <el-input v-model="form.title" maxlength="200" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item :label="t('case.productLine')" prop="product_line" required>
              <el-select v-model="form.product_line">
                <el-option :label="t('project.productCamera')" value="camera" />
                <el-option :label="t('project.productDoorbell')" value="doorbell" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item :label="t('case.type')" prop="type">
              <el-select v-model="form.type">
                <el-option v-for="(label, key) in typeLabels" :key="key" :label="label" :value="key" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item :label="t('crumb.project')">
              <el-select v-model="form.project" filterable clearable @change="onProjectChange">
                <el-option v-for="p in projectList" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item :label="t('case.module')">
              <el-select v-model="form.module" filterable clearable>
                <el-option v-for="m in moduleList" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item :label="t('case.priority')">
              <el-select v-model="form.priority">
                <el-option v-for="key in ['P0','P1','P2','P3','P4']" :key="key" :label="priorityLabel(key)" :value="key" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item :label="t('case.status')">
              <el-select v-model="form.status">
                <el-option v-for="(label, key) in statusLabels" :key="key" :label="label" :value="key" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item :label="t('case.preconditions')">
          <el-input v-model="form.preconditions" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item :label="t('case.description')">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="t('case.addStep')">
          <div v-for="(step, idx) in form.steps" :key="idx" style="margin-bottom: 12px; padding: 12px; background: var(--tm-surface-2); border-radius: 4px">
            <el-row :gutter="12">
              <el-col :span="2"><el-tag>{{ idx + 1 }}</el-tag></el-col>
              <el-col :span="10"><el-input v-model="step.action" :placeholder="t('case.action')" maxlength="500" /></el-col>
              <el-col :span="10"><el-input v-model="step.expected_result" :placeholder="t('case.expected')" maxlength="500" /></el-col>
              <el-col :span="2"><el-button type="danger" circle :icon="Delete" @click="removeStep(idx)" /></el-col>
            </el-row>
          </div>
          <el-button type="primary" @click="addStep">+ {{ t('case.addStep') }}</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">{{ t('common.save') }}</el-button>
          <el-button :disabled="saving" @click="goBack">{{ t('common.cancel') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { getTestCase, createTestCase, updateTestCase } from '@/api/testcases'
import { getProjects, getModules, getLibraryModules } from '@/api/projects'
import { ElMessage } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { useFormat } from '@/composables/useFormat'

const { t } = useI18n()
const { priorityLabel } = useFormat()
const route = useRoute()
const router = useRouter()
const testcaseId = route.params.tid
const isNew = computed(() => !testcaseId || testcaseId === 'new')
const isLibrary = computed(() => !route.path.startsWith('/projects/'))
const loading = ref(false)
const saving = ref(false)
const formRef = ref(null)
const typeLabels = computed(() => t('case.typeLabels'))
const statusLabels = computed(() => t('status.testcase'))

const rules = computed(() => ({
  title: [
    { required: true, message: t('case.title'), trigger: 'blur' },
    { min: 1, max: 200, message: t('case.title'), trigger: 'blur' },
  ],
  product_line: [
    { required: true, message: t('case.productLine'), trigger: 'change' },
  ],
  type: [
    { required: true, message: t('case.type'), trigger: 'change' },
  ],
})).value

const projectList = ref([])
const moduleList = ref([])

const productLine = route.params.product_line || 'camera'
const form = reactive({
  title: '',
  description: '',
  product_line: productLine,
  project: null,
  module: null,
  priority: 'P2',
  type: 'functional',
  status: 'draft',
  preconditions: '',
  steps: [],
})

async function fetchProjects() {
  try {
    const res = await getProjects()
    projectList.value = res.results || res
  } catch { /* */ }
}

async function loadModulesForLibrary() {
  try {
    moduleList.value = await getLibraryModules(productLine)
  } catch { moduleList.value = [] }
}

async function onProjectChange(pid) {
  form.module = null
  if (pid) {
    try { moduleList.value = await getModules(pid) } catch { moduleList.value = [] }
  } else if (isLibrary.value) {
    await loadModulesForLibrary()
  } else {
    moduleList.value = []
  }
}

function addStep() {
  form.steps.push({ step_number: form.steps.length + 1, action: '', expected_result: '' })
}

function removeStep(idx) {
  form.steps.splice(idx, 1)
  form.steps.forEach((s, i) => (s.step_number = i + 1))
}

async function handleSave() {
  if (saving.value) return
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请检查表单填写')
    return
  }
  saving.value = true
  const data = {
    title: form.title.trim(),
    description: form.description,
    product_line: form.product_line,
    project: form.project || null,
    module: form.module || null,
    priority: form.priority,
    type: form.type,
    status: form.status,
    preconditions: form.preconditions,
    steps: form.steps.map((s, i) => ({ step_number: i + 1, action: s.action, expected_result: s.expected_result })),
  }
  try {
    if (isNew.value) {
      await createTestCase(data)
      ElMessage.success('创建成功')
    } else {
      await updateTestCase(testcaseId, data)
      ElMessage.success('更新成功')
    }
    goBack()
  } catch {
    // error already shown by request interceptor
  } finally {
    saving.value = false
  }
}

function goBack() {
  const projectId = route.params.id
  if (projectId && route.path.startsWith('/projects/')) {
    router.push(`/projects/${projectId}/testcases`)
  } else {
    router.push(`/testcases/${form.product_line || productLine}`)
  }
}

onMounted(async () => {
  fetchProjects()
  if (isNew.value && isLibrary.value) {
    loadModulesForLibrary()
  }
  if (!isNew.value) {
    loading.value = true
    try {
      const data = await getTestCase(testcaseId)
      form.title = data.title
      form.description = data.description
      form.product_line = data.product_line
      form.priority = data.priority
      form.type = data.type
      form.status = data.status
      form.preconditions = data.preconditions
      form.project = data.project
      form.steps = data.steps || []
      if (data.project) {
        await onProjectChange(data.project)
      } else if (isLibrary.value) {
        await loadModulesForLibrary()
      }
      form.module = data.module
    } finally {
      loading.value = false
    }
  }
})
</script>
