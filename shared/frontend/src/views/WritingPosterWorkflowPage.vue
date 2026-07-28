<template>
  <div class="wp-workflow sketch-shell">
    <div class="wp-head sketch-card">
      <div>
        <h1>文案·海报工作流</h1>
        <p>选品带入后先写文案（可跳过），再进入抠图 → 背景 → 海报合成。</p>
      </div>
      <div class="head-actions">
        <el-button text type="primary" @click="$router.push('/catalog')">回选品中心</el-button>
        <el-button
          v-if="phase === 0"
          type="success"
          @click="skipWriting"
        >
          跳过文案，去做海报
        </el-button>
        <el-button v-else text type="info" @click="phase = 0">返回文案</el-button>
      </div>
    </div>

    <el-steps :active="phase" finish-status="success" align-center class="wp-steps">
      <el-step title="文案生成" description="可跳过" @click="phase = 0" />
      <el-step title="海报制作" description="抠图 / 背景 / 合成" @click="enterPoster" />
    </el-steps>

    <div v-show="phase === 0" class="wp-phase">
      <WritingPage :workflow-mode="true" @continue-workflow="enterPoster" />
    </div>
    <div v-if="phase === 1" class="wp-phase">
      <PosterWorkflowPage />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import WritingPage from '@m1/views/writing/WritingPage.vue'
import PosterWorkflowPage from '@/views/PosterWorkflowPage.vue'

const route = useRoute()
const router = useRouter()
const phase = ref(0)

function syncPhaseFromQuery() {
  const skip = String(route.query.skipWriting || '') === '1'
  phase.value = skip ? 1 : 0
}

function enterPoster() {
  phase.value = 1
  router.replace({
    path: '/writing-poster',
    query: { ...route.query, skipWriting: '1' },
  })
}

function skipWriting() {
  ElMessage.info('已跳过文案，进入海报制作')
  enterPoster()
}

onMounted(syncPhaseFromQuery)

watch(
  () => route.query.skipWriting,
  () => syncPhaseFromQuery(),
)
</script>

<style scoped>
.wp-workflow {
  display: grid;
  gap: 14px;
}
.wp-head {
  padding: 18px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.wp-head h1 {
  margin: 0 0 6px;
  font-size: 28px;
  font-family: var(--font-display);
  font-weight: 600;
}
.wp-head p {
  margin: 0;
  color: var(--ink-soft, #666);
  font-size: 14px;
  max-width: 560px;
}
.head-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.wp-steps {
  padding: 4px 0 8px;
  cursor: pointer;
}
.wp-phase {
  min-width: 0;
}
</style>
