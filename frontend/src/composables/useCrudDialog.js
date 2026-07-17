// H24 fix: 7 个 view 复制 CRUD 对话框模板（dialogVisible + editing + reactive form +
// showDialog + handleSave + handleDelete），抽成 composable 统一。
//
// 用法：
//   const projectDlg = useCrudDialog({
//     defaults: { name: '', description: '', ... },
//     rules: { name: [{ required: true, message: '...' }] },
//     create: (data) => createProject(data),
//     update: (id, data) => updateProject(id, data),
//     refresh: () => fetchProjects(),
//   })
//   // open / save / close
//   <el-dialog v-model="projectDlg.visible.value" ...>
//     <el-form ref="projectDlg.formRef" :model="projectDlg.form" :rules="projectDlg.rules">
//       ...
//     </el-form>
//   </el-dialog>
//   <el-button @click="projectDlg.open(row)">编辑</el-button>
//   <el-button @click="projectDlg.save()">保存</el-button>

import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

export function useCrudDialog({
  defaults = {},
  rules = {},
  create,
  update,
  refresh,
  successMessage = { create: '创建成功', update: '更新成功' },
}) {
  const visible = ref(false)
  const editing = ref(null)            // null = 新建；否则是当前编辑对象
  const form = reactive({ ...defaults })
  const formRef = ref(null)
  const submitting = ref(false)

  function _reset(row) {
    Object.keys(form).forEach((k) => { delete form[k] })
    Object.assign(form, defaults)
    if (row) {
      // 编辑模式：defaults + row（row 优先，所以可以覆盖初始 schema 不变的字段）
      Object.assign(form, row)
    }
  }

  function open(row, extraDefaults) {
    if (extraDefaults) Object.assign(defaults, extraDefaults)   // 首次 open 时附加默认
    _reset(row)
    editing.value = row || null
    visible.value = true
    // 等下一拍 dialog 挂载后再清 formRef 错误状态（el-form 会读 formRef）
    setTimeout(() => formRef.value?.clearValidate?.(), 0)
  }

  async function save() {
    if (!formRef.value) return false
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return false
    submitting.value = true
    try {
      if (editing.value?.id) {
        await update(editing.value.id, form)
        ElMessage.success(successMessage.update)
      } else {
        await create(form)
        ElMessage.success(successMessage.create)
      }
      visible.value = false
      if (refresh) await refresh()
      return true
    } catch {
      // interceptor 已 toast
      return false
    } finally {
      submitting.value = false
    }
  }

  function close() {
    visible.value = false
  }

  return {
    visible, editing, form, formRef, rules, submitting,
    open, save, close,
  }
}