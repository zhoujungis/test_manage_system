<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header">
      <h2>缺陷详情 #{{ defect.id }}</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="editing = true" v-if="!editing">编辑</el-button>
        <el-button type="primary" @click="handleSave" v-if="editing">保存</el-button>
        <el-button @click="editing = false" v-if="editing">取消</el-button>
      </div>
    </div>
    <el-card>
      <template v-if="!editing">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题">{{ defect.title }}</el-descriptions-item>
          <el-descriptions-item label="项目">{{ defect.project_name }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="severityType(defect.severity)">{{ defect.severity }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(defect.status)">{{ statusLabel(defect.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建人">{{ defect.created_by_name }}</el-descriptions-item>
          <el-descriptions-item label="处理人">{{ defect.assigned_to_name || '未分配' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ defect.created_at?.slice(0, 19).replace('T', ' ') }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ defect.updated_at?.slice(0, 19).replace('T', ' ') }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ defect.description }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template v-else>
        <el-form :model="form" label-width="80px">
          <el-form-item label="标题" required>
            <el-input v-model="form.title" />
          </el-form-item>
          <el-form-item label="描述" required>
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
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getDefect, updateDefect } from '@/api/defects'
import { ElMessage } from 'element-plus'

const route = useRoute()
const defectId = route.params.did
const loading = ref(false)
const defect = ref({})
const editing = ref(false)
const form = reactive({ title: '', description: '', severity: 'S2', status: 'open' })

function severityType(s) {
  const map = { S0: 'danger', S1: 'danger', S2: 'warning', S3: 'info', S4: '' }
  return map[s] || ''
}
function statusLabel(s) {
  const map = { open: '未处理', in_progress: '处理中', resolved: '已修复', closed: '已关闭' }
  return map[s] || s
}
function statusType(s) {
  const map = { open: 'danger', in_progress: 'warning', resolved: 'success', closed: 'info' }
  return map[s] || 'info'
}

onMounted(async () => {
  loading.value = true
  try {
    defect.value = await getDefect(defectId)
    form.title = defect.value.title
    form.description = defect.value.description
    form.severity = defect.value.severity
    form.status = defect.value.status
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  await updateDefect(defectId, form)
  Object.assign(defect.value, form)
  editing.value = false
  ElMessage.success('更新成功')
}
</script>
