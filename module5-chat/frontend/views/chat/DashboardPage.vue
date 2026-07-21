<template>
  <div class="dashboard sketch-shell">
    <el-row :gutter="16" class="top-cards">
      <el-col :span="6" v-for="card in topCards" :key="card.label">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>各功能调用占比</template>
          <div class="chart-placeholder">
            <div v-for="(v, k) in stats.feature_usage" :key="k" class="bar-row">
              <span class="bar-label">{{ k }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: (stats.feature_ratio?.[k] || 0) + '%' }"></div>
              </div>
              <span class="bar-num">{{ v }}</span>
            </div>
            <el-empty v-if="!Object.keys(stats.feature_usage || {}).length" description="暂无调用数据" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>近7天调用趋势（成员5原始能力）</template>
          <div class="trend-list">
            <div v-for="row in trend" :key="row.stat_date" class="trend-row">
              <span class="trend-date">{{ String(row.stat_date).slice(5) }}</span>
              <div class="trend-bars">
                <span title="writing">文 {{ row.writing_calls || 0 }}</span>
                <span title="matte">抠 {{ row.matte_calls || 0 }}</span>
                <span title="bg">背 {{ row.bg_calls || 0 }}</span>
                <span title="poster">海 {{ row.poster_calls || 0 }}</span>
                <span title="chat">客 {{ row.chat_calls || 0 }}</span>
              </div>
            </div>
            <el-empty v-if="!trend.length" description="暂无趋势数据" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>热门品类 TOP</template>
          <el-table :data="stats.hot_categories || []" size="small" max-height="250">
            <el-table-column type="index" label="#" width="40" />
            <el-table-column prop="name" label="品类" />
            <el-table-column prop="count" label="数量" width="80" align="right" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            运营建议
            <el-button size="small" style="float:right" @click="loadAdvice" :loading="adviceLoading">刷新</el-button>
          </template>
          <div class="advice-text" v-if="advice">{{ advice }}</div>
          <el-empty v-else description="点击刷新获取 AI 运营建议" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>异常预警</template>
          <div v-if="!(stats.error_alerts || []).length" class="ok-line">所有模块运行正常</div>
          <el-alert
            v-for="a in stats.error_alerts || []"
            :key="a.module"
            :title="a.module"
            :description="a.message"
            type="error"
            show-icon
            style="margin-bottom:8px"
          />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>客服满意度</template>
          <div class="feedback-row">
            <span>👍 {{ stats.chat_feedback_stats?.like || 0 }}</span>
            <span>👎 {{ stats.chat_feedback_stats?.dislike || 0 }}</span>
            <el-tag :type="satisfaction > 50 ? 'success' : 'warning'" size="large">满意度 {{ satisfaction }}%</el-tag>
          </div>
          <p class="live-hint">{{ liveHint }}</p>
        </el-card>
      </el-col>
    </el-row>

    <div class="export-row">
      <el-button @click="exportData('excel')"><el-icon><Download /></el-icon> 导出 Excel</el-button>
      <el-button @click="exportData('pdf')"><el-icon><Download /></el-icon> 导出 PDF</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import request from '@/api/request'

const stats = ref({
  total_users: 0,
  today_calls: 0,
  feature_usage: {},
  feature_ratio: {},
  hot_categories: [],
  error_alerts: [],
  chat_feedback_stats: { like: 0, dislike: 0 },
})
const trend = ref([])
const advice = ref('')
const adviceLoading = ref(false)
const liveHint = ref('实时通道未连接')
let ws = null

const satisfaction = computed(() => {
  const l = stats.value.chat_feedback_stats?.like || 0
  const d = stats.value.chat_feedback_stats?.dislike || 0
  if (l + d === 0) return 100
  return Math.round((l / (l + d)) * 100)
})

const topCards = computed(() => [
  { label: '总用户数', value: stats.value.total_users, color: '#2f6f6a' },
  { label: '今日调用量', value: stats.value.today_calls, color: '#3d7a52' },
  { label: '客服满意度', value: satisfaction.value + '%', color: '#c45c26' },
  { label: '异常预警', value: (stats.value.error_alerts || []).length, color: '#b42318' },
])

async function loadStats() {
  try {
    stats.value = await request.get('/dashboard/stats')
  } catch {}
}

async function loadTrend() {
  try {
    const data = await request.get('/dashboard/trend')
    trend.value = Array.isArray(data) ? data : data?.items || []
  } catch {}
}

async function loadAdvice() {
  adviceLoading.value = true
  try {
    const data = await request.get('/dashboard/advice')
    advice.value = data.advice
  } catch {} finally {
    adviceLoading.value = false
  }
}

function exportData(type) {
  const token = localStorage.getItem('token')
  window.open(`/api/dashboard/export/${type}?token=${token}`, '_blank')
}

function connectWs() {
  try {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    ws = new WebSocket(`${proto}://${location.host}/api/dashboard/ws`)
    ws.onopen = () => {
      liveHint.value = '实时刷新已连接（成员5 WebSocket）'
    }
    ws.onmessage = (ev) => {
      try {
        const payload = JSON.parse(ev.data)
        stats.value = { ...stats.value, ...payload }
        liveHint.value = `实时刷新 · ${new Date().toLocaleTimeString()}`
      } catch {}
    }
    ws.onclose = () => {
      liveHint.value = '实时通道已断开，使用轮询数据'
    }
  } catch {
    liveHint.value = '当前环境不支持 WebSocket'
  }
}

onMounted(() => {
  loadStats()
  loadTrend()
  loadAdvice()
  connectWs()
})

onBeforeUnmount(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
.dashboard { padding: 0; }
.stat-card { text-align: center; }
.stat-value { font-size: 32px; font-family: var(--font-display); }
.stat-label { font-size: 13px; color: var(--ink-soft); margin-top: 4px; }
.bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.bar-label { width: 80px; font-size: 13px; text-align: right; }
.bar-track {
  flex: 1;
  height: 16px;
  background: rgba(44, 58, 66, 0.08);
  border: 1.5px solid rgba(44, 58, 66, 0.2);
  border-radius: 999px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #2f6f6a, #7eb8a8);
  border-radius: 999px;
}
.bar-num { width: 30px; font-size: 12px; color: var(--ink-soft); }
.trend-list { max-height: 250px; overflow: auto; }
.trend-row {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px dashed rgba(44, 58, 66, 0.15);
}
.trend-date { width: 48px; color: var(--ink-soft); font-size: 12px; }
.trend-bars {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
}
.trend-bars span {
  border: 1px solid rgba(44, 58, 66, 0.25);
  border-radius: 999px;
  padding: 2px 8px;
  background: #fff;
}
.advice-text { white-space: pre-wrap; line-height: 1.8; font-size: 14px; }
.feedback-row { display: flex; align-items: center; gap: 16px; font-size: 18px; }
.ok-line { color: var(--good); text-align: center; padding: 20px; }
.live-hint { margin-top: 12px; font-size: 12px; color: var(--ink-soft); }
.export-row { text-align: right; margin-top: 16px; display: flex; justify-content: flex-end; gap: 8px; }
</style>
