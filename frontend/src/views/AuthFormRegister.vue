<template>
  <el-form :model="form" :rules="rules" ref="formRef" size="large" @submit.prevent="onSubmit">
    <el-form-item prop="displayName">
      <el-input v-model="form.displayName" :placeholder="t('auth.placeholderDisplayName')" prefix-icon="User" />
    </el-form-item>
    <el-form-item prop="email">
      <el-input v-model="form.email" :placeholder="t('auth.placeholderEmail')" prefix-icon="Message" />
    </el-form-item>
    <el-form-item prop="code">
      <div class="login-card__code-row">
        <el-input v-model="form.code" :placeholder="t('auth.placeholderCode')">
          <template #prefix><el-icon><Key /></el-icon></template>
        </el-input>
        <el-button :disabled="cooldown > 0" :loading="sending" @click="sendCode">
          {{ cooldown > 0 ? t('auth.cooldown', { n: cooldown }) : t('auth.sendCode') }}
        </el-button>
      </div>
    </el-form-item>
    <el-form-item prop="password">
      <el-input v-model="form.password" type="password" :placeholder="t('auth.placeholderNewPassword')" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item prop="confirmPassword">
      <el-input v-model="form.confirmPassword" type="password" :placeholder="t('auth.placeholderConfirm')" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item>
      <el-button type="success" class="login-card__btn" :loading="loading" @click="onSubmit">{{ t('auth.submitRegister') }}</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, computed, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import request from '@/utils/request'

const emit = defineEmits(['success', 'prefill'])
const { t } = useI18n()

const GLAZERO_SUFFIX = '@glazero.com'
const formRef = ref(null)
const loading = ref(false)
const sending = ref(false)
const cooldown = ref(0)

const form = reactive({ displayName: '', email: '', code: '', password: '', confirmPassword: '' })

function makeConfirmValidator(getOther) {
  return (rule, value, cb) => {
    if (value !== getOther()) return cb(new Error(t('auth.placeholderConfirm')))
    cb()
  }
}

const rules = computed(() => ({
  email: [
    { required: true, message: t('auth.placeholderEmail'), trigger: 'blur' },
    {
      validator: (r, v, cb) => (v || '').endsWith(GLAZERO_SUFFIX) ? cb() : cb(new Error(t('auth.placeholderEmail'))),
      trigger: 'blur',
    },
  ],
  code: [{ required: true, message: t('auth.placeholderCode'), trigger: 'blur' }],
  password: [{ required: true, min: 6, message: t('auth.placeholderNewPassword'), trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: makeConfirmValidator(() => form.password), trigger: 'blur' }],
})).value

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
  if (!form.email?.endsWith(GLAZERO_SUFFIX)) {
    ElMessage.warning(t('auth.placeholderEmail'))
    return
  }
  sending.value = true
  try {
    await request.post('/auth/send-code/', { email: form.email }, { _silent: true })
    ElMessage.success(t('msg.codeSent'))
    startCooldown()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || t('auth.sendCode'))
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
    ElMessage.success(t('msg.registerSuccess'))
    emit('prefill', { email: form.email })
    emit('success')
  } catch (e) {
    const msg = e.response?.data?.email?.[0] || e.response?.data?.error || e.response?.data?.detail || t('auth.submitRegister')
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>