<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2 class="auth-title">{{ $t('common.appName') }}</h2>
      <p class="auth-subtitle">{{ $t('register.title') }}</p>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item :label="$t('register.username')" prop="username">
          <el-input v-model="form.username" :placeholder="$t('register.usernamePlaceholder')" size="large" />
        </el-form-item>
        <el-form-item :label="$t('register.password')" prop="password">
          <el-input v-model="form.password" type="password" :placeholder="$t('register.passwordPlaceholder')" size="large"
            show-password />
        </el-form-item>
        <el-form-item :label="$t('register.confirmPassword')" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" :placeholder="$t('register.confirmPlaceholder')" size="large"
            show-password @keyup.enter="handleRegister" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" block @click="handleRegister">
            {{ $t('register.registerBtn') }}
          </el-button>
        </el-form-item>
      </el-form>
      <p class="auth-link">
        {{ $t('register.hasAccount') }}<router-link to="/login">{{ $t('register.goLogin') }}</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/store/useAuthStore'
import { ElMessage } from 'element-plus'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error(t('register.passwordMismatch')))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: () => t('register.usernamePlaceholder'), trigger: 'blur' },
    { min: 2, max: 50, message: () => t('register.usernameRule'), trigger: 'blur' },
  ],
  password: [
    { required: true, message: () => t('register.passwordPlaceholder'), trigger: 'blur' },
    { min: 6, message: () => t('register.passwordRule'), trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: () => t('register.confirmPlaceholder'), trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await authStore.register(form.username, form.password)
    ElMessage.success(t('register.registerSuccess'))
    router.push('/home')
  } catch {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.auth-card {
  width: 420px;
  padding: 36px 32px;
  background: var(--card);
  border: 2px solid var(--line);
  border-radius: 18px 22px 16px 20px / 20px 16px 22px 18px;
  box-shadow: var(--shadow);
}
.auth-title {
  text-align: center;
  margin-bottom: 4px;
  font-size: 34px;
  font-family: var(--font-display);
}
.auth-subtitle {
  text-align: center;
  margin-bottom: 24px;
  color: var(--ink-soft);
}
.auth-link {
  text-align: center;
  color: var(--ink-soft);
}
.auth-link a {
  color: var(--accent);
}
</style>
