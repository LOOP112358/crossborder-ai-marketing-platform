<template>
  <div class="dashboard">
    <!-- 顶部指标卡片 -->
    <el-row :gutter="16" class="top-cards">
      <el-col :span="6" v-for="card in topCards" :key="card.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value" :style="{color:card.color}">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <!-- 功能使用占比 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>各功能调用占比</template>
          <div class="chart-placeholder" style="height:250px">
            <div v-for="(v,k) in stats.feature_usage" :key="k" class="bar-row">
              <span class="bar-label">{{ k }}</span>
              <div class="bar-track"><div class="bar-fill" :style="{width: (stats.feature_ratio[k]||0)+'%'}"></div></div>
              <span class="bar-num">{{ v }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 热门品类 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>热门品类 TOP10</template>
          <div class="chart-placeholder" style="height:250px">
            <el-table :data="stats.hot_categories" size="small" max-height="250">
              <el-table-column type="index" label="#" width="40" />
              <el-table-column prop="name" label="品类" />
              <el-table-column prop="count" label="数量" width="80" align="right" />
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <!-- 运营建议 -->
      <el-col :span="14">
        <el-card shadow="hover">
          <template #header>
            运营建议
            <el-button size="small" style="float:right" @click="loadAdvice" :loading="adviceLoading">刷新</el-button>
          </template>
          <div class="advice-text" v-if="advice">{{ advice }}</div>
          <el-empty v-else description="点击刷新获取AI运营建议" />
        </el-card>
      </el-col>

      <!-- 异常预警 + 反馈 -->
      <el-col :span="10">
        <el-card shadow="hover">
          <template #header>异常预警</template>
          <div v-if="stats.error_alerts.length===0" style="color:#67c23a;text-align:center;padding:20px">
            ✅ 所有模块运行正常
          </div>
          <el-alert v-for="a in stats.error_alerts" :key="a.module"
            :title="a.module" :description="a.message"
            type="error" show-icon style="margin-bottom:8px" />
        </el-card>
        <el-card shadow="hover" style="margin-top:16px">
          <template #header>客服满意度</template>
          <div class="feedback-row">
            <span>👍 {{ stats.chat_feedback_stats?.like || 0 }}</span>
            <span>👎 {{ stats.chat_feedback_stats?.dislike || 0 }}</span>
            <el-tag :type="satisfaction>50?'success':'warning'" size="large">
              满意度 {{ satisfaction }}%
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 导出 -->
    <div style="text-align:right;margin-top:16px">
      <el-button @click="exportData('excel')">
        <el-icon><Download /></el-icon> 导出Excel
      </el-button>
      <el-button @click="exportData('pdf')">
        <el-icon><Download /></el-icon> 导出PDF
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

const stats = ref({
  total_users: 0, today_calls: 0,
  feature_usage: {}, feature_ratio: {},
  hot_categories: [], error_alerts: [],
  chat_feedback_stats: { like: 0, dislike: 0 },
})
const advice = ref('')
const adviceLoading = ref(false)

const satisfaction = computed(() => {
  const l = stats.value.chat_feedback_stats?.like || 0
  const d = stats.value.chat_feedback_stats?.dislike || 0
  if (l + d === 0) return 100
  return Math.round((l / (l + d)) * 100)
})

const topCards = computed(() => [
  { label: '总用户数', value: stats.value.total_users, color: '#409eff' },
  { label: '今日调用量', value: stats.value.today_calls, color: '#67c23a' },
  { label: '客服满意度', value: satisfaction.value + '%', color: '#e6a23c' },
  { label: '异常预警', value: stats.value.error_alerts.length === 0 ? '0' : stats.value.error_alerts.length, color: '#f56c6c' },
])

async function loadStats() {
  try { stats.value = await request.get('/dashboard/stats') } catch {}
}
async function loadAdvice() {
  adviceLoading.value = true
  try { const data = await request.get('/dashboard/advice'); advice.value = data.advice } catch {}
  finally { adviceLoading.value = false }
}
function exportData(type) {
  const token = localStorage.getItem('token')
  window.open(`/api/dashboard/export/${type}?token=${token}`, '_blank')
}

onMounted(() => { loadStats(); loadAdvice() })
</script>

<style scoped>
.dashboard { padding: 0; }
.stat-card { text-align: center; }
.stat-value { font-size: 32px; font-weight: bold; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.bar-label { width: 80px; font-size: 13px; text-align: right; }
.bar-track { flex: 1; height: 20px; background: #f0f2f5; border-radius: 10px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, #409eff, #67c23a); border-radius: 10px; transition: width 0.6s; }
.bar-num { width: 30px; font-size: 12px; color: #909399; }
.advice-text { white-space: pre-wrap; line-height: 1.8; font-size: 14px; }
.feedback-row { display: flex; align-items: center; gap: 16px; font-size: 18px; }
</style>
