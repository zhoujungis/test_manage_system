<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ isNew ? '新建测试用例' : '编辑测试用例' }}</h2>
    </div>
    <el-card v-loading="loading">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="标题" required>
              <el-input v-model="form.title" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="产品线" required>
              <el-select v-model="form.product_line">
                <el-option label="摄像头" value="camera" />
                <el-option label="门铃" value="doorbell" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="类型">
              <el-select v-model="form.type">
                <el-option label="功能测试" value="functional" />
                <el-option label="接口测试" value="api" />
                <el-option label="UI测试" value="ui" />
                <el-option label="性能测试" value="performance" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="所属项目">
              <el-select v-model="form.project" filterable clearable @change="onProjectChange">
                <el-option v-for="p in projectList" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="功能模块">
              <el-select v-model="form.module" filterable clearable>
                <el-option v-for="m in moduleList" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="优先级">
              <el-select v-model="form.priority">
                <el-option label="P0-最高" value="P0" />
                <el-option label="P1-高" value="P1" />
                <el-option label="P2-中" value="P2" />
                <el-option label="P3-低" value="P3" />
                <el-option label="P4-最低" value="P4" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态">
              <el-select v-model="form.status">
                <el-option label="草稿" value="draft" />
                <el-option label="活跃" value="active" />
                <el-option label="已废弃" value="deprecated" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="前置条件">
          <el-input v-model="form.preconditions" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="测试步骤">
          <div v-for="(step, idx) in form.steps" :key="idx" style="margin-bottom: 12px; padding: 12px; background: #f5f7fa; border-radius: 4px">
            <el-row :gutter="12">
              <el-col :span="2"><el-tag>步骤{{ idx + 1 }}</el-tag></el-col>
              <el-col :span="10"><el-input v-model="step.action" placeholder="操作步骤" /></el-col>
              <el-col :span="10"><el-input v-model="step.expected_result" placeholder="预期结果" /></el-col>
              <el-col :span="2"><el-button type="danger" circle :icon="Delete" @click="removeStep(idx)" /></el-col>
            </el-row>
          </div>
          <el-button type="primary" @click="addStep">+ 添加步骤</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave">保存</el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTestCase, createTestCase, updateTestCase } from '@/api/testcases'
import { getProjects, getModules, getLibraryModules } from '@/api/projects'
import { ElMessage } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const testcaseId = route.params.tid
const isNew = computed(() => !testcaseId || testcaseId === 'new')
const isLibrary = computed(() => !route.path.startsWith('/projects/'))
const loading = ref(false)

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
  const data = {
    title: form.title,
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
