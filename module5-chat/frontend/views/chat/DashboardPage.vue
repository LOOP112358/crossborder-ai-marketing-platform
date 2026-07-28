<template>
  <div class="dashboard">
    <header class="dash-hero sketch-card">
      <div>
        <p class="eyebrow">运营数据中枢 · Module 5</p>
        <h2 class="sketch-title">跨境营销运营看板</h2>
        <p class="hero-desc">汇总文案、抠图、背景、海报与智能客服的实时经营指标</p>
      </div>
      <div class="hero-actions">
        <div class="live-pill" :class="{ on: liveOk }">
          <span class="dot" />
          {{ liveHint }}
        </div>
        <el-button class="sketch-btn" :loading="refreshing" @click="refreshAll">刷新数据</el-button>
        <el-button class="sketch-btn" @click="exportData('excel')">导出 Excel</el-button>
        <el-button class="sketch-btn sketch-btn-primary" @click="exportData('pdf')">导出 PDF</el-button>
      </div>
    </header>

    <el-row :gutter="14" class="kpi-row">
      <el-col :xs="12" :sm="8" :md="4" v-for="card in topCards" :key="card.label">
        <div class="kpi-card sketch-card" :style="{ '--accent': card.color }">
          <div class="kpi-label">{{ card.label }}</div>
          <div class="kpi-value">{{ card.value }}</div>
          <div class="kpi-sub" v-if="card.sub">{{ card.sub }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="14" class="block-row">
      <el-col :xs="24" :lg="14">
        <div class="panel sketch-card">
          <div class="panel-head">
            <h3>近 7 天调用趋势</h3>
            <span class="muted">堆叠柱图 · 五模块合计</span>
          </div>
          <div class="stack-chart" v-if="trend.length">
            <div class="stack-col" v-for="row in trendChart" :key="row.stat_date">
              <div class="stack-bars" :title="row.tooltip">
                <div
                  v-for="seg in row.segments"
                  :key="seg.key"
                  class="stack-seg"
                  :style="{ height: seg.h + '%', background: seg.color }"
                />
              </div>
              <div class="stack-total">{{ row.total }}</div>
              <div class="stack-date">{{ row.label }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无趋势数据" />
          <div class="legend">
            <span v-for="l in featureLegend" :key="l.key"><i :style="{ background: l.color }" />{{ l.name }}</span>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="10">
        <div class="panel sketch-card">
          <div class="panel-head">
            <h3>今日功能占比</h3>
            <span class="muted">共 {{ stats.today_calls || 0 }} 次</span>
          </div>
          <div class="donut-wrap" v-if="donut.total">
            <svg viewBox="0 0 120 120" class="donut">
              <circle cx="60" cy="60" r="42" class="donut-track" />
              <circle
                v-for="(seg, idx) in donut.segments"
                :key="idx"
                cx="60" cy="60" r="42"
                class="donut-seg"
                :stroke="seg.color"
                :stroke-dasharray="seg.dash"
                :stroke-dashoffset="seg.offset"
              />
              <text x="60" y="56" text-anchor="middle" class="donut-num">{{ stats.today_calls }}</text>
              <text x="60" y="72" text-anchor="middle" class="donut-label">今日</text>
            </svg>
            <div class="donut-list">
              <div v-for="row in featureRows" :key="row.name" class="donut-item">
                <span class="swatch" :style="{ background: row.color }" />
                <span class="name">{{ row.name }}</span>
                <span class="pct">{{ row.ratio }}%</span>
                <span class="cnt">{{ row.count }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="今日暂无调用" />
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="14" class="block-row">
      <el-col :xs="24" :md="8">
        <div class="panel sketch-card">
          <div class="panel-head">
            <h3>海报工作流漏斗</h3>
            <span class="muted">近 7 日累计转化</span>
          </div>
          <div class="funnel" v-if="(stats.funnel || []).length">
            <div v-for="(step, i) in stats.funnel" :key="step.key" class="funnel-step">
              <div class="funnel-meta">
                <strong>{{ step.step }}</strong>
                <span>{{ step.count }} 次 · {{ step.conversion }}%</span>
              </div>
              <div class="funnel-bar">
                <div class="funnel-fill" :style="{ width: Math.max(step.ratio, 8) + '%' }" />
              </div>
              <div v-if="i < stats.funnel.length - 1" class="funnel-arrow">↓</div>
            </div>
          </div>
          <el-empty v-else description="暂无漏斗数据" />
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="panel sketch-card">
          <div class="panel-head">
            <h3>热门品类 TOP</h3>
            <span class="muted">来自抠图识别</span>
          </div>
          <div class="rank-list" v-if="(stats.hot_categories || []).length">
            <div v-for="(c, i) in stats.hot_categories" :key="c.name" class="rank-row">
              <span class="rank-idx" :class="{ top: i < 3 }">{{ i + 1 }}</span>
              <div class="rank-body">
                <div class="rank-name">{{ c.name }}</div>
                <div class="rank-track"><div class="rank-fill" :style="{ width: (c.ratio || 0) + '%' }" /></div>
              </div>
              <span class="rank-cnt">{{ c.count }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无品类数据" />
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="panel sketch-card">
          <div class="panel-head">
            <h3>文案投放平台</h3>
            <span class="muted">历史累计分布</span>
          </div>
          <div class="platform-list" v-if="(stats.platforms || []).length">
            <div v-for="p in stats.platforms" :key="p.name" class="platform-row">
              <span>{{ p.name }}</span>
              <div class="platform-track">
                <div class="platform-fill" :style="{ width: platformWidth(p.count) + '%' }" />
              </div>
              <b>{{ p.count }}</b>
            </div>
          </div>
          <el-empty v-else description="暂无平台数据" />
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="14" class="block-row">
      <el-col :xs="24" :lg="10">
        <div class="panel sketch-card">
          <div class="panel-head">
            <h3>模块健康度</h3>
            <span class="muted">今日错误率监控</span>
          </div>
          <div class="health-grid">
            <div
              v-for="m in stats.module_health || []"
              :key="m.key"
              class="health-item"
              :class="m.status"
            >
              <div class="health-name">{{ m.name }}</div>
              <div class="health-rate">{{ m.error_rate }}%</div>
              <div class="health-sub">调用 {{ m.calls }} · 错误 {{ m.errors }}</div>
            </div>
          </div>
          <div v-if="(stats.error_alerts || []).length" class="alerts">
            <el-alert
              v-for="a in stats.error_alerts"
              :key="a.module"
              :title="a.module"
              :description="a.message"
              type="error"
              show-icon
              :closable="false"
              style="margin-top: 8px"
            />
          </div>
          <p v-else class="ok-line">全部模块运行平稳</p>
        </div>
      </el-col>
      <el-col :xs="24" :md="12" :lg="7">
        <div class="panel sketch-card">
          <div class="panel-head">
            <h3>客服满意度</h3>
            <span class="muted">点赞 / 点踩</span>
          </div>
          <div class="sat-wrap">
            <div class="sat-ring" :style="satRingStyle">
              <div class="sat-inner">
                <strong>{{ satisfaction }}%</strong>
                <span>满意度</span>
              </div>
            </div>
            <div class="sat-stats">
              <div><em>👍</em> 点赞 {{ stats.chat_feedback_stats?.like || 0 }}</div>
              <div><em>👎</em> 点踩 {{ stats.chat_feedback_stats?.dislike || 0 }}</div>
              <div>会话数 {{ stats.chat_sessions || 0 }}</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12" :lg="7">
        <div class="panel sketch-card">
          <div class="panel-head">
            <h3>最近动态</h3>
            <span class="muted">实时流水</span>
          </div>
          <div class="activity" v-if="(stats.recent_activity || []).length">
            <div v-for="(a, i) in stats.recent_activity" :key="i" class="act-row">
              <span class="act-time">{{ a.time }}</span>
              <span class="act-mod" :class="a.kind">{{ a.module }}</span>
              <span class="act-detail">{{ a.detail }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无动态" />
        </div>
      </el-col>
    </el-row>

    <div class="panel sketch-card advice-panel">
      <div class="panel-head">
        <h3>AI 运营建议</h3>
        <el-button class="sketch-btn" size="small" :loading="adviceLoading" @click="loadAdvice">重新生成</el-button>
      </div>
      <div class="advice-text msg-md" v-if="advice" v-html="renderMarkdown(advice)" />
      <el-empty v-else description="正在生成运营建议…" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import request from '@/api/request'

marked.setOptions({ breaks: true, gfm: true })

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(String(text))
  } catch {
    return String(text).replace(/</g, '&lt;')
  }
}

const COLORS = {
  '文案生成': '#2f6f6a',
  '商品抠图': '#3d7a52',
  '背景生成': '#c45c26',
  '海报合成': '#b7791f',
  '智能客服': '#4a6fa5',
}
const TREND_KEYS = [
  { key: 'writing_calls', name: '文案生成', color: COLORS['文案生成'] },
  { key: 'matte_calls', name: '商品抠图', color: COLORS['商品抠图'] },
  { key: 'bg_calls', name: '背景生成', color: COLORS['背景生成'] },
  { key: 'poster_calls', name: '海报合成', color: COLORS['海报合成'] },
  { key: 'chat_calls', name: '智能客服', color: COLORS['智能客服'] },
]

const stats = ref({
  total_users: 0,
  today_calls: 0,
  yesterday_calls: 0,
  week_calls: 0,
  delta_calls: 0,
  delta_pct: null,
  feature_usage: {},
  feature_ratio: {},
  hot_categories: [],
  platforms: [],
  funnel: [],
  module_health: [],
  error_alerts: [],
  chat_feedback_stats: { like: 0, dislike: 0 },
  satisfaction: 100,
  chat_sessions: 0,
  poster_total: 0,
  recent_activity: [],
})
const trend = ref([])
const advice = ref('')
const adviceLoading = ref(false)
const refreshing = ref(false)
const liveHint = ref('实时通道连接中…')
const liveOk = ref(false)
let ws = null

const satisfaction = computed(() => {
  if (typeof stats.value.satisfaction === 'number') return stats.value.satisfaction
  const l = stats.value.chat_feedback_stats?.like || 0
  const d = stats.value.chat_feedback_stats?.dislike || 0
  if (l + d === 0) return 100
  return Math.round((l / (l + d)) * 100)
})

const topCards = computed(() => {
  const delta = stats.value.delta_calls || 0
  const pct = stats.value.delta_pct
  const deltaText =
    pct == null ? `较昨日 ${delta >= 0 ? '+' : ''}${delta}` : `较昨日 ${delta >= 0 ? '+' : ''}${delta}（${pct}%）`
  return [
    { label: '总用户数', value: stats.value.total_users || 0, color: '#2f6f6a', sub: '平台注册商家/运营' },
    { label: '今日调用', value: stats.value.today_calls || 0, color: '#3d7a52', sub: deltaText },
    { label: '近7日调用', value: stats.value.week_calls || 0, color: '#c45c26', sub: '五模块合计' },
    { label: '海报产出', value: stats.value.poster_total || 0, color: '#b7791f', sub: '历史累计张数' },
    { label: '客服满意度', value: satisfaction.value + '%', color: '#4a6fa5', sub: `会话 ${stats.value.chat_sessions || 0}` },
    {
      label: '异常预警',
      value: (stats.value.error_alerts || []).length,
      color: '#b42318',
      sub: (stats.value.error_alerts || []).length ? '需关注模块' : '运行正常',
    },
  ]
})

const featureLegend = TREND_KEYS
const featureRows = computed(() =>
  Object.keys(stats.value.feature_usage || {}).map((name) => ({
    name,
    count: stats.value.feature_usage[name] || 0,
    ratio: stats.value.feature_ratio?.[name] || 0,
    color: COLORS[name] || '#2f6f6a',
  }))
)

const trendChart = computed(() => {
  const max = Math.max(...trend.value.map((r) => r.total_calls || 0), 1)
  return trend.value.map((row) => {
    const total = row.total_calls || 0
    const segments = TREND_KEYS.map((t) => {
      const v = row[t.key] || 0
      return { key: t.key, color: t.color, h: total ? (v / max) * 100 : 0, v }
    }).filter((s) => s.v > 0)
    return {
      stat_date: row.stat_date,
      label: String(row.stat_date).slice(5),
      total,
      segments,
      tooltip: TREND_KEYS.map((t) => `${t.name}:${row[t.key] || 0}`).join(' · '),
    }
  })
})

const donut = computed(() => {
  const rows = featureRows.value
  const total = rows.reduce((s, r) => s + r.count, 0)
  if (!total) return { total: 0, segments: [] }
  const C = 2 * Math.PI * 42
  let acc = 0
  const segments = rows
    .filter((r) => r.count > 0)
    .map((r) => {
      const len = (r.count / total) * C
      const offset = C * 0.25 - acc
      acc += len
      return { color: r.color, dash: `${len} ${C - len}`, offset }
    })
  return { total, segments }
})

const satRingStyle = computed(() => {
  const p = satisfaction.value
  return {
    background: `conic-gradient(#3d7a52 0 ${p}%, rgba(44,58,66,0.12) ${p}% 100%)`,
  }
})

function platformWidth(count) {
  const max = Math.max(...(stats.value.platforms || []).map((p) => p.count), 1)
  return Math.round((count / max) * 100)
}

async function loadStats() {
  try {
    const data = await request.get('/dashboard/stats')
    stats.value = { ...stats.value, ...data }
  } catch (e) {
    console.error(e)
  }
}

async function loadTrend() {
  try {
    const data = await request.get('/dashboard/trend')
    trend.value = Array.isArray(data) ? data : data?.items || []
  } catch (e) {
    console.error(e)
  }
}

async function loadAdvice() {
  adviceLoading.value = true
  try {
    const data = await request.get('/dashboard/advice')
    advice.value = data.advice
  } catch (e) {
    console.error(e)
  } finally {
    adviceLoading.value = false
  }
}

async function refreshAll() {
  refreshing.value = true
  try {
    await Promise.all([loadStats(), loadTrend()])
    ElMessage.success('看板已刷新')
  } finally {
    refreshing.value = false
  }
}

async function exportData(type) {
  try {
    const blob = await request.get(`/dashboard/export/${type}`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = type === 'excel' ? 'dashboard_report.xlsx' : 'dashboard_report.pdf'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    // 兼容旧方式
    const token = localStorage.getItem('token')
    window.open(`/api/dashboard/export/${type}?token=${token}`, '_blank')
  }
}

function connectWs() {
  try {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    ws = new WebSocket(`${proto}://${location.host}/api/dashboard/ws`)
    ws.onopen = () => {
      liveOk.value = true
      liveHint.value = 'WebSocket 实时刷新中'
    }
    ws.onmessage = (ev) => {
      try {
        const payload = JSON.parse(ev.data)
        stats.value = { ...stats.value, ...payload }
        liveHint.value = `实时 · ${new Date().toLocaleTimeString()}`
      } catch {}
    }
    ws.onclose = () => {
      liveOk.value = false
      liveHint.value = '实时通道断开，可手动刷新'
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
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-bottom: 8px;
}
.dash-hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-end;
  padding: 18px 20px;
  flex-wrap: wrap;
}
.eyebrow {
  margin: 0 0 4px;
  font-size: 12px;
  letter-spacing: 0.08em;
  color: var(--ink-soft);
  text-transform: uppercase;
}
.hero-desc {
  margin: 6px 0 0;
  color: var(--ink-soft);
  font-size: 13px;
}
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.live-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1.5px solid rgba(44, 58, 66, 0.25);
  border-radius: 999px;
  font-size: 12px;
  background: #fff;
  color: var(--ink-soft);
}
.live-pill.on { color: var(--good); border-color: rgba(61, 122, 82, 0.45); }
.live-pill .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #999;
}
.live-pill.on .dot {
  background: var(--good);
  box-shadow: 0 0 0 3px rgba(61, 122, 82, 0.2);
  animation: pulse 1.6s ease infinite;
}
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

.kpi-row { margin-top: 0 !important; }
.kpi-card {
  padding: 14px 16px;
  margin-bottom: 10px;
  border-left: 4px solid var(--accent, var(--accent));
  min-height: 96px;
}
.kpi-label { font-size: 12px; color: var(--ink-soft); }
.kpi-value {
  margin-top: 4px;
  font-size: 28px;
  font-family: var(--font-display);
  color: var(--ink);
  line-height: 1.2;
}
.kpi-sub { margin-top: 4px; font-size: 12px; color: var(--ink-soft); }

.panel {
  padding: 16px 18px;
  height: 100%;
  margin-bottom: 10px;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 12px;
}
.panel-head h3 {
  margin: 0;
  font-size: 16px;
  font-family: var(--font-display);
}
.muted { font-size: 12px; color: var(--ink-soft); }

.stack-chart {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  height: 200px;
  padding: 8px 4px 0;
}
.stack-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}
.stack-bars {
  flex: 1;
  width: 100%;
  max-width: 36px;
  display: flex;
  flex-direction: column-reverse;
  justify-content: flex-start;
  border-radius: 8px 8px 4px 4px;
  overflow: hidden;
  background: rgba(44, 58, 66, 0.06);
  border: 1.5px solid rgba(44, 58, 66, 0.15);
}
.stack-seg { width: 100%; min-height: 2px; transition: height 0.4s ease; }
.stack-total { margin-top: 6px; font-size: 12px; font-weight: 600; }
.stack-date { font-size: 11px; color: var(--ink-soft); }
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--ink-soft);
}
.legend i {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  margin-right: 6px;
}

.donut-wrap {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}
.donut { width: 140px; height: 140px; }
.donut-track {
  fill: none;
  stroke: rgba(44, 58, 66, 0.08);
  stroke-width: 14;
}
.donut-seg {
  fill: none;
  stroke-width: 14;
  stroke-linecap: butt;
  transform-origin: 60px 60px;
}
.donut-num {
  font-size: 18px;
  font-weight: 700;
  fill: var(--ink);
  font-family: var(--font-display);
}
.donut-label { font-size: 10px; fill: var(--ink-soft); }
.donut-list { flex: 1; min-width: 180px; }
.donut-item {
  display: grid;
  grid-template-columns: 12px 1fr 48px 36px;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  margin-bottom: 8px;
}
.swatch { width: 10px; height: 10px; border-radius: 2px; }
.donut-item .pct, .donut-item .cnt { text-align: right; color: var(--ink-soft); }

.funnel-step { margin-bottom: 4px; }
.funnel-meta {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 4px;
}
.funnel-bar {
  height: 14px;
  border-radius: 999px;
  background: rgba(44, 58, 66, 0.08);
  border: 1.5px solid rgba(44, 58, 66, 0.15);
  overflow: hidden;
}
.funnel-fill {
  height: 100%;
  background: linear-gradient(90deg, #2f6f6a, #7eb8a8);
  border-radius: 999px;
  transition: width 0.45s ease;
}
.funnel-arrow { text-align: center; color: var(--ink-soft); font-size: 12px; margin: 2px 0; }

.rank-row, .platform-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.rank-idx {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 12px;
  background: rgba(44, 58, 66, 0.08);
}
.rank-idx.top { background: #2f6f6a; color: #fff; }
.rank-body { flex: 1; min-width: 0; }
.rank-name { font-size: 13px; margin-bottom: 4px; }
.rank-track, .platform-track {
  height: 8px;
  border-radius: 999px;
  background: rgba(44, 58, 66, 0.08);
  overflow: hidden;
}
.rank-fill {
  height: 100%;
  background: linear-gradient(90deg, #c45c26, #e0a070);
}
.rank-cnt { font-size: 12px; color: var(--ink-soft); width: 28px; text-align: right; }
.platform-row span { width: 72px; font-size: 13px; }
.platform-row .platform-track { flex: 1; }
.platform-fill {
  height: 100%;
  background: linear-gradient(90deg, #4a6fa5, #8fb0d8);
}
.platform-row b { width: 32px; text-align: right; font-size: 12px; }

.health-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.health-item {
  border: 1.5px solid rgba(44, 58, 66, 0.18);
  border-radius: 12px;
  padding: 10px;
  background: #fff;
}
.health-item.ok { border-color: rgba(61, 122, 82, 0.35); }
.health-item.warn { border-color: rgba(183, 121, 31, 0.45); background: #fffaf0; }
.health-item.critical { border-color: rgba(180, 35, 24, 0.45); background: #fff5f3; }
.health-name { font-size: 12px; color: var(--ink-soft); }
.health-rate { font-size: 22px; font-family: var(--font-display); margin-top: 2px; }
.health-sub { font-size: 11px; color: var(--ink-soft); margin-top: 2px; }
.ok-line { color: var(--good); text-align: center; margin: 12px 0 0; font-size: 13px; }

.sat-wrap {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}
.sat-ring {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  padding: 10px;
}
.sat-inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.sat-inner strong { font-size: 22px; font-family: var(--font-display); }
.sat-inner span { font-size: 11px; color: var(--ink-soft); }
.sat-stats { display: flex; flex-direction: column; gap: 8px; font-size: 14px; }
.sat-stats em { font-style: normal; margin-right: 4px; }

.activity { max-height: 240px; overflow: auto; }
.act-row {
  display: grid;
  grid-template-columns: 72px 72px 1fr;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px dashed rgba(44, 58, 66, 0.12);
  font-size: 12px;
}
.act-time { color: var(--ink-soft); }
.act-mod {
  border-radius: 999px;
  padding: 1px 6px;
  text-align: center;
  background: rgba(47, 111, 106, 0.12);
}
.act-mod.matte { background: rgba(61, 122, 82, 0.15); }
.act-mod.background { background: rgba(196, 92, 38, 0.15); }
.act-mod.poster { background: rgba(183, 121, 31, 0.18); }
.act-mod.chat { background: rgba(74, 111, 165, 0.15); }
.act-detail { color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.advice-panel { min-height: 120px; }
.advice-text {
  line-height: 1.85;
  font-size: 14px;
  color: var(--ink);
}
.msg-md :deep(p) { margin: 0 0 0.55em; line-height: 1.65; }
.msg-md :deep(p:last-child) { margin-bottom: 0; }
.msg-md :deep(ul), .msg-md :deep(ol) {
  margin: 0.35em 0 0.55em;
  padding-left: 1.25em;
}
.msg-md :deep(li) { margin: 0.2em 0; line-height: 1.55; }
.msg-md :deep(h1), .msg-md :deep(h2), .msg-md :deep(h3) {
  margin: 0.4em 0 0.35em;
  font-family: var(--font-display);
  font-size: 1.05em;
  font-weight: 600;
}
.msg-md :deep(strong) { color: #1f4f4b; font-weight: 650; }
.msg-md :deep(code) {
  background: rgba(44, 58, 66, 0.08);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.92em;
}

@media (max-width: 768px) {
  .act-row { grid-template-columns: 64px 1fr; }
  .act-mod { grid-column: 2; justify-self: start; }
  .health-grid { grid-template-columns: 1fr; }
}
</style>
