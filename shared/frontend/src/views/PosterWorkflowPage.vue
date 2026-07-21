<template>
  <div class="workflow-page sketch-shell">
    <div class="workflow-head sketch-card">
      <div>
        <h1>AI 海报工作流</h1>
        <p>从 ABO 商品库选品（图文一体）→ 背景生成 → 海报合成。选品后会自动带出官方图与海报文案。</p>
      </div>
      <el-button text type="primary" @click="step = Math.min(2, step + 1)" v-if="step < 2">下一步</el-button>
    </div>

    <el-steps :active="step" finish-status="success" align-center class="workflow-steps">
      <el-step title="商品选品/抠图" description="库内商品 或 上传抠图" @click="step = 0" />
      <el-step title="背景生成" description="按品类生成场景并超分" @click="step = 1" />
      <el-step title="海报合成" description="自动文案 + 模板合成" @click="step = 2" />
    </el-steps>

    <div class="workflow-body">
      <div class="step-nav">
        <el-button :disabled="step === 0" @click="step -= 1">上一步</el-button>
        <el-tag v-if="appStore.mattedUrl" type="success" effect="plain">已有抠图</el-tag>
        <el-tag v-if="appStore.category" type="info" effect="plain">类别：{{ appStore.category }}</el-tag>
        <el-tag v-if="appStore.enhancedBgUrl" type="success" effect="plain">已有背景</el-tag>
        <el-button type="primary" :disabled="step === 2" @click="goNext">下一步</el-button>
      </div>

      <MattePage v-show="step === 0" />
      <BackgroundPage v-show="step === 1" />
      <PosterPage v-show="step === 2" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/store/useAppStore'
import MattePage from '@m2/views/matte/MattePage.vue'
import BackgroundPage from '@m3/views/background/BackgroundPage.vue'
import PosterPage from '@m4/views/poster/PosterPage.vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const step = ref(Number(route.query.step || 0))

watch(step, (v) => {
  router.replace({ path: '/poster-workflow', query: { step: String(v) } })
})

function goNext() {
  if (step.value === 0) {
    const m = appStore.mattedUrl || ''
    if (!m.includes('/static/matte/')) {
      ElMessage.warning('请先完成第1步抠图（不要直接用库内白底原图）')
      return
    }
  }
  if (step.value === 1 && !appStore.enhancedBgUrl) {
    ElMessage.warning('建议先生成背景，再进入海报合成')
  }
  if (step.value < 2) step.value += 1
}
</script>

<style scoped>
.workflow-page { display: grid; gap: 14px; }
.workflow-head {
  padding: 18px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.workflow-head h1 {
  margin: 0 0 6px;
  font-size: 28px;
  font-family: var(--font-display);
  font-weight: 600;
}
.workflow-head p {
  margin: 0;
  color: var(--ink-soft, #666);
  font-size: 14px;
}
.workflow-steps {
  padding: 8px 0 4px;
  cursor: pointer;
}
.workflow-body {
  background: transparent;
}
.step-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
</style>
