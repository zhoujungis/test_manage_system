<template>
  <el-form :model="form" :rules="rules" ref="formRef" size="large" @submit.prevent="onSubmit">
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
      <el-button type="warning" class="login-card__btn" :loading="loading" @click="onSubmit">{{ t('auth.submitReset') }}</el-button>
    </el-form-item>
    <div class="login-card__back">
      <el-button link @click="$emit('switch', 'login')">{{ t('auth.backToLogin') }}</el-button>
    </div>
  </el-form>
</template>

<script setup>
import { ref, reactive, computed, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import request from '@/utils/request'

const emit = defineEmits(['success', 'switch', 'prefill'])
const { t } = useI18n()
const GLAZERO_SUFFIX = '@glazero.com'

const formRef = ref(null)
const loading = ref(false)
const sending = ref(false)
const cooldown = ref(0)
const form = reactive({ email: '', code: '', password: '', confirmPassword: '' })

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
  confirmPassword: [{
    required: true,
    validator: (r, v, cb) => v === form.password ? cb() : cb(new Error(t('auth.placeholderConfirm'))),
    trigger: 'blur',
  }],
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
    await request.post('/auth/send-reset-code/', { email: form.email }, { _silent: true })
    ElMessage.success(t('msg.codeResetSent'))
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
    await request.post('/auth/reset-password/', {
      email: form.email, code: form.code, password: form.password,
    }, { _silent: true })
    ElMessage.success(t('msg.resetSuccess'))
    emit('prefill', { email: form.email, password: '' })
    emit('success')
  } catch (e) {
    ElMessage.error(e.response?.data?.error || e.response?.data?.detail || t('auth.submitReset'))
  } finally {
    loading.value = false
  }
}
</script>