<template>
  <div class="home-page">
    <div class="welcome-card">
      <h1>{{ $t('home.welcome') }}</h1>
      <p>{{ $t('home.welcomeDesc') }}</p>
    </div>

    <el-row :gutter="20" class="module-cards">
      <el-col :xs="24" :sm="12" :lg="8" v-for="module in modules" :key="module.path">
        <el-card class="module-card" :body-style="{ padding: '0' }" shadow="hover"
          @click="$router.push(module.path)">
          <div class="card-icon" :style="{ background: module.color }">
            <el-icon :size="40"><component :is="module.icon" /></el-icon>
          </div>
          <div class="card-info">
            <h3>{{ module.name }}</h3>
            <p>{{ module.desc }}</p>
            <el-tag :type="module.tagType" size="small">{{ module.status }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const modules = computed(() => [
  {
    name: t('home.writingName'),
    desc: t('home.writingDesc'),
    path: '/writing',
    icon: 'Edit',
    color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    tagType: 'success',
    status: t('home.done'),
  },
  {
    name: t('home.matteName'),
    desc: t('home.matteDesc'),
    path: '/matte',
    icon: 'Scissor',
    color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    tagType: 'warning',
    status: t('home.developing'),
  },
  {
    name: t('home.bgName'),
    desc: t('home.bgDesc'),
    path: '/background',
    icon: 'PictureFilled',
    color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    tagType: 'warning',
    status: t('home.developing'),
  },
  {
    name: t('home.posterName'),
    desc: t('home.posterDesc'),
    path: '/poster',
    icon: 'Postcard',
    color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    tagType: 'warning',
    status: t('home.developing'),
  },
  {
    name: t('home.chatName'),
    desc: t('home.chatDesc'),
    path: '/chat',
    icon: 'ChatDotRound',
    color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    tagType: 'warning',
    status: t('home.developing'),
  },
])
</script>

<style scoped>
.home-page { padding: 0; }
.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 40px;
  border-radius: 8px;
  margin-bottom: 24px;
}
.welcome-card h1 { margin: 0 0 8px; font-size: 24px; }
.welcome-card p { margin: 0; opacity: 0.85; }
.module-cards { margin-top: 8px; }
.module-card {
  cursor: pointer;
  margin-bottom: 20px;
  border-radius: 8px;
  transition: transform 0.2s;
}
.module-card:hover { transform: translateY(-4px); }
.card-icon {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.card-info { padding: 16px; }
.card-info h3 { margin: 0 0 8px; font-size: 16px; }
.card-info p { margin: 0 0 12px; font-size: 13px; color: #909399; line-height: 1.6; }
</style>
