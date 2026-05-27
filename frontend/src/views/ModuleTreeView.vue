<template>
  <div class="page-container">
    <div class="page-header">
      <h2>模块管理</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="showDialog()">添加模块</el-button>
      </div>
    </div>
    <div class="table-card">
    <el-table :data="modules" v-loading="loading" row-key="id" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="模块名称" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <el-dialog :title="editing.id ? '编辑模块' : '添加模块'" v-model="dialogVisible" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="父模块">
          <el-select v-model="form.parent" clearable placeholder="无（顶级模块）">
            <el-option v-for="m in modules" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
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
import { getModules, createModule, updateModule, deleteModule } from '@/api/projects'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const projectId = route.params.id
const loading = ref(false)
const modules = ref([])
const dialogVisible = ref(false)
const editing = reactive({})
const form = reactive({ name: '', description: '', parent: null })

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
  if (editing.id) {
    await updateModule(editing.id, { name: form.name, description: form.description, parent: form.parent })
    ElMessage.success('更新成功')
  } else {
    await createModule(projectId, { name: form.name, description: form.description, parent: form.parent })
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  fetchModules()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除该模块？', '提示', { type: 'warning' })
  await deleteModule(row.id)
  ElMessage.success('删除成功')
  fetchModules()
}

onMounted(fetchModules)
</script>
