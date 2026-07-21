<template>
  <div class="writing-page sketch-shell">
    <!-- 左侧：输入表单 -->
    <div class="input-panel">
      <el-card shadow="never">
        <template #header>
          <span class="panel-title"><el-icon><Edit /></el-icon> {{ $t('writing.title') }}</span>
        </template>
        <el-form :model="form" label-position="top" size="default">
          <el-form-item :label="$t('writing.pickFromCatalog')">
            <el-select
              v-model="selectedProductId"
              filterable
              remote
              clearable
              :remote-method="remoteSearchProducts"
              :loading="searchingProducts"
              :placeholder="$t('writing.catalogSearchPlaceholder')"
              style="width:100%"
              @change="onProductPicked"
              @clear="clearCatalogSelection"
            >
              <el-option
                v-for="p in productOptions"
                :key="p.id"
                :label="p.label"
                :value="p.id"
              >
                <div class="product-opt">
                  <img v-if="p.image_url" :src="p.image_url" class="product-opt-thumb" alt="" />
                  <div>
                    <span class="product-opt-name">{{ p.name }}</span>
                    <span class="product-opt-meta">{{ p.brand || p.category || p.product_type }}{{ p.has_image ? ' · 有图' : '' }}</span>
                  </div>
                </div>
              </el-option>
            </el-select>
            <p class="catalog-hint">{{ $t('writing.pickFromCatalogHint') }}</p>
            <p v-if="catalogTotal != null" class="catalog-count">
              {{ $t('writing.catalogTotal', { n: catalogTotal }) }}
              <span v-if="withImage != null"> · 有图 {{ withImage }}</span>
            </p>
          </el-form-item>
          <el-form-item :label="$t('writing.productName')" required>
            <el-input v-model="form.product_name" :placeholder="$t('writing.productNamePlaceholder')" />
          </el-form-item>
          <el-form-item :label="$t('writing.productFeatures')">
            <el-input v-model="form.product_features" type="textarea" :rows="4"
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

          <!-- 风格选择 — 手绘线稿图标 -->
          <el-form-item :label="$t('writing.style')">
            <div class="style-grid">
              <div
                v-for="s in styleOptions" :key="s.value"
                class="style-card"
                :class="{ active: form.style === s.value }"
                @click="form.style = s.value"
              >
                <span class="style-icon" v-html="STYLE_ICONS[s.value]" aria-hidden="true"></span>
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
            <el-tag size="small" type="info">
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { generateCopywriting, getWritingHistory, searchWritingProducts } from '@/api/writing'
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

const selectedProductId = ref(null)
const productOptions = ref([])
const searchingProducts = ref(false)
const catalogTotal = ref(null)
const withImage = ref(null)
let searchTimer = null

async function remoteSearchProducts(query) {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    searchingProducts.value = true
    try {
      const data = await searchWritingProducts(query || '', 20, false, { diverse: !query })
      productOptions.value = data.items || []
      if (data.catalog_total != null) catalogTotal.value = data.catalog_total
      if (data.with_image != null) withImage.value = data.with_image
    } catch {
      productOptions.value = []
    } finally {
      searchingProducts.value = false
    }
  }, 280)
}

function onProductPicked(id) {
  if (!id) return
  const p = productOptions.value.find((x) => x.id === id)
  if (!p) return
  form.product_name = p.name || p.item_name || ''
  form.product_features = p.features || ''
  ElMessage.success(t('writing.catalogSelected'))
}

function clearCatalogSelection() {
  selectedProductId.value = null
}

onMounted(() => {
  remoteSearchProducts('')
})

// 手绘线稿图标（青绿描边，与 sketch 主题一致）
const STYLE_ICONS = {
  professional: `<svg viewBox="0 0 48 48" fill="none"><path d="M10 18.2c8.5-.8 19.2-.6 28.2.4v18.6c-9.2.9-19.4.7-28.2-.3V18.2z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M10 18.5c2.2-5.2 7.4-7.8 14.1-7.6 6.4.2 11.2 2.9 13.9 7.8" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><path d="M21.5 18.2v3.8c0 1.6 1.2 2.6 2.7 2.6s2.6-1 2.6-2.6v-3.9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M14 26.5h6.2M28 26.5h6.5M14 31.5h20.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity=".75"/></svg>`,
  casual: `<svg viewBox="0 0 48 48" fill="none"><path d="M24.2 38c-1.2-6.8-1.5-12.4-.4-17.2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><path d="M23.8 22.2c-4.6-5.2-9.8-6.8-13.6-4.4-2.8 1.8-2.6 5.6.6 7.4 3.6 2.1 8.4.6 13-3" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><path d="M24.6 20.8c4.2-4.8 9.4-6.2 13.1-3.6 2.6 1.9 2.2 5.5-.8 7.1-3.4 1.8-8.2.4-12.3-3.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><path d="M18 36.5c3.8 1.4 8.2 1.5 12 .2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity=".7"/></svg>`,
  minimalist: `<svg viewBox="0 0 48 48" fill="none"><rect x="14.5" y="14.5" width="19" height="19" rx="1.5" stroke="currentColor" stroke-width="1.7" transform="rotate(-2 24 24)"/><path d="M18 30.5h12.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="24" cy="22.5" r="2.2" stroke="currentColor" stroke-width="1.5"/></svg>`,
  emotional: `<svg viewBox="0 0 48 48" fill="none"><path d="M24.1 36.5c-7.8-5.2-12.6-10.4-12.4-16.2.2-4.2 3.4-7 7.4-6.8 2.4.1 4.4 1.4 5.2 3.2.9-1.9 2.9-3.3 5.4-3.4 4.1-.2 7.2 2.8 7.2 7.1 0 5.7-5.2 10.8-12.8 16.1z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M17.5 22.8c1.2-1.8 3.1-2.6 4.8-2.2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" opacity=".65"/></svg>`,
  humorous: `<svg viewBox="0 0 48 48" fill="none"><path d="M12.5 24.2c.4-7.2 5.6-12.4 11.8-12.6 6.4-.2 11.4 4.8 11.6 12.1.2 6.8-4.9 12.4-11.5 12.5-6.4.2-12.2-5-11.9-12z" stroke="currentColor" stroke-width="1.7"/><path d="M18.2 21.2c.6-1.4 1.7-2.2 2.9-2.1M27 21c.7-1.3 1.8-2 3-1.9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M17.8 27.2c2.2 3.4 5.2 5 6.6 5.1 1.5.1 4.4-1.6 6.4-5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><path d="M33.5 14.5c1.6-2.2 3.8-3.2 5.6-2.6M36.2 17.8c1.8-.2 3.4.6 4.4 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity=".8"/></svg>`,
  luxury: `<svg viewBox="0 0 48 48" fill="none"><path d="M10.5 20.5l5.2-7.2 4.6 4.8L24 11.2l3.8 6.9 4.5-4.6 5.1 7.1-3.2 12.8H13.6L10.5 20.5z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M14.2 33.8h19.6c.8 2.6-.2 4.4-3.2 4.6H17.2c-2.9-.1-3.9-2-3-4.6z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M21.5 23.2h5.2M24.1 20.5v5.6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity=".75"/></svg>`,
}

const styleOptions = computed(() => [
  { value: 'professional', label: t('writing.styleProfessional'), desc: t('writing.styleDesc.professional') },
  { value: 'casual',       label: t('writing.styleCasual'),       desc: t('writing.styleDesc.casual') },
  { value: 'minimalist',   label: t('writing.styleMinimalist'),   desc: t('writing.styleDesc.minimalist') },
  { value: 'emotional',    label: t('writing.styleEmotional'),    desc: t('writing.styleDesc.emotional') },
  { value: 'humorous',     label: t('writing.styleHumorous'),     desc: t('writing.styleDesc.humorous') },
  { value: 'luxury',       label: t('writing.styleLuxury'),       desc: t('writing.styleDesc.luxury') },
])

const langNames = { zh: '中文', en: 'English', ja: '日本語', ko: '한국어', es: 'Español' }

function getLangName(lang) { return langNames[lang] || lang }
function getStyleName(style) { return t(`writing.style${style.charAt(0).toUpperCase() + style.slice(1)}`) }

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
.catalog-hint { margin: 6px 0 0; font-size: 12px; color: #909399; line-height: 1.4; }
.catalog-count { margin: 4px 0 0; font-size: 12px; color: #67a090; }
.product-opt { display: flex; flex-direction: row; align-items: center; gap: 8px; line-height: 1.35; max-width: 320px; }
.product-opt-thumb { width: 32px; height: 32px; object-fit: cover; border-radius: 6px; border: 1px solid #ddd; flex-shrink: 0; }
.product-opt-name { display: block; font-size: 13px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 260px; }
.product-opt-meta { display: block; font-size: 11px; color: #909399; }

/* 风格卡片 — 手绘感 */
.style-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; width: 100%; }
.style-card {
  border: 2px solid var(--line, #2c3a42);
  border-radius: 14px 18px 12px 16px / 16px 12px 18px 14px;
  padding: 12px 8px 10px;
  cursor: pointer;
  text-align: center;
  transition: transform 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.55);
  box-shadow: 2px 3px 0 rgba(36, 48, 56, 0.08);
  color: var(--accent, #2f6f6a);
}
.style-card:hover {
  transform: translate(-1px, -1px);
  background: var(--wash, #d7e8df);
  box-shadow: 3px 4px 0 rgba(36, 48, 56, 0.12);
}
.style-card.active {
  background: var(--wash, #d7e8df);
  box-shadow: 3px 4px 0 rgba(47, 111, 106, 0.22);
  color: var(--accent, #2f6f6a);
}
.style-icon {
  display: flex;
  width: 36px;
  height: 36px;
  margin-bottom: 2px;
}
.style-icon :deep(svg) {
  width: 100%;
  height: 100%;
}
.style-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink, #243038);
  font-family: var(--font-display, inherit);
}
.style-desc {
  font-size: 11px;
  color: var(--ink-soft, #4a5a63);
  line-height: 1.35;
}

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
