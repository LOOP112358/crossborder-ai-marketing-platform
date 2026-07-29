<template>
  <div class="wp-workflow sketch-shell">
    <div class="workflow-head sketch-card">
      <div>
        <h1>文案 · 海报工作流</h1>
        <p>
          已从选品中心带入商品。先写营销文案，再进入海报生成；文案与海报均可跳过，商品状态全程保留。
        </p>
      </div>
      <div class="head-actions">
        <el-button text type="primary" @click="$router.push('/catalog')">回选品中心</el-button>
        <el-button text type="success" @click="$router.push('/my-works')">我的作品</el-button>
      </div>
    </div>

    <el-steps :active="phase" finish-status="success" align-center class="workflow-steps">
      <el-step
        title="营销文案"
        :description="skipped.writing ? '已跳过' : '可跳过'"
        @click="jumpPhase(0)"
      />
      <el-step
        title="海报生成"
        :description="skipped.poster ? '已跳过' : '抠图 → 背景 → 底图 → 加字（可跳过）'"
        @click="jumpPhase(1)"
      />
    </el-steps>

    <div class="context-bar" v-if="productLabel">
      <el-tag type="success" effect="plain">当前商品：{{ productLabel }}</el-tag>
      <el-tag v-if="writingDone && !skipped.writing" type="success" effect="plain">已有文案</el-tag>
      <el-tag v-else-if="skipped.writing" type="info" effect="plain">已跳过文案</el-tag>
      <el-tag v-if="skipped.poster" type="info" effect="plain">已跳过海报</el-tag>
    </div>

    <!-- ===== 阶段 1：文案 ===== -->
    <div v-show="phase === 0" class="phase-body">
      <div class="step-nav">
        <el-button plain type="warning" @click="skipWriting">跳过文案，去做海报</el-button>
        <el-button
          v-if="writingDone"
          type="primary"
          @click="goToPoster"
        >
          下一步：海报生成
        </el-button>
      </div>
      <WritingPage workflow-mode @continue-workflow="onWritingContinue" />
    </div>

    <!-- ===== 阶段 2：海报（原抠图→背景→合成） ===== -->
    <div v-show="phase === 1" class="phase-body">
      <div class="step-nav">
        <el-button @click="phase = 0">返回文案</el-button>
        <el-button plain type="warning" @click="skipPoster">跳过海报并结束</el-button>
        <el-button :disabled="posterStep === 0" @click="posterStep -= 1">上一步</el-button>
        <el-button v-if="posterStep < 3" type="primary" @click="posterNext">
          {{ posterNextLabel }}
        </el-button>
        <el-button v-else type="success" @click="finishWorkflow">完成并查看作品</el-button>
      </div>

      <el-steps :active="posterStep" finish-status="success" align-center class="poster-substeps">
        <el-step title="商品抠图" @click="posterJump(0)" />
        <el-step title="背景生成" @click="posterJump(1)" />
        <el-step title="生成底图" @click="posterJump(2)" />
        <el-step title="加文案" @click="posterJump(3)" />
      </el-steps>

      <MattePage v-show="posterStep === 0" />
      <BackgroundPage v-show="posterStep === 1" />
      <PosterPage v-if="posterStep === 2" stage="base" />
      <PosterPage v-if="posterStep === 3" stage="text" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAppStore } from '@/store/useAppStore'
import WritingPage from '@m1/views/writing/WritingPage.vue'
import MattePage from '@m2/views/matte/MattePage.vue'
import BackgroundPage from '@m3/views/background/BackgroundPage.vue'
import PosterPage from '@m4/views/poster/PosterPage.vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const phase = ref(route.query.skipWriting === '1' ? 1 : 0)
const posterStep = ref(0)
const writingDone = ref(!!sessionStorage.getItem('workflow_writing_done'))
const skipped = reactive({
  writing: route.query.skipWriting === '1',
  poster: false,
})

const productLabel = computed(() => {
  const p = appStore.selectedProduct
  if (!p) return ''
  return [p.brand, p.name || p.item_name].filter(Boolean).join(' · ').slice(0, 64)
})

const posterNextLabel = computed(() => {
  if (posterStep.value === 0) return '下一步：背景生成'
  if (posterStep.value === 1) return '下一步：生成底图'
  return '下一步：加文案'
})

onMounted(() => {
  if (!appStore.selectedProductId && !appStore.selectedProduct) {
    ElMessage.warning('请先在智能选品中选择商品')
    router.replace('/catalog')
  }
})

watch(phase, (v) => {
  const q = { ...route.query, phase: v === 0 ? 'writing' : 'poster' }
  if (skipped.writing) q.skipWriting = '1'
  else delete q.skipWriting
  router.replace({ path: '/writing-poster', query: q })
})

function jumpPhase(i) {
  if (i === 1) {
    goToPoster()
    return
  }
  phase.value = 0
}

function pushWritingToPoster() {
  try {
    const raw = sessionStorage.getItem('workflow_writing_result')
    if (!raw) return
    const item = JSON.parse(raw)
    const lines = String(item.body || '')
      .split(/[\n。！？!?；;]/)
      .map((s) => s.trim())
      .filter(Boolean)
    const copy = {
      title: (item.title || '').slice(0, 40),
      subtitle: (lines[0] || '').slice(0, 48),
      selling_point_1: (lines[1] || '').slice(0, 36),
      selling_point_2: (lines[2] || '').slice(0, 36),
      cta_text: '立即选购',
      discount: (lines[0] || '').slice(0, 48),
      price: '立即选购',
    }
    sessionStorage.setItem('poster_copy_override', JSON.stringify(copy))
    appStore.setPosterConfig(copy, appStore.mattedProductId || appStore.selectedProductId)
  } catch { /* ignore */ }
}

function onWritingContinue() {
  writingDone.value = true
  skipped.writing = false
  sessionStorage.setItem('workflow_writing_done', '1')
  pushWritingToPoster()
  phase.value = 1
  posterStep.value = 0
  ElMessage.success('文案已带入，开始海报生成')
}

function goToPoster() {
  if (writingDone.value) pushWritingToPoster()
  phase.value = 1
  if (posterStep.value > 3) posterStep.value = 0
}

function skipWriting() {
  skipped.writing = true
  ElMessage.info('已跳过文案，进入海报生成')
  phase.value = 1
  posterStep.value = 0
}

async function skipPoster() {
  try {
    await ElMessageBox.confirm(
      '确定跳过海报生成？文案与选品进度会保留，可之后在「AI海报工作流」继续。',
      '跳过海报',
      { type: 'warning', confirmButtonText: '跳过并结束', cancelButtonText: '继续做海报' },
    )
  } catch {
    return
  }
  skipped.poster = true
  finishWorkflow()
}

function validatePosterLeave(from) {
  if (from === 0) {
    const m = appStore.mattedUrl || ''
    if (!m.includes('/static/matte/')) {
      ElMessage.warning('请先完成抠图（海报需要透明商品图）')
      return false
    }
  }
  if (from === 2) {
    if (!appStore.basePosterUrl) {
      ElMessage.warning('请先生成无字底图')
      return false
    }
  }
  return true
}

function posterNext() {
  if (!validatePosterLeave(posterStep.value)) return
  if (posterStep.value < 3) posterStep.value += 1
}

function posterJump(i) {
  if (i > posterStep.value + 1) {
    ElMessage.info('请按步骤推进')
    return
  }
  if (i > posterStep.value && !validatePosterLeave(posterStep.value)) return
  posterStep.value = i
}

function finishWorkflow() {
  const tab = skipped.poster && writingDone.value ? 'writing' : 'poster'
  ElMessage.success('工作流已结束')
  router.push({ path: '/my-works', query: { tab } })
}
</script>

<style scoped>
.wp-workflow { display: grid; gap: 14px; }
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
  max-width: 640px;
}
.head-actions { display: flex; gap: 4px; flex-wrap: wrap; }
.workflow-steps { padding: 8px 0 4px; cursor: pointer; }
.poster-substeps { padding: 4px 0 12px; cursor: pointer; }
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
