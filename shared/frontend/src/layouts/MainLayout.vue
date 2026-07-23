<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo" @click="$router.push('/home')">
        <el-icon :size="28"><Shop /></el-icon>
        <span class="logo-text">{{ $t('common.appName') }}</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/home">
          <el-icon><HomeFilled /></el-icon>
          <span>{{ $t('nav.home') }}</span>
        </el-menu-item>
        <el-menu-item index="/writing">
          <el-icon><Edit /></el-icon>
          <span>{{ $t('nav.writing') }}</span>
        </el-menu-item>
        <el-menu-item index="/matte">
          <el-icon><Scissor /></el-icon>
          <span>{{ $t('nav.matte') }}</span>
        </el-menu-item>
        <el-menu-item index="/background">
          <el-icon><PictureFilled /></el-icon>
          <span>{{ $t('nav.background') }}</span>
        </el-menu-item>
        <el-menu-item index="/poster">
          <el-icon><Postcard /></el-icon>
          <span>{{ $t('nav.poster') }}</span>
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

    <!-- 右侧区域 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <span class="page-title">{{ currentPageTitle }}</span>
        </div>
        <div class="header-right">
          <!-- 语言切换 -->
          <el-dropdown trigger="click" @command="handleLangChange">
            <span class="lang-switch">
              <el-icon><Switch /></el-icon>
              {{ $t('lang.switch') }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="zh-CN">🇨🇳 {{ $t('lang.zhCN') }}</el-dropdown-item>
                <el-dropdown-item command="en">🇺🇸 {{ $t('lang.en') }}</el-dropdown-item>
                <el-dropdown-item command="ja">🇯🇵 {{ $t('lang.ja') }}</el-dropdown-item>
                <el-dropdown-item command="ko">🇰🇷 {{ $t('lang.ko') }}</el-dropdown-item>
                <el-dropdown-item command="es">🇪🇸 {{ $t('lang.es') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <!-- 用户 -->
          <el-dropdown trigger="click">
            <span class="user-info">
              <el-avatar :size="32" icon="UserFilled" />
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

const activeMenu = computed(() => route.path)

const currentPageTitle = computed(() => {
  const nameMap = {
    '/home': 'nav.home',
    '/writing': 'nav.writing',
    '/matte': 'nav.matte',
    '/background': 'nav.background',
    '/poster': 'nav.poster',
    '/chat': 'nav.chat',
  }
  const key = nameMap[route.path]
  return key ? t(key) : t('common.home')
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
}
.sidebar {
  background-color: #001529;
  overflow-y: auto;
  overflow-x: hidden;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo-text {
  font-size: 16px;
  font-weight: bold;
}
.sidebar .el-menu {
  border-right: none;
}
.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e8e8e8;
  padding: 0 24px;
  height: 60px;
}
.page-title {
  font-size: 18px;
  font-weight: 500;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.lang-switch {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #606266;
  font-size: 13px;
}
.lang-switch:hover {
  color: #409eff;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.content {
  background: #f0f2f5;
  min-height: calc(100vh - 60px);
}
</style>
