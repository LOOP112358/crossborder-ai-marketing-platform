<template>
  <el-container class="main-layout sketch-shell">
    <el-aside width="232px" class="sidebar sketch-card">
      <div class="logo" @click="$router.push('/home')">
        <span class="logo-mark">✦</span>
        <div>
          <div class="logo-text">跨境AI营销系统</div>
          <div class="logo-sub">越境智绘 · Beyond Borders</div>
        </div>
      </div>
      <el-menu :default-active="activeMenu" router>
        <el-menu-item index="/home">
          <el-icon><HomeFilled /></el-icon>
          <span>{{ $t('nav.home') }}</span>
        </el-menu-item>
        <el-menu-item index="/writing">
          <el-icon><Edit /></el-icon>
          <span>{{ $t('nav.writing') }}</span>
        </el-menu-item>
        <el-menu-item index="/poster-workflow">
          <el-icon><Postcard /></el-icon>
          <span>AI海报工作流</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>{{ $t('nav.chat') }}</span>
        </el-menu-item>
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>运营看板</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header sketch-card">
        <div class="header-left">
          <span class="page-title sketch-title">{{ currentPageTitle }}</span>
          <span class="page-hint">越境智绘</span>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleLangChange">
            <span class="lang-switch">
              <el-icon><Switch /></el-icon>
              {{ $t('lang.switch') }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="zh-CN">{{ $t('lang.zhCN') }}</el-dropdown-item>
                <el-dropdown-item command="en">{{ $t('lang.en') }}</el-dropdown-item>
                <el-dropdown-item command="ja">{{ $t('lang.ja') }}</el-dropdown-item>
                <el-dropdown-item command="ko">{{ $t('lang.ko') }}</el-dropdown-item>
                <el-dropdown-item command="es">{{ $t('lang.es') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-dropdown trigger="click">
            <span class="user-info">
              <span class="avatar">{{ (authStore.user?.username || 'U').slice(0, 1).toUpperCase() }}</span>
              <span class="username">{{ authStore.user?.username || 'User' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>{{ $t('common.logout') }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/store/useAuthStore'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  if (['/matte', '/background', '/poster', '/poster-workflow'].includes(route.path)) {
    return '/poster-workflow'
  }
  return route.path
})

const currentPageTitle = computed(() => {
  const nameMap = {
    '/home': 'nav.home',
    '/writing': 'nav.writing',
    '/poster-workflow': 'AI海报工作流',
    '/matte': 'AI海报工作流',
    '/background': 'AI海报工作流',
    '/poster': 'AI海报工作流',
    '/chat': 'nav.chat',
    '/dashboard': '运营看板',
  }
  const key = nameMap[route.path]
  if (!key) return t('common.home')
  return key.startsWith('nav.') ? t(key) : key
})

function handleLangChange(lang) {
  locale.value = lang
  localStorage.setItem('lang', lang)
}

function handleLogout() {
  ElMessageBox.confirm(t('common.logoutConfirm'), t('common.tip'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning',
  }).then(() => {
    authStore.logout()
    router.push('/login')
  }).catch(() => {})
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  padding: 14px;
  gap: 14px;
  background: transparent;
}
.sidebar {
  height: calc(100vh - 28px);
  padding-top: 8px;
  overflow: auto;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px 18px;
  cursor: pointer;
  border-bottom: 2px dashed rgba(44, 58, 66, 0.2);
  margin-bottom: 8px;
}
.logo-mark {
  width: 42px;
  height: 42px;
  border: 2px solid var(--line);
  border-radius: 40% 60% 45% 55% / 55% 40% 60% 45%;
  display: grid;
  place-items: center;
  background: #fff7e8;
  color: var(--accent-2);
  font-size: 18px;
}
.logo-text {
  font-family: var(--font-display);
  font-size: 22px;
  line-height: 1.2;
  font-weight: 600;
}
.logo-sub {
  font-size: 11px;
  color: var(--ink-soft);
  margin-top: 4px;
}
.header {
  height: 64px !important;
  margin: 0 0 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
}
.page-title {
  font-size: 26px;
  margin-right: 10px;
  font-weight: 600;
}
.page-hint {
  font-size: 12px;
  color: var(--accent);
  border-bottom: 2px solid rgba(47, 111, 106, 0.35);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 18px;
}
.lang-switch,
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--ink-soft);
}
.avatar {
  width: 32px;
  height: 32px;
  border: 2px solid var(--line);
  border-radius: 40% 60% 55% 45%;
  display: grid;
  place-items: center;
  background: #fff;
  font-size: 13px;
  font-weight: 700;
}
.content {
  padding: 0 !important;
  min-height: calc(100vh - 120px);
}
@media (max-width: 900px) {
  .main-layout { display: block; padding: 10px; }
  .sidebar { width: 100% !important; height: auto; margin-bottom: 12px; }
}
</style>
