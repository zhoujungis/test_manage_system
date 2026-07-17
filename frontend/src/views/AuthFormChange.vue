<template>
  <el-form :model="form" :rules="rules" ref="formRef" size="large" @submit.prevent="onSubmit">
    <el-form-item prop="email">
      <el-input v-model="form.email" :placeholder="t('auth.placeholderEmail')" prefix-icon="Message" />
    </el-form-item>
    <el-form-item prop="oldPassword">
      <el-input v-model="form.oldPassword" type="password" :placeholder="t('auth.placeholderOldPassword')" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item prop="password">
      <el-input v-model="form.password" type="password" :placeholder="t('auth.placeholderNewPassword')" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item prop="confirmPassword">
      <el-input v-model="form.confirmPassword" type="password" :placeholder="t('auth.placeholderConfirm')" prefix-icon="Lock" show-password />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" class="login-card__btn" :loading="loading" @click="onSubmit">{{ t('auth.submitChange') }}</el-button>
    </el-form-item>
    <div class="login-card__back">
      <el-button link @click="$emit('switch', 'login')">{{ t('auth.backToLogin') }}</el-button>
    </div>
  </el-form>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import request from '@/utils/request'

const emit = defineEmits(['success', 'switch', 'prefill'])
const { t } = useI18n()
const GLAZERO_SUFFIX = '@glazero.com'

const formRef = ref(null)
const loading = ref(false)
const form = reactive({ email: '', oldPassword: '', password: '', confirmPassword: '' })

const rules = computed(() => ({
  email: [
    { required: true, message: t('auth.placeholderEmail'), trigger: 'blur' },
    {
      validator: (r, v, cb) => (v || '').endsWith(GLAZERO_SUFFIX) ? cb() : cb(new Error(t('auth.placeholderEmail'))),
      trigger: 'blur',
    },
  ],
  oldPassword: [{ required: true, message: t('auth.placeholderOldPassword'), trigger: 'blur' }],
  password: [{ required: true, min: 6, message: t('auth.placeholderNewPassword'), trigger: 'blur' }],
  confirmPassword: [{
    required: true,
    validator: (r, v, cb) => v === form.password ? cb() : cb(new Error(t('auth.placeholderConfirm'))),
    trigger: 'blur',
  }],
})).value

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
    ElMessage.success(t('msg.changeSuccess'))
    emit('prefill', { email: form.email, password: '' })
    emit('success')
  } catch (e) {
    ElMessage.error(e.response?.data?.error || e.response?.data?.detail || t('auth.submitChange'))
  } finally {
    loading.value = false
  }
}
</script>