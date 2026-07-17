<template>
  <el-form :model="form" :rules="rules" ref="formRef" size="large" @submit.prevent="onSubmit">
    <el-form-item prop="email">
      <el-input v-model="form.email" placeholder="邮箱" prefix-icon="Message" @keyup.enter="onSubmit" />
    </el-form-item>
    <el-form-item prop="password">
      <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password @keyup.enter="onSubmit" />
    </el-form-item>
    <div class="login-card__links">
      <el-button link type="primary" @click="$emit('switch', 'forgot')">忘记密码？</el-button>
      <el-button link type="primary" @click="$emit('switch', 'change')">修改密码</el-button>
    </div>
    <el-form-item>
      <el-button type="primary" class="login-card__btn" :loading="loading" @click="onSubmit">登 录</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const emit = defineEmits(['success', 'switch'])
const router = useRouter()
const auth = useAuthStore()

const formRef = ref(null)
const loading = ref(false)
const form = reactive({ email: '', password: '' })
const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { validator: (r, v, cb) => (v || '').endsWith('@glazero.com') ? cb() : cb(new Error('仅支持 @glazero.com 邮箱')), trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await auth.login(form.email, form.password)
    ElMessage.success('登录成功')
    emit('success')
    router.push('/home')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>