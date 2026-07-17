<template>
  <el-form :model="form" :rules="rules" ref="formRef" size="large" @submit.prevent="onSubmit">
    <el-form-item prop="email">
      <el-input v-model="form.email" placeholder="邮箱 (@glazero.com)" prefix-icon="Message" />
    </el-form-item>
    <el-form-item prop="oldPassword">
      <el-input v-model="form.oldPassword" type="password" placeholder="原密码" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item prop="password">
      <el-input v-model="form.password" type="password" placeholder="新密码 (至少6位)" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item prop="confirmPassword">
      <el-input v-model="form.confirmPassword" type="password" placeholder="确认新密码" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" class="login-card__btn" :loading="loading" @click="onSubmit">修改密码</el-button>
    </el-form-item>
    <div class="login-card__back">
      <el-button link @click="$emit('switch', 'login')">返回登录</el-button>
    </div>
  </el-form>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const emit = defineEmits(['success', 'switch', 'prefill'])

const formRef = ref(null)
const loading = ref(false)
const form = reactive({ email: '', oldPassword: '', password: '', confirmPassword: '' })
const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { validator: (r, v, cb) => (v || '').endsWith('@glazero.com') ? cb() : cb(new Error('仅支持 @glazero.com 邮箱')), trigger: 'blur' },
  ],
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: (r, v, cb) => v === form.password ? cb() : cb(new Error('两次输入的密码不一致')), trigger: 'blur' }],
}

async function onSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await request.post('/auth/change-password/', {
      email: form.email,
      old_password: form.oldPassword,
      new_password: form.password,
    }, { _silent: true })
    ElMessage.success('密码修改成功，请使用新密码登录')
    emit('prefill', { email: form.email, password: '' })
    emit('success')
  } catch (e) {
    ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '修改失败')
  } finally {
    loading.value = false
  }
}
</script>