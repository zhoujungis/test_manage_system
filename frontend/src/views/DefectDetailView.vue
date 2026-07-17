<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header">
      <h2>{{ t('defect.detail') }} #{{ defect.id }}</h2>
      <div class="page-header__actions">
        <el-button type="primary" @click="editing = true" v-if="!editing">{{ t('common.edit') }}</el-button>
        <el-button type="primary" @click="handleSave" v-if="editing">{{ t('common.save') }}</el-button>
        <el-button @click="editing = false" v-if="editing">{{ t('common.cancel') }}</el-button>
      </div>
    </div>
    <el-card>
      <template v-if="!editing">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="t('defect.title')">{{ defect.title }}</el-descriptions-item>
          <el-descriptions-item :label="t('crumb.project')">{{ defect.project_name }}</el-descriptions-item>
          <el-descriptions-item :label="t('defect.severity')">
            <el-tag :type="severityType(defect.severity)">{{ defect.severity }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="t('defect.status')">
            <el-tag :type="defectStatusType(defect.status)">{{ defectStatusLabel(defect.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="t('defect.creator')">{{ defect.created_by_name }}</el-descriptions-item>
          <el-descriptions-item :label="t('defect.assignee')">{{ defect.assigned_to_name || t('common.unknown') }}</el-descriptions-item>
          <el-descriptions-item :label="t('defect.createdAt')">{{ formatDateTime(defect.created_at) }}</el-descriptions-item>
          <el-descriptions-item :label="t('defect.updatedAt')">{{ formatDateTime(defect.updated_at) }}</el-descriptions-item>
          <el-descriptions-item :label="t('defect.description')" :span="2">{{ defect.description }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template v-else>
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
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { getDefect, updateDefect } from '@/api/defects'
import { ElMessage } from 'element-plus'
import { useFormat } from '@/composables/useFormat'
import { formatDateTime } from '@/utils/dateFormat'

const { t } = useI18n()
const { severityType, defectStatusType, defectStatusLabel } = useFormat()
const route = useRoute()
const defectId = route.params.did
const loading = ref(false)
const defect = ref({})
const editing = ref(false)
const form = reactive({ title: '', description: '', severity: 'S2', status: 'open' })
const formRef = ref(null)
const rules = computed(() => ({
  title: [{ required: true, message: t('defect.title'), trigger: 'blur' }],
  description: [{ required: true, message: t('defect.description'), trigger: 'blur' }],
})).value
const severityLabels = computed(() => t('defect.severityLabels'))
const statusLabels = computed(() => t('status.defect'))

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
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    await updateDefect(defectId, form)
    Object.assign(defect.value, form)
    editing.value = false
    ElMessage.success(t('msg.updateSuccess'))
  } catch {
    /* 拦截器已 toast */
  }
}
</script>