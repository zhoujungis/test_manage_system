<template>
  <el-form :model="form" :rules="rules" ref="formRef" size="large" @submit.prevent="onSubmit">
    <el-form-item prop="displayName">
      <el-input v-model="form.displayName" placeholder="显示名称（可选）" prefix-icon="User" />
    </el-form-item>
    <el-form-item prop="email">
      <el-input v-model="form.email" placeholder="邮箱 (@glazero.com)" prefix-icon="Message" />
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
      <el-input v-model="form.password" type="password" placeholder="密码 (至少6位)" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item prop="confirmPassword">
      <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item>
      <el-button type="success" class="login-card__btn" :loading="loading" @click="onSubmit">注 册</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const emit = defineEmits(['success', 'prefill'])

const formRef = ref(null)
const loading = ref(false)
const sending = ref(false)
const cooldown = ref(0)

const form = reactive({ displayName: '', email: '', code: '', password: '', confirmPassword: '' })
const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { validator: (r, v, cb) => (v || '').endsWith('@glazero.com') ? cb() : cb(new Error('仅支持 @glazero.com 邮箱')), trigger: 'blur' },
  ],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: makeConfirmValidator(() => form.password), trigger: 'blur' }],
}

function makeConfirmValidator(getOther) {
  return (rule, value, cb) => {
    if (value !== getOther()) return cb(new Error('两次输入的密码不一致'))
    cb()
  }
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
    await request.post('/auth/send-code/', { email: form.email }, { _silent: true })
    ElMessage.success('验证码已发送，请查收邮件')
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
    await request.post('/auth/register/', {
      username: form.displayName, email: form.email,
      code: form.code, password: form.password, role: 'tester',
    }, { _silent: true })
    ElMessage.success('注册成功，请登录')
    emit('prefill', { email: form.email })
    emit('success')
  } catch (e) {
    const msg = e.response?.data?.email?.[0] || e.response?.data?.error || e.response?.data?.detail || '注册失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>