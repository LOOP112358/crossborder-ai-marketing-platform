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
          <template #header>各功能调用占比（今日）</template>
          <div ref="doughnutRef" class="chart-box" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>热门品类 TOP</template>
          <el-table :data="stats.hot_categories || []" size="small" max-height="280">
            <el-table-column type="index" label="#" width="40" />
            <el-table-column prop="name" label="品类" />
            <el-table-column prop="count" label="数量" width="80" align="right" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="14">
        <el-card shadow="never">
          <template #header>近7天调用趋势</template>
          <div ref="trendRef" class="chart-box chart-tall" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never">
          <template #header>错误量 & 客服反馈</template>
          <div ref="errorRef" class="chart-box chart-short" />
          <div class="feedback-row">
            <span>👍 {{ stats.chat_feedback_stats?.like || 0 }}</span>
            <span>👎 {{ stats.chat_feedback_stats?.dislike || 0 }}</span>
            <el-tag :type="satisfaction > 50 ? 'success' : 'warning'" size="large">满意度 {{ satisfaction }}%</el-tag>
          </div>
          <p class="live-hint">{{ liveHint }}</p>
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
          <template #header>
            运营建议
            <el-button size="small" style="float:right" @click="loadAdvice" :loading="adviceLoading">刷新</el-button>
          </template>
          <div class="advice-text" v-if="advice">{{ advice }}</div>
          <el-empty v-else description="点击刷新获取 AI 运营建议" />
        </el-card>
      </el-col>
    </el-row>

    <div class="export-row">
      <el-button :loading="exporting" @click="exportData('excel')"><el-icon><Download /></el-icon> 导出 Excel</el-button>
      <el-button :loading="exporting" @click="exportData('pdf')"><el-icon><Download /></el-icon> 导出 PDF</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const FEATURE_KEYS = ['文案生成', '商品抠图', '背景生成', '海报合成', '智能客服']
const TREND_FIELDS = ['writing_calls', 'matte_calls', 'bg_calls', 'poster_calls', 'chat_calls']
const CAT = ['#2f6f6a', '#3d7a52', '#c45c26', '#eda100', '#2a78d6']

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
const exporting = ref(false)
const liveHint = ref('实时通道未连接')

const doughnutRef = ref(null)
const trendRef = ref(null)
const errorRef = ref(null)
let doughnutChart = null
let trendChart = null
let errorChart = null
let ws = null
let reconnectTimer = null
let disposed = false

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

function ensureCharts() {
  if (doughnutRef.value && !doughnutChart) doughnutChart = echarts.init(doughnutRef.value)
  if (trendRef.value && !trendChart) trendChart = echarts.init(trendRef.value)
  if (errorRef.value && !errorChart) errorChart = echarts.init(errorRef.value)
}

function renderCharts() {
  ensureCharts()
  if (doughnutChart) {
    doughnutChart.setOption({
      color: CAT,
      tooltip: { trigger: 'item', formatter: '{b}: {c} 次 ({d}%)' },
      legend: { orient: 'vertical', right: 8, top: 'center', textStyle: { fontSize: 12 } },
      series: [{
        type: 'pie',
        radius: ['48%', '74%'],
        center: ['38%', '50%'],
        itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, position: 'inside', formatter: '{d}%', fontSize: 11, color: '#fff' },
        data: FEATURE_KEYS.map((name) => ({
          name,
          value: stats.value.feature_usage?.[name] || 0,
        })),
      }],
    })
  }
  if (trendChart) {
    trendChart.setOption({
      color: CAT,
      tooltip: { trigger: 'axis' },
      legend: { data: FEATURE_KEYS, bottom: 0, textStyle: { fontSize: 11 } },
      grid: { left: 36, right: 16, top: 24, bottom: 48 },
      xAxis: {
        type: 'category',
        data: trend.value.map((t) => String(t.stat_date).slice(5)),
        axisTick: { show: false },
      },
      yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { type: 'dashed' } } },
      series: FEATURE_KEYS.map((name, i) => ({
        name,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        data: trend.value.map((t) => t[TREND_FIELDS[i]] || 0),
      })),
    })
  }
  if (errorChart) {
    errorChart.setOption({
      color: ['#d03b3b'],
      tooltip: { trigger: 'axis' },
      grid: { left: 36, right: 12, top: 16, bottom: 28 },
      xAxis: {
        type: 'category',
        data: trend.value.map((t) => String(t.stat_date).slice(5)),
        axisTick: { show: false },
      },
      yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { type: 'dashed' } } },
      series: [{
        type: 'bar',
        barWidth: 14,
        data: trend.value.map((t) => t.error_count || 0),
        itemStyle: { borderRadius: [3, 3, 0, 0] },
      }],
    })
  }
}

function onResize() {
  doughnutChart?.resize()
  trendChart?.resize()
  errorChart?.resize()
}

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
    const data = await request.get('/dashboard/advice', { timeout: 60000 })
    advice.value = data.advice
  } catch {} finally {
    adviceLoading.value = false
  }
}

async function exportData(type) {
  exporting.value = true
  try {
    const blob = await request.get(`/dashboard/export/${type}`, {
      responseType: 'blob',
      timeout: 60000,
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `dashboard_report.${type === 'excel' ? 'xlsx' : 'pdf'}`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

function connectWs() {
  if (disposed) return
  try {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    ws = new WebSocket(`${proto}://${location.host}/api/dashboard/ws`)
    ws.onopen = () => {
      liveHint.value = '实时刷新已连接'
    }
    ws.onmessage = (ev) => {
      try {
        const payload = JSON.parse(ev.data)
        stats.value = { ...stats.value, ...payload }
        liveHint.value = `实时刷新 · ${new Date().toLocaleTimeString()}`
      } catch {}
    }
    ws.onclose = () => {
      liveHint.value = '实时通道已断开，5 秒后重连…'
      if (!disposed) reconnectTimer = setTimeout(connectWs, 5000)
    }
    ws.onerror = () => {
      try { ws?.close() } catch {}
    }
  } catch {
    liveHint.value = '当前环境不支持 WebSocket'
  }
}

watch([stats, trend], () => nextTick(renderCharts), { deep: true })

onMounted(async () => {
  await Promise.all([loadStats(), loadTrend()])
  await nextTick()
  renderCharts()
  window.addEventListener('resize', onResize)
  loadAdvice()
  connectWs()
})

onBeforeUnmount(() => {
  disposed = true
  clearTimeout(reconnectTimer)
  window.removeEventListener('resize', onResize)
  try { ws?.close() } catch {}
  doughnutChart?.dispose()
  trendChart?.dispose()
  errorChart?.dispose()
})
</script>

<style scoped>
.dashboard { padding: 0; }
.stat-card { text-align: center; }
.stat-value { font-size: 32px; font-family: var(--font-display); }
.stat-label { font-size: 13px; color: var(--ink-soft); margin-top: 4px; }
.chart-box { width: 100%; height: 280px; }
.chart-tall { height: 320px; }
.chart-short { height: 180px; }
.advice-text { white-space: pre-wrap; line-height: 1.8; font-size: 14px; }
.feedback-row { display: flex; align-items: center; gap: 16px; font-size: 18px; margin-top: 12px; }
.ok-line { color: var(--good); text-align: center; padding: 20px; }
.live-hint { margin-top: 12px; font-size: 12px; color: var(--ink-soft); }
.export-row { text-align: right; margin-top: 16px; display: flex; justify-content: flex-end; gap: 8px; }
</style>
