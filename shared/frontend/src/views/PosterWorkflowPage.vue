<template>
  <div class="workflow-page sketch-shell">
    <div class="workflow-head sketch-card">
      <div>
        <h1>AI 海报工作流</h1>
        <p>商品抠图 → 背景生成 → 无字底图 → 加文案。底图可收藏，成稿可发布到广场。</p>
      </div>
      <div class="head-actions">
        <el-button text type="primary" @click="$router.push('/catalog')">去选品中心</el-button>
        <el-button text type="success" @click="$router.push('/my-works?tab=poster')">我的作品</el-button>
      </div>
    </div>

    <el-steps :active="step" finish-status="success" align-center class="workflow-steps">
      <el-step title="商品抠图" description="去背景 / 识别" @click="jumpTo(0)" />
      <el-step title="背景生成" description="场景图 / 超分" @click="jumpTo(1)" />
      <el-step title="生成底图" description="无字原始素材" @click="jumpTo(2)" />
      <el-step title="加文案" description="叠字成稿" @click="jumpTo(3)" />
    </el-steps>

    <div class="context-bar" v-if="productLabel || appStore.basePosterUrl">
      <el-tag v-if="productLabel" type="success" effect="plain">当前商品：{{ productLabel }}</el-tag>
      <el-tag v-if="appStore.mattedUrl?.includes('/static/matte/')" type="success" effect="plain">已抠图</el-tag>
      <el-tag
        v-if="appStore.preferredBgUrl || appStore.enhancedBgUrl || appStore.seedreamBgUrl"
        type="success"
        effect="plain"
      >已有背景</el-tag>
      <el-tag v-if="appStore.basePosterUrl" type="success" effect="plain">已有无字底图</el-tag>
    </div>

    <div class="workflow-body">
      <div class="step-nav">
        <el-button :disabled="step === 0" @click="step -= 1">上一步</el-button>
        <el-button v-if="step < 3" type="primary" @click="goNext">
          {{ nextLabel }}
        </el-button>
        <el-button v-else type="success" @click="$router.push('/my-works?tab=poster')">完成并查看作品</el-button>
      </div>

      <MattePage v-show="step === 0" />
      <BackgroundPage v-show="step === 1" />
      <PosterPage v-if="step === 2" stage="base" @base-ready="onBaseReady" />
      <PosterPage v-if="step === 3" stage="text" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/store/useAppStore'
import MattePage from '@m2/views/matte/MattePage.vue'
import BackgroundPage from '@m3/views/background/BackgroundPage.vue'
import PosterPage from '@m4/views/poster/PosterPage.vue'

const STEP_ALIAS = {
  matte: 0, background: 1, bg: 1,
  base: 2, poster: 2,
  text: 3, copy: 3,
  0: 0, 1: 1, 2: 2, 3: 3,
}

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

function parseStep(raw) {
  if (raw == null || raw === '') return 0
  if (STEP_ALIAS[raw] != null) return STEP_ALIAS[raw]
  const n = Number(raw)
  return Number.isFinite(n) ? Math.min(3, Math.max(0, n)) : 0
}

const step = ref(parseStep(route.query.step))

const productLabel = computed(() => {
  const p = appStore.selectedProduct
  if (!p) return ''
  return [p.brand, p.name || p.item_name].filter(Boolean).join(' · ').slice(0, 64)
})

const nextLabel = computed(() => {
  if (step.value === 0) return '下一步：背景生成'
  if (step.value === 1) return '下一步：生成底图'
  return '下一步：加文案'
})

watch(step, (v) => {
  const path = route.path.startsWith('/writing-poster') ? '/writing-poster' : '/poster-workflow'
  router.replace({ path, query: { ...route.query, step: String(v) } })
})

watch(
  () => route.query.step,
  (v) => {
    const next = parseStep(v)
    if (next !== step.value) step.value = next
  },
)

function jumpTo(i) {
  if (i > step.value + 1) {
    ElMessage.info('请按步骤推进')
    return
  }
  if (i > step.value && !validateBeforeLeave(step.value)) return
  step.value = i
}

function validateBeforeLeave(from) {
  if (from === 0) {
    const m = appStore.mattedUrl || ''
    if (!m.includes('/static/matte/')) {
      ElMessage.warning('请先完成抠图（海报需要透明商品图）')
      return false
    }
  }
  if (from === 2) {
    if (!appStore.basePosterUrl) {
      ElMessage.warning('请先生成无字底图，或从「我的作品」选择底图')
      return false
    }
  }
  return true
}

function goNext() {
  if (!validateBeforeLeave(step.value)) return
  if (step.value < 3) step.value += 1
}

function onBaseReady() {
  ElMessage.success('底图已就绪，可进入加文案')
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
  flex-wrap: wrap;
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
  max-width: 620px;
}
.head-actions { display: flex; gap: 4px; flex-wrap: wrap; }
.workflow-steps { padding: 8px 0 4px; cursor: pointer; }
.context-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.step-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
</style>
