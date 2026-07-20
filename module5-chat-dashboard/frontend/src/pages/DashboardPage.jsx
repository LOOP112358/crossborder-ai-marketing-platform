import { useState, useEffect, useCallback, useRef } from 'react'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { PieChart, LineChart, BarChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { dashboardApi } from '../api/client'

echarts.use([PieChart, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer])

/* ---- palette (from validated reference) ---- */
const CAT = ['#2a78d6', '#008300', '#e87ba4', '#eda100', '#1baf7a']
const FEATURE_KEYS = ['文案生成', '商品抠图', '背景生成', '海报合成', '智能客服']
const TREND_FIELDS = ['writing_calls', 'matte_calls', 'bg_calls', 'poster_calls', 'chat_calls']

/* ---- chart base theme ---- */
const chartTheme = {
  textStyle: { fontFamily: "system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif" },
  legend: { textStyle: { color: '#52514e' }, icon: 'roundRect', itemWidth: 10, itemHeight: 10 },
}

/* ================================================================
   DashboardPage — 运营看板
   ================================================================ */
export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [trend, setTrend] = useState([])
  const [advice, setAdvice] = useState('')
  const [loading, setLoading] = useState(true)
  const [adviceLoading, setAdviceLoading] = useState(false)
  const [error, setError] = useState('')
  const wsRef = useRef(null)

  /* fetch all data */
  const fetchData = useCallback(async () => {
    try {
      setError('')
      const [statsRes, trendRes] = await Promise.all([
        dashboardApi.stats(),
        dashboardApi.trend(),
      ])
      setStats(statsRes.data)
      setTrend(trendRes.data)
    } catch (e) {
      setError('数据加载失败，请确认后端已启动')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [])

  /* fetch AI advice */
  const fetchAdvice = useCallback(async () => {
    setAdviceLoading(true)
    try {
      const res = await dashboardApi.advice()
      setAdvice(res.data.advice)
    } catch (e) {
      console.error('获取AI建议失败', e)
    } finally {
      setAdviceLoading(false)
    }
  }, [])

  /* initial load */
  useEffect(() => { fetchData() }, [fetchData])
  useEffect(() => { fetchAdvice() }, [fetchAdvice])

  /* WebSocket realtime refresh */
  useEffect(() => {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${location.host}/api/dashboard/ws`
    let ws
    let reconnectTimer
    const connect = () => {
      ws = new WebSocket(wsUrl)
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data)
          setStats(data)
        } catch {}
      }
      ws.onclose = () => { reconnectTimer = setTimeout(connect, 5000) }
      ws.onerror = () => { ws?.close() }
    }
    connect()
    return () => {
      clearTimeout(reconnectTimer)
      ws?.close()
    }
  }, [])

  /* export */
  const handleExport = async (type) => {
    try {
      const fn = type === 'excel' ? dashboardApi.exportExcel : dashboardApi.exportPdf
      const res = await fn()
      const blob = new Blob([res.data], {
        type: type === 'excel'
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'application/pdf',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `dashboard_report.${type === 'excel' ? 'xlsx' : 'pdf'}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error('导出失败', e)
    }
  }

  /* ========== chart options ========== */

  /* doughnut — feature usage ratio */
  const doughnutOption = stats ? {
    color: CAT,
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 次 ({d}%)',
      backgroundColor: '#fff',
      borderColor: '#e5e7eb',
      textStyle: { color: '#0b0b0b' },
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#52514e', fontSize: 12 },
      itemWidth: 10,
      itemHeight: 10,
    },
    series: [{
      type: 'pie',
      radius: ['52%', '78%'],
      center: ['38%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 4,
        borderColor: '#fcfcfb',
        borderWidth: 2,
      },
      label: {
        show: true,
        position: 'inside',
        formatter: '{d}%',
        fontSize: 11,
        fontWeight: 600,
        color: '#fff',
      },
      emphasis: {
        label: { fontSize: 16, fontWeight: 'bold' },
      },
      data: FEATURE_KEYS.map((name, i) => ({
        name,
        value: stats.feature_usage[name] || 0,
      })),
    }],
  } : null

  /* line chart — 7-day trend */
  const trendOption = trend.length > 0 ? {
    color: CAT,
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#fff',
      borderColor: '#e1e0d9',
      textStyle: { color: '#0b0b0b', fontSize: 12 },
    },
    legend: {
      data: FEATURE_KEYS,
      bottom: 0,
      textStyle: { color: '#52514e', fontSize: 11 },
      itemWidth: 12,
      itemHeight: 2,
      icon: 'roundRect',
    },
    grid: { left: 10, right: 30, top: 20, bottom: 50 },
    xAxis: {
      type: 'category',
      data: trend.map(t => t.stat_date.slice(5)), // MM-DD
      axisLine: { lineStyle: { color: '#c3c2b7' } },
      axisTick: { show: false },
      axisLabel: { color: '#898781', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#e1e0d9', type: 'dashed' } },
      axisLabel: { color: '#898781', fontSize: 11 },
    },
    series: FEATURE_KEYS.map((name, i) => ({
      name,
      type: 'line',
      data: trend.map(t => t[TREND_FIELDS[i]] || 0),
      smooth: true,
      symbol: 'circle',
      symbolSize: 5,
      lineStyle: { width: 2 },
    })),
  } : null

  /* error bar chart — tiny */
  const errorOption = trend.length > 0 ? {
    color: ['#d03b3b'],
    tooltip: { trigger: 'axis' },
    grid: { left: 10, right: 10, top: 8, bottom: 20 },
    xAxis: {
      type: 'category',
      data: trend.map(t => t.stat_date.slice(5)),
      axisLabel: { color: '#898781', fontSize: 10 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#e1e0d9', type: 'dashed' } },
      axisLabel: { color: '#898781', fontSize: 10 },
      minInterval: 1,
    },
    series: [{
      type: 'bar',
      data: trend.map(t => t.error_count || 0),
      barWidth: 14,
      itemStyle: { borderRadius: [3, 3, 0, 0] },
    }],
  } : null

  /* ========== render ========== */
  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="loading-center" style={{ height: 400 }}>
          <span className="spinner" />&nbsp; 加载看板数据…
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-page">
      {error && <div className="error-banner">{error}</div>}

      <h2>📊 运营数据看板</h2>

      {/* ---- stat cards ---- */}
      <div className="stat-cards">
        <div className="stat-card">
          <div className="stat-icon users">👥</div>
          <div className="stat-info">
            <div className="stat-value">{stats?.total_users ?? 0}</div>
            <div className="stat-label">总用户数</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon calls">📞</div>
          <div className="stat-info">
            <div className="stat-value">{stats?.today_calls ?? 0}</div>
            <div className="stat-label">今日总调用</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon chat">💬</div>
          <div className="stat-info">
            <div className="stat-value">{stats?.feature_usage?.['智能客服'] ?? 0}</div>
            <div className="stat-label">客服调用</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon errors">
            {stats?.error_alerts?.length > 0 ? '⚠️' : '✅'}
          </div>
          <div className="stat-info">
            <div className="stat-value">{stats?.error_alerts?.length ?? 0}</div>
            <div className="stat-label">异常预警</div>
          </div>
        </div>
      </div>

      {/* ---- row: feature ratios + hot categories ---- */}
      <div className="dashboard-grid">
        {/* doughnut */}
        <div className="panel">
          <div className="panel-header">📈 功能使用占比（今日）</div>
          <div className="panel-body">
            {doughnutOption ? (
              <ReactEChartsCore
                echarts={echarts}
                option={doughnutOption}
                theme={chartTheme}
                style={{ height: 300 }}
                opts={{ renderer: 'canvas' }}
              />
            ) : (
              <div className="loading-center">暂无数据</div>
            )}
          </div>
        </div>

        {/* hot categories */}
        <div className="panel">
          <div className="panel-header">🔥 热门品类排行</div>
          <div className="panel-body">
            {stats?.hot_categories?.length > 0 ? (
              <ul className="hot-list">
                {stats.hot_categories.map((cat, i) => (
                  <li key={cat.name}>
                    <span className={`hot-rank${i < 3 ? ` top-${i + 1}` : ''}`}>
                      {i + 1}
                    </span>
                    <span className="hot-name">{cat.name}</span>
                    <span className="hot-count">{cat.count}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="loading-center" style={{ height: 100, fontSize: 13 }}>
                暂无品类数据
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ---- row: trend line + error bars ---- */}
      <div className="dashboard-grid">
        {/* 7-day trend */}
        <div className="panel">
          <div className="panel-header">📅 近 7 天调用趋势</div>
          <div className="panel-body">
            {trendOption ? (
              <ReactEChartsCore
                echarts={echarts}
                option={trendOption}
                theme={chartTheme}
                style={{ height: 300 }}
                opts={{ renderer: 'canvas' }}
              />
            ) : (
              <div className="loading-center">暂无趋势数据</div>
            )}
          </div>
        </div>

        {/* error count + feedback */}
        <div className="panel">
          <div className="panel-header">⚠️ 错误量 & 客服反馈</div>
          <div className="panel-body">
            {errorOption ? (
              <ReactEChartsCore
                echarts={echarts}
                option={errorOption}
                theme={chartTheme}
                style={{ height: 180 }}
                opts={{ renderer: 'canvas' }}
              />
            ) : (
              <div className="loading-center" style={{ height: 100 }}>暂无数据</div>
            )}

            <div style={{ marginTop: 16, borderTop: '1px solid var(--gray-100)', paddingTop: 14 }}>
              <div style={{ fontSize: 13, color: 'var(--gray-500)', marginBottom: 8 }}>客服反馈统计</div>
              <div className="feedback-mini">
                <div className="fb-item fb-like">
                  👍 {stats?.chat_feedback_stats?.like ?? 0}
                </div>
                <div className="fb-item fb-dislike">
                  👎 {stats?.chat_feedback_stats?.dislike ?? 0}
                </div>
                <div style={{ fontSize: 13, color: 'var(--gray-400)' }}>
                  好评率 {stats ? (
                    (stats.chat_feedback_stats.like + stats.chat_feedback_stats.dislike) > 0
                      ? Math.round(stats.chat_feedback_stats.like / (stats.chat_feedback_stats.like + stats.chat_feedback_stats.dislike) * 100)
                      : 0
                  ) : 0}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ---- alerts ---- */}
      {stats?.error_alerts?.length > 0 && (
        <div className="dashboard-grid">
          <div className="panel full-width">
            <div className="panel-header">
              🚨 异常预警
              <span style={{ fontSize: 12, color: 'var(--danger)', fontWeight: 400 }}>
                {stats.error_alerts.length} 个模块错误率超过 10%
              </span>
            </div>
            <div className="panel-body">
              <div className="alert-list">
                {stats.error_alerts.map((a, i) => (
                  <div key={i} className="alert-item">
                    ⚠️ {a.message}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ---- AI advice ---- */}
      <div className="dashboard-grid">
        <div className="panel full-width">
          <div className="panel-header">
            🤖 AI 运营建议
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn-refresh-advice" onClick={fetchAdvice} disabled={adviceLoading}>
                {adviceLoading ? '分析中…' : '🔄 刷新建议'}
              </button>
              <button className="btn-export" onClick={() => handleExport('excel')}>
                📥 Excel
              </button>
              <button className="btn-export" onClick={() => handleExport('pdf')}>
                📄 PDF
              </button>
            </div>
          </div>
          <div className="panel-body">
            {advice ? (
              <div className="advice-card">
                <div className="advice-label">AI 运营分析</div>
                {advice}
              </div>
            ) : (
              <div className="loading-center" style={{ height: 60, fontSize: 13 }}>
                {adviceLoading ? 'AI 正在分析运营数据…' : '点击「刷新建议」获取 AI 分析'}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
