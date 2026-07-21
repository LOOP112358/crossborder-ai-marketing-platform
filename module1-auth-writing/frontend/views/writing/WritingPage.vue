<template>
  <div class="writing-page">
    <!-- 左侧：输入表单 -->
    <div class="input-panel">
      <el-card shadow="never">
        <template #header>
          <span class="panel-title"><el-icon><Edit /></el-icon> {{ $t('writing.title') }}</span>
        </template>
        <el-form :model="form" label-position="top" size="default">
          <el-form-item :label="$t('writing.productName')" required>
            <el-input v-model="form.product_name" :placeholder="$t('writing.productNamePlaceholder')" />
          </el-form-item>
          <el-form-item :label="$t('writing.productFeatures')">
            <el-input v-model="form.product_features" type="textarea" :rows="3"
              :placeholder="$t('writing.featuresPlaceholder')" />
          </el-form-item>
          <el-form-item :label="$t('writing.platform')">
            <el-select v-model="form.platforms" multiple :placeholder="$t('writing.platformPlaceholder')" style="width:100%">
              <el-option label="TikTok" value="TikTok" />
              <el-option label="Instagram" value="Instagram" />
              <el-option label="Amazon" value="Amazon" />
            </el-select>
          </el-form-item>
          <el-form-item :label="$t('writing.language')">
            <el-select v-model="form.language" style="width:100%">
              <el-option :label="$t('lang.zhCN')" value="zh" />
              <el-option :label="$t('lang.en')" value="en" />
              <el-option :label="$t('lang.ja')" value="ja" />
              <el-option :label="$t('lang.ko')" value="ko" />
              <el-option :label="$t('lang.es')" value="es" />
            </el-select>
          </el-form-item>

          <!-- 风格选择 — 增强版：6风格卡片 -->
          <el-form-item :label="$t('writing.style')">
            <div class="style-grid">
              <div
                v-for="s in styleOptions" :key="s.value"
                class="style-card"
                :class="{ active: form.style === s.value }"
                @click="form.style = s.value"
              >
                <span class="style-emoji">{{ s.emoji }}</span>
                <span class="style-name">{{ s.label }}</span>
                <span class="style-desc">{{ s.desc }}</span>
              </div>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" size="large" :loading="generating" block @click="handleGenerate">
              <el-icon><MagicStick /></el-icon> {{ generating ? $t('writing.generating') : $t('writing.generateBtn') }}
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 右侧：结果展示 -->
    <div class="result-panel">
      <div v-if="results.length > 0">
        <el-card v-for="(item, idx) in results" :key="idx" class="result-card" shadow="hover">
          <div class="result-header">
            <el-tag type="primary" size="large">{{ item.platform }}</el-tag>
            <el-tag size="small">{{ getLangName(item.language) }}</el-tag>
            <el-tag size="small" :type="getStyleTagType(item.style)">
              <span class="style-emoji-sm">{{ getStyleEmoji(item.style) }}</span>
              {{ getStyleName(item.style) }}
            </el-tag>
            <el-button size="small" text type="primary" @click="copyAll(item)">
              <el-icon><CopyDocument /></el-icon> {{ $t('common.copyAll') }}
            </el-button>
          </div>
          <el-divider margin="12px 0" />
          <div class="result-field">
            <span class="field-label">{{ $t('writing.resultTitle') }}</span>
            <el-button size="small" text type="primary" @click="copyText(item.title)">{{ $t('common.copy') }}</el-button>
            <p class="field-value title">{{ item.title }}</p>
          </div>
          <div class="result-field">
            <span class="field-label">{{ $t('writing.resultBody') }}</span>
            <el-button size="small" text type="primary" @click="copyText(item.body)">{{ $t('common.copy') }}</el-button>
            <p class="field-value body">{{ item.body }}</p>
          </div>
          <div class="result-field">
            <span class="field-label">{{ $t('writing.resultTags') }}</span>
            <el-button size="small" text type="primary" @click="copyText(item.tags)">{{ $t('common.copy') }}</el-button>
            <p class="field-value tags">{{ item.tags }}</p>
          </div>
        </el-card>
      </div>

      <!-- 空状态 -->
      <el-empty v-else description="选择风格 → 输入商品信息 → 点击生成" />

      <!-- 历史记录 -->
      <div class="history-bar">
        <el-button text type="primary" @click="openHistory" :loading="loadingHistory" v-if="!showHistory">
          <el-icon><Clock /></el-icon> {{ $t('writing.history') }}
        </el-button>
      </div>
    </div>

    <!-- 历史记录抽屉 -->
    <el-drawer v-model="showHistory" :title="$t('writing.historyTitle')" direction="rtl" size="450px">
      <div v-loading="loadingHistory">
        <div v-if="historyList.length === 0">
          <el-empty :description="$t('writing.noHistory')" />
        </div>
        <el-card v-for="item in historyList" :key="item.id" class="history-card" shadow="hover" size="small">
          <div class="history-item">
            <p class="history-product"><strong>{{ item.product_name }}</strong></p>
            <p class="history-meta">
              <el-tag size="small">{{ item.platform }}</el-tag>
              <el-tag size="small" type="info">{{ item.language }}</el-tag>
              <el-tag size="small">{{ item.style }}</el-tag>
            </p>
            <p class="history-title">{{ item.title }}</p>
            <p class="history-body">{{ item.body?.substring(0, 100) }}{{ item.body?.length > 100 ? '...' : '' }}</p>
            <p class="history-time">{{ item.created_at }}</p>
            <el-button size="small" type="primary" text @click="reloadFromHistory(item)">
              {{ $t('writing.reload') }}
            </el-button>
          </div>
        </el-card>
        <div class="pagination-wrap" v-if="historyTotal > 0">
          <el-pagination
            v-model:current-page="historyPage"
            :page-size="historyPageSize"
            :total="historyTotal"
            layout="prev, pager, next"
            small
            @current-change="loadHistory"
          />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { generateCopywriting, getWritingHistory } from '@/api/writing'
import { ElMessage } from 'element-plus'

const { t, locale } = useI18n()
const generating = ref(false)
const results = ref([])

const form = reactive({
  product_name: '',
  product_features: '',
  platforms: ['TikTok'],
  language: 'zh',
  style: 'professional',
})

// 6种风格选项（响应式，随语言切换变化）
const styleOptions = computed(() => [
  { value: 'professional', emoji: '💼', label: t('writing.styleProfessional'), desc: t('writing.styleDesc.professional') },
  { value: 'casual',       emoji: '🌱', label: t('writing.styleCasual'),       desc: t('writing.styleDesc.casual') },
  { value: 'minimalist',   emoji: '🤍', label: t('writing.styleMinimalist'),   desc: t('writing.styleDesc.minimalist') },
  { value: 'emotional',    emoji: '💙', label: t('writing.styleEmotional'),    desc: t('writing.styleDesc.emotional') },
  { value: 'humorous',     emoji: '😂', label: t('writing.styleHumorous'),     desc: t('writing.styleDesc.humorous') },
  { value: 'luxury',       emoji: '👑', label: t('writing.styleLuxury'),       desc: t('writing.styleDesc.luxury') },
])

const langNames = { zh: '中文', en: 'English', ja: '日本語', ko: '한국어', es: 'Español' }
const styleNames = {
  professional: '💼', casual: '🌱', minimalist: '🤍',
  emotional: '💙', humorous: '😂', luxury: '👑',
}
const styleTagType = {
  professional: '', casual: 'success', minimalist: 'info',
  emotional: 'warning', humorous: 'danger', luxury: 'warning',
}

function getLangName(lang) { return langNames[lang] || lang }
function getStyleEmoji(style) { return styleNames[style] || '' }
function getStyleName(style) { return t(`writing.style${style.charAt(0).toUpperCase() + style.slice(1)}`) }
function getStyleTagType(style) { return styleTagType[style] || '' }

async function handleGenerate() {
  if (!form.product_name.trim()) {
    ElMessage.warning(t('writing.productNameRequired'))
    return
  }
  if (form.platforms.length === 0) {
    ElMessage.warning(t('writing.platformRequired'))
    return
  }
  generating.value = true
  try {
    const data = await generateCopywriting(form)
    results.value = data.results
    ElMessage.success(t('writing.generateSuccess'))
  } catch {
    // handled
  } finally {
    generating.value = false
  }
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success(t('common.copied'))
  }).catch(() => {
    ElMessage.error(t('common.copyFailed'))
  })
}

function copyAll(item) {
  const text = `【${t('writing.resultTitle')}】${item.title}\n【${t('writing.resultBody')}】${item.body}\n【${t('writing.resultTags')}】${item.tags}`
  copyText(text)
}

// 历史记录
const showHistory = ref(false)
const loadingHistory = ref(false)
const historyList = ref([])
const historyPage = ref(1)
const historyPageSize = ref(20)
const historyTotal = ref(0)

async function openHistory() { showHistory.value = true; await loadHistory() }
async function loadHistory() {
  loadingHistory.value = true
  try {
    const data = await getWritingHistory(historyPage.value, historyPageSize.value)
    historyList.value = data.items; historyTotal.value = data.total
  } finally { loadingHistory.value = false }
}
function reloadFromHistory(item) {
  form.product_name = item.product_name
  form.product_features = item.product_features || ''
  if (item.platform) form.platforms = item.platform.split(', ')
  form.language = item.language || 'zh'
  form.style = item.style || 'professional'
  showHistory.value = false
}
</script>

<style scoped>
.writing-page { display: flex; gap: 20px; min-height: calc(100vh - 120px); }
.input-panel { width: 400px; flex-shrink: 0; }
.result-panel { flex: 1; }
.panel-title { display: flex; align-items: center; gap: 6px; font-weight: 600; }

/* 风格卡片 */
.style-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; width: 100%; }
.style-card {
  border: 2px solid #e8e8e8;
  border-radius: 8px;
  padding: 10px;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.style-card:hover { border-color: #409eff; background: #ecf5ff; }
.style-card.active { border-color: #409eff; background: #ecf5ff; box-shadow: 0 0 0 2px rgba(64,158,255,.2); }
.style-emoji { font-size: 24px; }
.style-name { font-size: 13px; font-weight: 600; color: #303133; }
.style-desc { font-size: 11px; color: #909399; line-height: 1.3; }
.style-emoji-sm { margin-right: 2px; }

.result-card { margin-bottom: 16px; }
.result-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.result-field { margin-bottom: 12px; }
.field-label { font-weight: 600; margin-right: 8px; color: #606266; }
.field-value { margin: 4px 0 0; line-height: 1.8; white-space: pre-wrap; }
.field-value.title { font-size: 16px; font-weight: 600; color: #303133; }
.field-value.body { color: #606266; }
.field-value.tags { color: #409eff; }
.history-bar { margin-top: 16px; text-align: center; }
.history-card { margin-bottom: 12px; }
.history-product { margin: 0 0 4px; }
.history-meta { display: flex; gap: 4px; margin: 0 0 6px; }
.history-title { margin: 0 0 4px; font-weight: 500; color: #303133; }
.history-body { margin: 0 0 4px; font-size: 13px; color: #909399; }
.history-time { margin: 0 0 6px; font-size: 12px; color: #c0c4cc; }
.pagination-wrap { display: flex; justify-content: center; margin-top: 16px; }
</style>
