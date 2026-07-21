<template>
  <div class="auth-container sketch-shell">
    <div class="auth-card sketch-card">
      <div class="stamp">合</div>
      <h2 class="auth-title sketch-title">{{ $t('common.appName') }}</h2>
      <p class="auth-subtitle">{{ $t('login.title') }} · 越境智绘</p>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item :label="$t('login.username')" prop="username">
          <el-input v-model="form.username" :placeholder="$t('login.usernamePlaceholder')" size="large" />
        </el-form-item>
        <el-form-item :label="$t('login.password')" prop="password">
          <el-input v-model="form.password" type="password" :placeholder="$t('login.passwordPlaceholder')" size="large"
            show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button class="sketch-btn sketch-btn-primary" size="large" :loading="loading" style="width:100%" @click="handleLogin">
            {{ $t('login.loginBtn') }}
          </el-button>
        </el-form-item>
      </el-form>
      <p class="auth-link">
        {{ $t('login.noAccount') }}<router-link to="/register">{{ $t('login.goRegister') }}</router-link>
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
})

const rules = {
  username: [{ required: true, message: () => t('login.usernamePlaceholder'), trigger: 'blur' }],
  password: [{ required: true, message: () => t('login.passwordPlaceholder'), trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success(t('login.loginSuccess'))
    router.push('/home')
  } catch {
    // 错误在拦截器中已处理
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
  position: relative;
}
.stamp {
  position: absolute;
  top: 18px;
  right: 18px;
  width: 48px;
  height: 48px;
  border: 2px solid var(--accent-2);
  border-radius: 50%;
  color: var(--accent-2);
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-size: 24px;
  transform: rotate(12deg);
  opacity: 0.85;
}
.auth-title {
  text-align: center;
  margin: 0 0 4px;
  font-size: 34px;
}
.auth-subtitle {
  text-align: center;
  margin: 0 0 24px;
  color: var(--ink-soft);
}
.auth-link {
  text-align: center;
  color: var(--ink-soft);
}
.auth-link a {
  color: var(--accent);
  margin-left: 4px;
  border-bottom: 1.5px solid rgba(47, 111, 106, 0.35);
}
</style>
