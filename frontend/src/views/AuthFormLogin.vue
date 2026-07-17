<template>
  <el-form :model="form" :rules="rules" ref="formRef" size="large" @submit.prevent="onSubmit">
    <el-form-item prop="email">
      <el-input v-model="form.email" :placeholder="t('auth.placeholderEmail')" prefix-icon="Message" @keyup.enter="onSubmit" />
    </el-form-item>
    <el-form-item prop="password">
      <el-input v-model="form.password" type="password" :placeholder="t('auth.placeholderPassword')" prefix-icon="Lock" show-password @keyup.enter="onSubmit" />
    </el-form-item>
    <div class="login-card__links">
      <el-button link type="primary" @click="$emit('switch', 'forgot')">{{ t('auth.forgotLink') }}</el-button>
      <el-button link type="primary" @click="$emit('switch', 'change')">{{ t('auth.changeLink') }}</el-button>
    </div>
    <el-form-item>
      <el-button type="primary" class="login-card__btn" :loading="loading" @click="onSubmit">{{ t('auth.submitLogin') }}</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const emit = defineEmits(['success', 'switch'])
const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()

const formRef = ref(null)
const loading = ref(false)
const form = reactive({ email: '', password: '' })

const GLAZERO_SUFFIX = '@glazero.com'
const rules = computed(() => ({
  email: [
    { required: true, message: t('auth.placeholderEmail'), trigger: 'blur' },
    {
      validator: (r, v, cb) =>
        (v || '').endsWith(GLAZERO_SUFFIX) ? cb() : cb(new Error(t('auth.placeholderEmail'))),
      trigger: 'blur',
    },
  ],
  password: [{ required: true, message: t('auth.placeholderPassword'), trigger: 'blur' }],
})).value

async function onSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await auth.login(form.email, form.password)
    ElMessage.success(t('msg.loginSuccess'))
    emit('success')
    router.push('/home')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || t('auth.placeholderPassword'))
  } finally {
    loading.value = false
  }
}
</script>