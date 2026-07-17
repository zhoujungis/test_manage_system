<template>
  <el-form :model="form" :rules="rules" ref="formRef" size="large" @submit.prevent="onSubmit">
    <el-form-item prop="email">
      <el-input v-model="form.email" placeholder="注册邮箱 (@glazero.com)" prefix-icon="Message" />
    </el-form-item>
    <el-form-item prop="code">
      <div class="login-card__code-row">
        <el-input v-model="form.code" placeholder="验证码">
          <template #prefix><el-icon><Key /></el-icon></template>
        </el-input>
        <el-button :disabled="cooldown > 0" :loading="sending" @click="sendCode">
          {{ cooldown > 0 ? `${cooldown}s` : '发送验证码' }}
        </el-button>
      </div>
    </el-form-item>
    <el-form-item prop="password">
      <el-input v-model="form.password" type="password" placeholder="新密码 (至少6位)" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item prop="confirmPassword">
      <el-input v-model="form.confirmPassword" type="password" placeholder="确认新密码" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item>
      <el-button type="warning" class="login-card__btn" :loading="loading" @click="onSubmit">重置密码</el-button>
    </el-form-item>
    <div class="login-card__back">
      <el-button link @click="$emit('switch', 'login')">返回登录</el-button>
    </div>
  </el-form>
</template>

<script setup>
import { ref, reactive, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const emit = defineEmits(['success', 'switch', 'prefill'])

const formRef = ref(null)
const loading = ref(false)
const sending = ref(false)
const cooldown = ref(0)
const form = reactive({ email: '', code: '', password: '', confirmPassword: '' })
const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { validator: (r, v, cb) => (v || '').endsWith('@glazero.com') ? cb() : cb(new Error('仅支持 @glazero.com 邮箱')), trigger: 'blur' },
  ],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: (r, v, cb) => v === form.password ? cb() : cb(new Error('两次输入的密码不一致')), trigger: 'blur' }],
}

const cooldownTimers = new Set()
function startCooldown() {
  cooldown.value = 60
  const timer = setInterval(() => {
    cooldown.value--
    if (cooldown.value <= 0) { clearInterval(timer); cooldownTimers.delete(timer) }
  }, 1000)
  cooldownTimers.add(timer)
}
onBeforeUnmount(() => { for (const t of cooldownTimers) clearInterval(t); cooldownTimers.clear() })

async function sendCode() {
  if (!form.email?.endsWith('@glazero.com')) {
    ElMessage.warning('请先输入正确的 @glazero.com 邮箱')
    return
  }
  sending.value = true
  try {
    await request.post('/auth/send-reset-code/', { email: form.email }, { _silent: true })
    ElMessage.success('若该邮箱已注册，验证码将发送至您的邮箱')
    startCooldown()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '发送失败')
  } finally {
    sending.value = false
  }
}

async function onSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await request.post('/auth/reset-password/', {
      email: form.email, code: form.code, password: form.password,
    }, { _silent: true })
    ElMessage.success('密码已重置，请使用新密码登录')
    emit('prefill', { email: form.email, password: '' })
    emit('success')
  } catch (e) {
    ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '重置失败')
  } finally {
    loading.value = false
  }
}
</script>