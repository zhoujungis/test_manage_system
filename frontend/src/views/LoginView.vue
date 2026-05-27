<template>
  <div class="login-page">
    <div class="login-page__bg">
      <div class="login-page__orb login-page__orb--1" />
      <div class="login-page__orb login-page__orb--2" />
    </div>

    <div class="login-page__content">
      <div class="login-page__intro">
        <div class="login-page__intro-logo">
          <el-icon :size="32"><Monitor /></el-icon>
        </div>
        <h1>测试管理系统</h1>
        <p>统一管理测试用例、项目计划与执行结果，提升团队协作效率。</p>
        <ul class="login-page__features">
          <li><el-icon><Document /></el-icon> 用例库与模块管理</li>
          <li><el-icon><FolderOpened /></el-icon> 项目与测试计划</li>
          <li><el-icon><VideoPlay /></el-icon> 执行跟踪与缺陷闭环</li>
        </ul>
      </div>

      <el-card class="login-card" shadow="never">
        <h2 class="login-card__title">{{ tabTitles[activeTab] }}</h2>
        <p class="login-card__desc">{{ tabDescs[activeTab] }}</p>
        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" size="large" @submit.prevent="handleLogin">
              <el-form-item prop="email">
                <el-input v-model="loginForm.email" placeholder="邮箱" prefix-icon="Message" @keyup.enter="handleLogin" />
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="loginForm.password" type="password" placeholder="密码" prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
              </el-form-item>
              <div class="login-card__links">
                <el-button link type="primary" @click="activeTab = 'forgot'">忘记密码？</el-button>
                <el-button link type="primary" @click="activeTab = 'change'">修改密码</el-button>
              </div>
              <el-form-item>
                <el-button type="primary" class="login-card__btn" :loading="loading" @click="handleLogin">登 录</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" size="large">
              <el-form-item prop="displayName">
                <el-input v-model="registerForm.displayName" placeholder="显示名称（可选）" prefix-icon="User" />
              </el-form-item>
              <el-form-item prop="email">
                <el-input v-model="registerForm.email" placeholder="邮箱 (@glazero.com)" prefix-icon="Message" />
              </el-form-item>
              <el-form-item prop="code">
                <div class="login-card__code-row">
                  <el-input v-model="registerForm.code" placeholder="验证码">
                    <template #prefix><el-icon><Key /></el-icon></template>
                  </el-input>
                  <el-button :disabled="regCodeCooldown > 0" :loading="sendingRegCode" @click="sendRegisterCode">
                    {{ regCodeCooldown > 0 ? `${regCodeCooldown}s` : '发送验证码' }}
                  </el-button>
                </div>
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="registerForm.password" type="password" placeholder="密码 (至少6位)" prefix-icon="Lock" show-password />
              </el-form-item>
              <el-form-item prop="confirmPassword">
                <el-input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" prefix-icon="Lock" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="success" class="login-card__btn" :loading="regLoading" @click="handleRegister">注 册</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="忘记密码" name="forgot">
            <el-form :model="forgotForm" :rules="forgotRules" ref="forgotFormRef" size="large">
              <el-form-item prop="email">
                <el-input v-model="forgotForm.email" placeholder="注册邮箱 (@glazero.com)" prefix-icon="Message" />
              </el-form-item>
              <el-form-item prop="code">
                <div class="login-card__code-row">
                  <el-input v-model="forgotForm.code" placeholder="验证码">
                    <template #prefix><el-icon><Key /></el-icon></template>
                  </el-input>
                  <el-button :disabled="resetCodeCooldown > 0" :loading="sendingResetCode" @click="sendResetCode">
                    {{ resetCodeCooldown > 0 ? `${resetCodeCooldown}s` : '发送验证码' }}
                  </el-button>
                </div>
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="forgotForm.password" type="password" placeholder="新密码 (至少6位)" prefix-icon="Lock" show-password />
              </el-form-item>
              <el-form-item prop="confirmPassword">
                <el-input v-model="forgotForm.confirmPassword" type="password" placeholder="确认新密码" prefix-icon="Lock" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="warning" class="login-card__btn" :loading="forgotLoading" @click="handleResetPassword">重置密码</el-button>
              </el-form-item>
              <div class="login-card__back">
                <el-button link @click="activeTab = 'login'">返回登录</el-button>
              </div>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="修改密码" name="change">
            <el-form :model="changeForm" :rules="changeRules" ref="changeFormRef" size="large">
              <el-form-item prop="email">
                <el-input v-model="changeForm.email" placeholder="邮箱 (@glazero.com)" prefix-icon="Message" />
              </el-form-item>
              <el-form-item prop="oldPassword">
                <el-input v-model="changeForm.oldPassword" type="password" placeholder="原密码" prefix-icon="Lock" show-password />
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="changeForm.password" type="password" placeholder="新密码 (至少6位)" prefix-icon="Lock" show-password />
              </el-form-item>
              <el-form-item prop="confirmPassword">
                <el-input v-model="changeForm.confirmPassword" type="password" placeholder="确认新密码" prefix-icon="Lock" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" class="login-card__btn" :loading="changeLoading" @click="handleChangePassword">修改密码</el-button>
              </el-form-item>
              <div class="login-card__back">
                <el-button link @click="activeTab = 'login'">返回登录</el-button>
              </div>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const auth = useAuthStore()
const activeTab = ref('login')
const loading = ref(false)
const regLoading = ref(false)
const forgotLoading = ref(false)
const changeLoading = ref(false)
const loginFormRef = ref(null)
const registerFormRef = ref(null)
const forgotFormRef = ref(null)
const changeFormRef = ref(null)

const tabTitles = {
  login: '欢迎回来',
  register: '创建账号',
  forgot: '忘记密码',
  change: '修改密码',
}
const tabDescs = {
  login: '登录以继续使用',
  register: '使用企业邮箱注册新账号',
  forgot: '通过邮箱验证码重置密码',
  change: '验证原密码后设置新密码',
}

const loginForm = reactive({ email: '', password: '' })
const loginRules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerForm = reactive({
  displayName: '',
  email: '',
  code: '',
  password: '',
  confirmPassword: '',
})
const forgotForm = reactive({
  email: '',
  code: '',
  password: '',
  confirmPassword: '',
})
const changeForm = reactive({
  email: '',
  oldPassword: '',
  password: '',
  confirmPassword: '',
})

const regCodeCooldown = ref(0)
const resetCodeCooldown = ref(0)
const sendingRegCode = ref(false)
const sendingResetCode = ref(false)

function validateGlazeroEmail(rule, value, callback) {
  if (!value?.endsWith('@glazero.com')) {
    callback(new Error('仅允许 @glazero.com 邮箱'))
  } else {
    callback()
  }
}

function makeConfirmValidator(getPassword) {
  return (rule, value, callback) => {
    if (value !== getPassword()) {
      callback(new Error('两次密码不一致'))
    } else {
      callback()
    }
  }
}

const registerRules = {
  displayName: [],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { validator: validateGlazeroEmail, trigger: 'blur' },
  ],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: makeConfirmValidator(() => registerForm.password), trigger: 'blur' },
  ],
}

const forgotRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { validator: validateGlazeroEmail, trigger: 'blur' },
  ],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: makeConfirmValidator(() => forgotForm.password), trigger: 'blur' },
  ],
}

const changeRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { validator: validateGlazeroEmail, trigger: 'blur' },
  ],
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: makeConfirmValidator(() => changeForm.password), trigger: 'blur' },
  ],
}

function startCooldown(target) {
  target.value = 60
  const timer = setInterval(() => {
    target.value--
    if (target.value <= 0) clearInterval(timer)
  }, 1000)
}

async function sendRegisterCode() {
  if (!registerForm.email?.endsWith('@glazero.com')) {
    ElMessage.warning('请先输入正确的 @glazero.com 邮箱')
    return
  }
  sendingRegCode.value = true
  try {
    await request.post('/auth/send-code/', { email: registerForm.email })
    ElMessage.success('验证码已发送，请查收邮件')
    startCooldown(regCodeCooldown)
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '发送失败')
  } finally {
    sendingRegCode.value = false
  }
}

async function sendResetCode() {
  if (!forgotForm.email?.endsWith('@glazero.com')) {
    ElMessage.warning('请先输入正确的 @glazero.com 邮箱')
    return
  }
  sendingResetCode.value = true
  try {
    await request.post('/auth/send-reset-code/', { email: forgotForm.email })
    ElMessage.success('若该邮箱已注册，验证码将发送至您的邮箱')
    startCooldown(resetCodeCooldown)
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '发送失败')
  } finally {
    sendingResetCode.value = false
  }
}

async function handleLogin() {
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await auth.login(loginForm.email, loginForm.password)
    ElMessage.success('登录成功')
    router.push('/home')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  const valid = await registerFormRef.value.validate().catch(() => false)
  if (!valid) return
  regLoading.value = true
  try {
    await request.post('/auth/register/', {
      username: registerForm.displayName,
      email: registerForm.email,
      code: registerForm.code,
      password: registerForm.password,
      role: 'tester',
    })
    ElMessage.success('注册成功，请登录')
    loginForm.email = registerForm.email
    activeTab.value = 'login'
  } catch (e) {
    const msg = e.response?.data?.email?.[0] || e.response?.data?.error || e.response?.data?.detail || '注册失败'
    ElMessage.error(msg)
  } finally {
    regLoading.value = false
  }
}

async function handleResetPassword() {
  const valid = await forgotFormRef.value.validate().catch(() => false)
  if (!valid) return
  forgotLoading.value = true
  try {
    await request.post('/auth/reset-password/', {
      email: forgotForm.email,
      code: forgotForm.code,
      password: forgotForm.password,
    })
    ElMessage.success('密码已重置，请使用新密码登录')
    loginForm.email = forgotForm.email
    loginForm.password = ''
    activeTab.value = 'login'
  } catch (e) {
    ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '重置失败')
  } finally {
    forgotLoading.value = false
  }
}

async function handleChangePassword() {
  const valid = await changeFormRef.value.validate().catch(() => false)
  if (!valid) return
  changeLoading.value = true
  try {
    await request.post('/auth/change-password/', {
      email: changeForm.email,
      old_password: changeForm.oldPassword,
      new_password: changeForm.password,
    })
    ElMessage.success('密码修改成功，请使用新密码登录')
    loginForm.email = changeForm.email
    loginForm.password = ''
    activeTab.value = 'login'
  } catch (e) {
    ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '修改失败')
  } finally {
    changeLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(145deg, #0f172a 0%, #1e3a5f 45%, #312e81 100%);
}

.login-page__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.login-page__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
}

.login-page__orb--1 {
  width: 400px;
  height: 400px;
  background: #4f6ef7;
  top: -100px;
  right: -80px;
}

.login-page__orb--2 {
  width: 300px;
  height: 300px;
  background: #10b981;
  bottom: -60px;
  left: -60px;
}

.login-page__content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 64px;
  max-width: 960px;
  width: 100%;
}

.login-page__intro {
  flex: 1;
  color: #fff;
  min-width: 280px;
}

.login-page__intro-logo {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--tm-primary), #818cf8);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}

.login-page__intro h1 {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin-bottom: 12px;
}

.login-page__intro p {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.6;
  margin-bottom: 28px;
}

.login-page__features {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.login-page__features li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
}

.login-card {
  width: 420px;
  flex-shrink: 0;
  padding: 8px 4px 4px;
  border: none !important;
  box-shadow: var(--tm-shadow-lg) !important;
  border-radius: var(--tm-radius-lg) !important;
}

.login-card__title {
  font-size: 22px;
  font-weight: 700;
  color: var(--tm-text);
  margin-bottom: 4px;
}

.login-card__desc {
  font-size: 14px;
  color: var(--tm-text-secondary);
  margin-bottom: 20px;
}

.login-card__btn {
  width: 100%;
  height: 42px;
  font-size: 15px;
}

.login-card__code-row {
  display: flex;
  gap: 10px;
  width: 100%;
}

.login-card__code-row .el-input {
  flex: 1;
}

.login-card__links {
  display: flex;
  justify-content: space-between;
  margin: -8px 0 8px;
}

.login-card__back {
  text-align: center;
  margin-top: -8px;
}

.login-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

.login-tabs :deep(.el-tabs__item) {
  font-weight: 500;
  padding: 0 10px;
}

@media (max-width: 768px) {
  .login-page__intro {
    display: none;
  }

  .login-page__content {
    justify-content: center;
  }

  .login-card {
    width: 100%;
    max-width: 420px;
  }
}
</style>
