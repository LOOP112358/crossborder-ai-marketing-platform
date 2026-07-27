<template>
  <div class="catalog-page" :class="{ 'has-select-bar': !!selected }">
    <header class="hero sketch-card">
      <div class="hero-copy">
        <p class="eyebrow">Merchant · ABO Catalog</p>
        <h1 class="sketch-title">智能选品中心</h1>
        <p class="lead">
          从亚马逊开源 ABO 库检索真实货盘；选定后进入「文案 · 海报」工作流（文案与海报均可跳过）。独立模块仍可单独使用。
        </p>
        <div class="stat-row">
          <div class="stat">
            <strong>{{ catalogTotal ?? '—' }}</strong>
            <span>库内商品</span>
          </div>
          <div class="stat">
            <strong>{{ mode === 'browse' ? items.length : campaignItems.length }}</strong>
            <span>{{ mode === 'browse' ? '当前结果' : '方案数' }}</span>
          </div>
        </div>
      </div>
    </header>

    <nav class="mode-tabs sketch-card" role="tablist">
      <button
        type="button"
        role="tab"
        class="mode-tab"
        :class="{ on: mode === 'browse' }"
        :aria-selected="mode === 'browse'"
        @click="setMode('browse')"
      >
        <strong>浏览选品</strong>
        <span>搜索 / 品类 / 换一批</span>
      </button>
      <button
        type="button"
        role="tab"
        class="mode-tab"
        :class="{ on: mode === 'campaign' }"
        :aria-selected="mode === 'campaign'"
        @click="setMode('campaign')"
      >
        <strong>活动选品</strong>
        <span>主题匹配 · 营销角度</span>
      </button>
    </nav>

    <!-- 浏览选品 -->
    <template v-if="mode === 'browse'">
      <section class="toolbar sketch-card">
        <el-input
          v-model="query"
          size="large"
          clearable
          placeholder="搜索商品名 / 品牌 / ASIN / 卖点…"
          @keyup.enter="runSearch"
          @clear="runSearch"
        >
          <template #append>
            <el-button :loading="loading" @click="runSearch">搜索</el-button>
          </template>
        </el-input>
        <div class="toolbar-filters">
          <el-switch v-model="onlyImage" active-text="仅看有主图" @change="runSearch" />
          <el-button text type="primary" @click="shuffleBrowse" :loading="loading">换一批</el-button>
        </div>
        <div class="chips" v-if="categories.length">
          <button
            type="button"
            class="chip"
            :class="{ on: !productType }"
            @click="selectType('')"
          >全部</button>
          <button
            v-for="c in categories.slice(0, 14)"
            :key="c.product_type"
            type="button"
            class="chip"
            :class="{ on: productType === c.product_type }"
            @click="selectType(c.product_type)"
          >
            {{ c.label }}
            <em>{{ c.count }}</em>
          </button>
        </div>
      </section>

      <section class="recent" v-if="recentItems.length">
        <div class="section-head">
          <h2 class="sketch-title">最近选过</h2>
        </div>
        <div class="recent-row">
          <button
            v-for="p in recentItems"
            :key="'r-' + p.id"
            type="button"
            class="recent-pill sketch-card"
            :class="{ on: selected?.id === p.id }"
            @click="selectProduct(p)"
          >
            <img v-if="p.image_url" :src="p.image_url" alt="" @error="onImgError" />
            <span>{{ p.name }}</span>
          </button>
        </div>
      </section>

      <section class="results">
        <div class="section-head">
          <h2 class="sketch-title">{{ sectionTitle }}</h2>
          <p v-if="query || productType">共 {{ items.length }} 条结果</p>
        </div>

        <div v-if="loading" class="grid">
          <div v-for="n in 8" :key="'sk-' + n" class="card sketch-card skeleton">
            <div class="thumb" />
            <div class="body">
              <div class="sk-line" />
              <div class="sk-line short" />
            </div>
          </div>
        </div>

        <el-empty v-else-if="!items.length" description="没有匹配商品，换个关键词或品类试试" />

        <div v-else class="grid">
          <article
            v-for="(p, idx) in items"
            :key="p.id"
            class="card sketch-card"
            :class="{ selected: selected?.id === p.id }"
            :style="{ animationDelay: `${Math.min(idx, 12) * 35}ms` }"
            @click="selectProduct(p)"
          >
            <div class="thumb" :style="thumbTone(p)">
              <img v-if="p.image_url" :src="p.image_url" :alt="p.name" loading="lazy" @error="onImgError" />
              <span v-else class="fallback">{{ (p.name || '?').slice(0, 1).toUpperCase() }}</span>
            </div>
            <div class="body">
              <h3 class="title">{{ p.name }}</h3>
              <div class="meta">
                <span class="brand">{{ p.brand || '独立品牌' }}</span>
                <span class="type">{{ p.category }}</span>
              </div>
              <ul v-if="p.feature_list?.length" class="feats">
                <li v-for="(f, i) in p.feature_list.slice(0, 2)" :key="i">{{ f }}</li>
              </ul>
              <div class="card-actions" @click.stop>
                <el-button size="small" class="sketch-btn" @click="selectProduct(p); goWriting()">写文案</el-button>
                <el-button
                  size="small"
                  type="primary"
                  class="sketch-btn sketch-btn-primary"
                  :loading="preparingPoster && selected?.id === p.id"
                  @click="selectProduct(p); goPoster()"
                >做海报</el-button>
                <el-button
                  size="small"
                  text
                  class="similar-btn"
                  :loading="similarLoading && similarSourceId === p.id"
                  @click="selectProduct(p); loadSimilar(p)"
                >相似款</el-button>
              </div>
            </div>
          </article>
        </div>
      </section>
    </template>

    <!-- 活动选品 -->
    <template v-else>
      <section class="campaign sketch-card">
        <div class="campaign-head">
          <div>
            <p class="eyebrow">Campaign Assistant</p>
            <h2 class="sketch-title">活动选品助手</h2>
            <p class="campaign-lead">
              选定活动主题与目标市场，系统从 ABO 货盘打分推荐，并给出营销角度与海报氛围建议。
            </p>
          </div>
          <div class="campaign-controls">
            <el-select v-model="campaignMarket" style="width: 140px" @change="onMarketChange">
              <el-option label="中国站 / 中文" value="cn" />
              <el-option label="美国 / English" value="us" />
              <el-option label="日本 / 日本語" value="jp" />
              <el-option label="韩国 / 한국어" value="kr" />
              <el-option label="西班牙 / Español" value="es" />
            </el-select>
            <el-button
              class="sketch-btn sketch-btn-primary"
              :loading="campaignLoading"
              @click="runCampaign"
            >生成选品方案</el-button>
          </div>
        </div>

        <div class="campaign-presets">
          <button
            v-for="c in campaigns"
            :key="c.id"
            type="button"
            class="preset"
            :class="{ on: campaignId === c.id }"
            @click="pickCampaign(c.id)"
          >
            <strong>{{ c.name }}</strong>
            <span>{{ c.tagline }}</span>
          </button>
          <button
            type="button"
            class="preset"
            :class="{ on: campaignId === 'custom' }"
            @click="pickCampaign('custom')"
          >
            <strong>自定义主题</strong>
            <span>输入你的活动名，即时匹配</span>
          </button>
        </div>

        <div class="campaign-kw">
          <label class="kw-label" for="campaign-kw-input">
            {{ campaignId === 'custom' ? '自定义活动主题' : '补充关键词（可选）' }}
          </label>
          <el-input
            id="campaign-kw-input"
            v-model="campaignTheme"
            clearable
            :placeholder="campaignId === 'custom'
              ? '必填：如「毕业季送礼」「露营好物」'
              : '例：轻便、降噪（会自动匹配英文货盘词）'"
            @keyup.enter="runCampaign"
          />
          <p class="campaign-hint">
            <template v-if="campaignId === 'custom'">
              填写活动名后点「生成选品方案」，或回车提交。
            </template>
            <template v-else>
              补充词只作用于<strong>当前已选活动</strong>，不是全局搜索；中文会自动扩展英文同义词。
            </template>
          </p>
          <div v-if="campaignId !== 'custom'" class="kw-chips">
            <button
              v-for="kw in SUPPLEMENT_CHIPS"
              :key="kw"
              type="button"
              class="chip"
              :class="{ on: keywordActive(kw) }"
              @click="toggleSupplement(kw)"
            >{{ kw }}</button>
          </div>
          <p v-if="expandedHint" class="expand-hint">已扩展检索: {{ expandedHint }}</p>
        </div>

        <div v-if="campaignBrief" class="campaign-brief">
          <div class="brief-main">
            <h3>{{ campaignBrief.name }}</h3>
            <p>{{ campaignBrief.tagline }}</p>
            <ul>
              <li><b>人群</b> {{ campaignBrief.audience }}</li>
              <li><b>档期</b> {{ campaignBrief.season }}</li>
              <li><b>语气</b> {{ styleLabel(campaignBrief.style) }} · {{ campaignBrief.language }}</li>
              <li><b>海报</b> {{ campaignBrief.poster_mood }}</li>
            </ul>
            <div class="brief-hooks">
              <span v-for="h in campaignBrief.hooks" :key="h">{{ h }}</span>
            </div>
          </div>
          <div class="brief-side">
            <p class="aside-label">执行清单</p>
            <ol>
              <li v-for="(t, i) in campaignBrief.checklist" :key="i">{{ t }}</li>
            </ol>
            <p class="brief-meta">扫描货盘 {{ campaignBrief.pool_scanned }} · 产出 {{ campaignBrief.matched }} 条方案</p>
            <div class="brief-platforms">
              <em v-for="p in campaignBrief.platforms" :key="p">{{ p }}</em>
            </div>
          </div>
        </div>

        <div v-if="campaignLoading" class="campaign-results loading">
          <div v-for="n in 4" :key="'ck-' + n" class="rec sketch-card skeleton">
            <div class="sk-line" />
            <div class="sk-line short" />
          </div>
        </div>

        <el-empty
          v-else-if="!campaignItems.length && campaignTried"
          description="这轮没有匹配到合适货盘，换个主题或补充关键词再试"
        />

        <div v-else-if="campaignItems.length" class="campaign-results">
          <article
            v-for="(rec, idx) in campaignItems"
            :key="rec.product.id"
            class="rec sketch-card"
            :class="{ selected: selected?.id === rec.product.id }"
            :style="{ animationDelay: `${Math.min(idx, 10) * 40}ms` }"
            @click="selectCampaignItem(rec)"
          >
            <div class="rec-top">
              <div class="rec-thumb">
                <img
                  v-if="rec.product.image_url"
                  :src="rec.product.image_url"
                  :alt="rec.product.name"
                  @error="onImgError"
                />
                <span v-else>{{ (rec.product.name || '?').slice(0, 1) }}</span>
              </div>
              <div class="score" :data-level="rec.fit_level">
                <strong>{{ rec.score }}</strong>
                <span>{{ rec.fit_level }}</span>
              </div>
            </div>
            <h3 class="title">{{ rec.product.name }}</h3>
            <div class="meta">
              <span class="brand">{{ rec.product.brand || '独立品牌' }}</span>
              <span class="type">{{ rec.product.category }}</span>
            </div>
            <p class="angle">{{ rec.angle }}</p>
            <ul class="reasons">
              <li v-for="(r, i) in rec.reasons" :key="i">{{ r }}</li>
            </ul>
            <div class="rec-tags">
              <span>{{ styleLabel(rec.style) }}</span>
              <span>{{ rec.language }}</span>
              <span v-for="p in rec.platforms.slice(0, 2)" :key="p">{{ p }}</span>
            </div>
            <div class="card-actions" @click.stop>
              <el-button size="small" class="sketch-btn" @click="selectCampaignItem(rec)">选中</el-button>
              <el-button
                size="small"
                text
                class="similar-btn"
                :loading="similarLoading && similarSourceId === rec.product.id"
                @click="selectCampaignItem(rec); loadSimilar(rec.product)"
              >相似款</el-button>
              <el-button size="small" class="sketch-btn" @click="goCampaignWriting(rec)">写文案</el-button>
              <el-button
                size="small"
                type="primary"
                class="sketch-btn sketch-btn-primary"
                :loading="preparingPoster && selected?.id === rec.product.id"
                @click="goCampaignPoster(rec)"
              >做海报</el-button>
            </div>
          </article>
        </div>
      </section>
    </template>

    <!-- 同款延伸 -->
    <section
      v-if="similarTried || similarLoading"
      id="similar-strip"
      class="similar-section"
    >
      <div class="section-head">
        <h2 class="sketch-title">同款延伸</h2>
        <p v-if="selected">基于「{{ selected.name }}」</p>
      </div>

      <div v-if="similarLoading" class="grid">
        <div v-for="n in 6" :key="'sim-sk-' + n" class="card sketch-card skeleton">
          <div class="thumb" />
          <div class="body">
            <div class="sk-line" />
            <div class="sk-line short" />
          </div>
        </div>
      </div>

      <el-empty
        v-else-if="!similarItems.length"
        :description="similarError || '暂无相似款，换一件商品再试'"
      />

      <div v-else class="grid">
        <article
          v-for="(p, idx) in similarItems"
          :key="'sim-' + p.id"
          class="card sketch-card"
          :class="{ selected: selected?.id === p.id }"
          :style="{ animationDelay: `${Math.min(idx, 10) * 35}ms` }"
          @click="selectProduct(p)"
        >
          <div class="thumb" :style="thumbTone(p)">
            <img v-if="p.image_url" :src="p.image_url" :alt="p.name" loading="lazy" @error="onImgError" />
            <span v-else class="fallback">{{ (p.name || '?').slice(0, 1).toUpperCase() }}</span>
          </div>
          <div class="body">
            <h3 class="title">{{ p.name }}</h3>
            <div class="meta">
              <span class="brand">{{ p.brand || '独立品牌' }}</span>
              <span class="type">{{ p.category }}</span>
            </div>
            <div class="card-actions" @click.stop>
              <el-button size="small" class="sketch-btn" @click="selectProduct(p)">选中</el-button>
              <el-button size="small" class="sketch-btn" @click="selectProduct(p); goWriting()">写文案</el-button>
              <el-button
                size="small"
                type="primary"
                class="sketch-btn sketch-btn-primary"
                :loading="preparingPoster && selected?.id === p.id"
                @click="selectProduct(p); goPoster()"
              >做海报</el-button>
            </div>
          </div>
        </article>
      </div>
    </section>

    <!-- 粘性已选栏 -->
    <Transition name="select-bar">
      <div v-if="selected" class="select-bar sketch-card" role="status">
        <div class="select-bar-thumb">
          <img v-if="selected.image_url" :src="selected.image_url" :alt="selected.name" @error="onImgError" />
          <span v-else>{{ (selected.name || '?').slice(0, 1) }}</span>
        </div>
        <div class="select-bar-copy">
          <p class="aside-label">当前已选</p>
          <strong>{{ selected.name }}</strong>
          <span>{{ selected.brand || '未知名牌' }} · {{ selected.category }}</span>
        </div>
        <div class="select-bar-actions">
          <el-button
            class="sketch-btn similar-btn"
            :loading="similarLoading"
            @click="loadSimilar(selected)"
          >相似款</el-button>
          <el-button class="sketch-btn sketch-btn-primary" type="primary" @click="goWorkflow" :loading="preparingPoster">
            进入文案·海报工作流
          </el-button>
          <el-button class="sketch-btn" @click="goWriting">仅写文案</el-button>
          <el-button class="sketch-btn" plain @click="goPoster" :loading="preparingPoster">仅做海报</el-button>
          <el-button text type="info" @click="clearSelected">清除</el-button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { searchWritingProducts, listProductCategories, getPosterCopy, listCampaigns, recommendCampaign, getSimilarProducts } from '@/api/writing'
import { useAppStore } from '@/store/useAppStore'

const RECENT_KEY = 'catalog_recent_v1'
const TONES = ['#2f6f6a', '#c45c26', '#4a6fa5', '#b7791f', '#3d7a52']
const STYLE_LABELS = {
  professional: '专业商务',
  casual: '活泼种草',
  minimalist: '极简高级',
  emotional: '情感共鸣',
  humorous: '幽默风趣',
  luxury: '奢华高端',
}
const SUPPLEMENT_CHIPS = ['轻便', '降噪', '送礼', '宿舍', '防水', '无线', '运动', '高颜值', '耐用', '收纳']

const router = useRouter()
const appStore = useAppStore()

const mode = ref('browse')
const query = ref('')
const productType = ref('')
const onlyImage = ref(true)
const loading = ref(false)
const preparingPoster = ref(false)
const items = ref([])
const categories = ref([])
const catalogTotal = ref(null)
const selected = ref(null)
const recentItems = ref([])
const similarItems = ref([])
const similarLoading = ref(false)
const similarTried = ref(false)
const similarSourceId = ref(null)
const similarError = ref('')

const campaigns = ref([])
const campaignId = ref('back_to_school')
const campaignTheme = ref('')
const campaignMarket = ref('cn')
const campaignLoading = ref(false)
const campaignBrief = ref(null)
const campaignItems = ref([])
const campaignTried = ref(false)
const campaignBootstrapped = ref(false)

const sectionTitle = computed(() => {
  if (query.value.trim()) return `搜索「${query.value.trim()}」`
  if (productType.value) {
    const hit = categories.value.find((c) => c.product_type === productType.value)
    return hit ? hit.label : '品类浏览'
  }
  return '精选浏览'
})

const expandedHint = computed(() => {
  const brief = campaignBrief.value
  if (!brief) return ''
  const expanded = brief.expanded_keywords
  const supplements = brief.supplement_keywords
  if (Array.isArray(expanded) && expanded.length) {
    return expanded.slice(0, 10).join(' · ')
  }
  if (Array.isArray(supplements) && supplements.length) {
    return supplements.join(' · ')
  }
  return ''
})

function styleLabel(style) {
  return STYLE_LABELS[style] || style || '种草'
}

function thumbTone(p) {
  const seed = String(p.item_id || p.id || '')
  let h = 0
  for (let i = 0; i < seed.length; i++) h = (h + seed.charCodeAt(i) * (i + 1)) % TONES.length
  return { '--tone': TONES[h] }
}

function onImgError(e) {
  const img = e?.target
  if (img) img.style.display = 'none'
}

function loadRecent() {
  try {
    const raw = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
    recentItems.value = Array.isArray(raw) ? raw.slice(0, 8) : []
  } catch {
    recentItems.value = []
  }
}

function remember(p) {
  const next = [p, ...recentItems.value.filter((x) => x.id !== p.id)].slice(0, 8)
  recentItems.value = next
  localStorage.setItem(RECENT_KEY, JSON.stringify(next))
}

function selectProduct(p) {
  selected.value = p
  appStore.setSelectedProduct(p)
  appStore.setCampaignHint(null)
  remember(p)
}

function clearSelected() {
  selected.value = null
  appStore.setSelectedProduct(null)
  appStore.setCampaignHint(null)
  similarItems.value = []
  similarTried.value = false
  similarSourceId.value = null
  similarError.value = ''
}

function similarFailMessage(err) {
  const data = err?.response?.data
  if (typeof data?.detail === 'string' && data.detail) return data.detail
  if (Array.isArray(data?.detail) && data.detail.length) {
    return data.detail.map((d) => d.msg || d).join('；')
  }
  if (typeof data?.message === 'string' && data.message) return data.message
  if (err?.message && !String(err.message).startsWith('Request failed')) return err.message
  const status = err?.response?.status
  if (status === 404) return '相似款接口未找到（需重启后端加载最新路由）'
  if (status === 401) return '登录已失效，请重新登录'
  if (status >= 500) return '服务器错误，请稍后重试'
  return '相似款加载失败'
}

async function loadSimilar(p) {
  const target = p || selected.value
  const productId = target?.id ?? target?.product_id
  if (!productId) {
    ElMessage.warning('请先选择一件商品')
    return
  }
  similarLoading.value = true
  similarTried.value = true
  similarError.value = ''
  similarSourceId.value = productId
  try {
    const data = await getSimilarProducts(productId, 8)
    similarItems.value = data.items || []
    if (!similarItems.value.length) {
      ElMessage.info('暂无相似款')
    } else {
      requestAnimationFrame(() => {
        document.getElementById('similar-strip')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    }
  } catch (err) {
    similarItems.value = []
    const brief = similarFailMessage(err).slice(0, 100)
    similarError.value = brief
    // request 拦截器已 toast HTTP/业务错误；此处补一句场景提示，404 时最有用
    if (err?.response?.status === 404 || !err?.response) {
      ElMessage.error(brief)
    }
  } finally {
    similarLoading.value = false
  }
}

function setMode(next) {
  mode.value = next
  if (next === 'campaign' && !campaignBootstrapped.value) {
    campaignBootstrapped.value = true
    runCampaign()
  }
}

async function runSearch() {
  loading.value = true
  try {
    const data = await searchWritingProducts(query.value.trim(), 24, onlyImage.value, {
      diverse: !query.value.trim() && !productType.value,
      product_type: productType.value,
    })
    items.value = data.items || []
    if (data.catalog_total != null) catalogTotal.value = data.catalog_total
    if (selected.value) {
      const still = items.value.find((x) => x.id === selected.value.id)
      if (still) selected.value = still
    }
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

function shuffleBrowse() {
  query.value = ''
  runSearch()
}

function selectType(pt) {
  productType.value = pt
  runSearch()
}

function goWriting() {
  if (!selected.value) {
    ElMessage.warning('请先选择一件商品')
    return
  }
  appStore.setSelectedProduct(selected.value)
  router.push('/writing')
}

/** 选品后进入：文案（可跳过）→ 海报生成（可跳过） */
async function goWorkflow() {
  if (!selected.value) {
    ElMessage.warning('请先选择一件商品')
    return
  }
  preparingPoster.value = true
  try {
    const hint = appStore.campaignHint
    const lang = hint?.language === 'zh' || !hint?.language ? 'zh' : hint.language
    const data = await getPosterCopy(selected.value.id, lang === 'zh' ? 'zh' : 'en', false)
    const base = data.poster_copy || null
    const copy = hint
      ? {
          ...(base || {}),
          title: hint.poster_hook || base?.title,
          cta_text: hint.cta || base?.cta_text,
          subtitle: hint.angle || base?.subtitle,
        }
      : base
    appStore.setSelectedProduct(data.product || selected.value, copy)
  } catch {
    appStore.setSelectedProduct(selected.value)
  } finally {
    preparingPoster.value = false
  }
  sessionStorage.removeItem('workflow_writing_done')
  sessionStorage.removeItem('workflow_writing_result')
  ElMessage.success('已选品，进入文案·海报工作流')
  router.push({ path: '/writing-poster' })
}

async function goPoster() {
  if (!selected.value) {
    ElMessage.warning('请先选择一件商品')
    return
  }
  preparingPoster.value = true
  try {
    const hint = appStore.campaignHint
    const lang = hint?.language === 'zh' || !hint?.language ? 'zh' : hint.language
    const data = await getPosterCopy(selected.value.id, lang === 'zh' ? 'zh' : 'en', false)
    const base = data.poster_copy || null
    const copy = hint
      ? {
          ...(base || {}),
          title: hint.poster_hook || base?.title,
          cta_text: hint.cta || base?.cta_text,
          subtitle: hint.angle || base?.subtitle,
        }
      : base
    appStore.setSelectedProduct(data.product || selected.value, copy)
    ElMessage.success(hint ? '已按活动方案带入，跳过文案直达海报' : '已带入商品，跳过文案直达海报')
    router.push({ path: '/writing-poster', query: { skipWriting: '1' } })
  } catch {
    const hint = appStore.campaignHint
    appStore.setSelectedProduct(
      selected.value,
      hint
        ? { title: hint.poster_hook, subtitle: hint.angle, cta_text: hint.cta }
        : null,
    )
    router.push({ path: '/writing-poster', query: { skipWriting: '1' } })
  } finally {
    preparingPoster.value = false
  }
}

function parseThemeTokens() {
  return campaignTheme.value
    .split(/[,，、\s]+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

function keywordActive(kw) {
  return parseThemeTokens().includes(kw)
}

function toggleSupplement(kw) {
  const tokens = parseThemeTokens()
  if (tokens.includes(kw)) {
    campaignTheme.value = tokens.filter((t) => t !== kw).join('、')
  } else {
    campaignTheme.value = [...tokens, kw].join('、')
  }
}

function pickCampaign(id) {
  campaignId.value = id
  if (id === 'custom') {
    campaignBrief.value = null
    campaignItems.value = []
    campaignTried.value = false
    return
  }
  runCampaign()
}

async function onMarketChange() {
  if (campaignId.value === 'custom' && !campaignTheme.value.trim()) return
  await runCampaign()
}

function applyCampaignHint(rec) {
  appStore.setCampaignHint({
    campaign_id: campaignBrief.value?.campaign_id,
    campaign_name: campaignBrief.value?.name,
    angle: rec.angle,
    platforms: rec.platforms,
    language: rec.language,
    style: rec.style,
    poster_hook: rec.poster_hook,
    cta: rec.cta,
    poster_mood: rec.poster_mood,
  })
}

function selectCampaignItem(rec) {
  selectProduct(rec.product)
  applyCampaignHint(rec)
}

async function runCampaign() {
  if (campaignId.value === 'custom' && !campaignTheme.value.trim()) {
    ElMessage.warning('自定义主题请先填写活动名称或关键词')
    return
  }
  campaignLoading.value = true
  campaignTried.value = true
  try {
    const data = await recommendCampaign({
      campaign_id: campaignId.value,
      theme: campaignTheme.value.trim(),
      market: campaignMarket.value,
      limit: 8,
    })
    campaignBrief.value = data.brief || null
    campaignItems.value = data.items || []
    if (!campaignItems.value.length) {
      ElMessage.warning('这轮没有匹配到合适货盘，换个主题或关键词再试')
    } else {
      ElMessage.success(`已生成 ${campaignItems.value.length} 条活动选品方案`)
    }
  } catch {
    campaignBrief.value = null
    campaignItems.value = []
    ElMessage.error('活动方案生成失败，请确认后端已重启')
  } finally {
    campaignLoading.value = false
  }
}

async function loadCampaigns() {
  try {
    const data = await listCampaigns()
    campaigns.value = data.items || []
  } catch {
    campaigns.value = []
  }
}

async function loadCategories() {
  try {
    const data = await listProductCategories()
    categories.value = data.items || []
  } catch {
    categories.value = []
  }
}

onMounted(async () => {
  loadRecent()
  if (appStore.selectedProduct) {
    selected.value = appStore.selectedProduct
  }
  await Promise.all([loadCategories(), loadCampaigns(), runSearch()])
})
</script>

<style scoped>
.catalog-page {
  display: grid;
  gap: 14px;
  padding-bottom: 28px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  overflow-x: clip;
}
.catalog-page.has-select-bar {
  padding-bottom: 96px;
}
.catalog-page > * {
  min-width: 0;
  max-width: 100%;
}

.hero {
  padding: 22px 24px;
  background:
    linear-gradient(145deg, rgba(255,255,255,0.88), rgba(215,232,223,0.55));
}
.eyebrow {
  margin: 0 0 8px;
  color: var(--accent);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-size: 12px;
  font-weight: 600;
}
.sketch-title {
  margin: 0 0 8px;
  font-size: clamp(1.65rem, 3vw, 2.25rem);
}
.lead {
  margin: 0;
  max-width: 640px;
  line-height: 1.7;
  color: var(--ink-soft);
  font-size: 14px;
}
.stat-row {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.stat {
  min-width: 88px;
  padding: 8px 12px;
  border: 1.5px solid rgba(44, 58, 66, 0.18);
  border-radius: 14px;
  background: rgba(255,255,255,0.65);
}
.stat strong {
  display: block;
  font-family: var(--font-display);
  font-size: 1.3rem;
  color: var(--accent);
}
.stat span {
  font-size: 12px;
  color: var(--ink-soft);
}

.mode-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding: 10px;
}
.mode-tab {
  text-align: left;
  border: 1.5px solid rgba(44, 58, 66, 0.16);
  background: rgba(255,255,255,0.7);
  border-radius: 14px;
  padding: 12px 14px;
  cursor: pointer;
  display: grid;
  gap: 2px;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}
.mode-tab strong {
  font-size: 15px;
  color: var(--ink);
}
.mode-tab span {
  font-size: 12px;
  color: var(--ink-soft);
}
.mode-tab.on {
  border-color: var(--accent);
  background: rgba(47, 111, 106, 0.1);
  box-shadow: 2px 3px 0 rgba(47, 111, 106, 0.12);
}
.mode-tab:hover:not(.on) {
  border-color: rgba(47, 111, 106, 0.35);
}

.aside-label {
  margin: 0;
  font-size: 11px;
  letter-spacing: 0.08em;
  color: var(--accent);
  text-transform: uppercase;
}

.campaign {
  padding: 20px 22px;
  display: grid;
  gap: 14px;
  background:
    linear-gradient(160deg, rgba(255,255,255,0.9), rgba(232, 242, 236, 0.7));
}
.campaign-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
  flex-wrap: wrap;
}
.campaign-lead {
  margin: 0;
  max-width: 560px;
  color: var(--ink-soft);
  line-height: 1.65;
  font-size: 14px;
}
.campaign-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.campaign-presets {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 150px), 1fr));
  gap: 10px;
  width: 100%;
  min-width: 0;
}
.preset {
  text-align: left;
  border: 1.5px solid rgba(44, 58, 66, 0.18);
  background: rgba(255,255,255,0.75);
  border-radius: 14px;
  padding: 11px 12px;
  cursor: pointer;
  display: grid;
  gap: 4px;
  min-width: 0;
}
.preset strong {
  font-size: 13px;
  color: var(--ink);
  overflow-wrap: anywhere;
}
.preset span {
  font-size: 12px;
  color: var(--ink-soft);
  line-height: 1.4;
  overflow-wrap: anywhere;
}
.preset.on {
  border-color: var(--accent);
  background: rgba(47, 111, 106, 0.1);
  box-shadow: 2px 3px 0 rgba(47, 111, 106, 0.12);
}

.campaign-kw {
  display: grid;
  gap: 8px;
}
.kw-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
}
.campaign-hint {
  margin: 0;
  font-size: 12px;
  color: var(--ink-soft);
  line-height: 1.5;
}
.kw-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.expand-hint {
  margin: 0;
  font-size: 12px;
  color: var(--accent);
  line-height: 1.45;
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(47, 111, 106, 0.08);
  overflow-wrap: anywhere;
}

.campaign-brief {
  display: grid;
  grid-template-columns: 1.4fr 0.9fr;
  gap: 14px;
  padding: 14px 16px;
  border: 1.5px dashed rgba(47, 111, 106, 0.35);
  border-radius: 16px;
  background: rgba(255,255,255,0.55);
}
.brief-main h3 {
  margin: 0 0 4px;
  font-size: 1.1rem;
}
.brief-main > p {
  margin: 0 0 10px;
  color: var(--ink-soft);
  font-size: 14px;
}
.brief-main ul {
  margin: 0;
  padding-left: 0;
  list-style: none;
  display: grid;
  gap: 4px;
  font-size: 13px;
  color: var(--ink-soft);
}
.brief-main b { color: var(--ink); margin-right: 6px; }
.brief-hooks {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.brief-hooks span {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(196, 92, 38, 0.1);
  color: #9a4a1f;
}
.brief-side ol {
  margin: 6px 0 10px;
  padding-left: 18px;
  color: var(--ink-soft);
  font-size: 13px;
  line-height: 1.55;
}
.brief-meta {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--ink-soft);
}
.brief-platforms {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.brief-platforms em {
  font-style: normal;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(44,58,66,0.18);
  background: #fff;
}

.campaign-results {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 220px), 1fr));
  gap: 12px;
  width: 100%;
  min-width: 0;
}
.campaign-results.loading .rec {
  min-height: 160px;
  padding: 16px;
}
.rec {
  padding: 12px 14px 14px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  animation: rise 0.45s ease both;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.rec:hover {
  transform: translate(-2px, -2px);
  box-shadow: 5px 6px 0 rgba(36, 48, 56, 0.14);
}
.rec.selected {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}
.rec-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
  margin-bottom: 10px;
}
.rec-thumb {
  width: 72px;
  height: 72px;
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(145deg, #2f6f6a, #1b4542);
  display: grid;
  place-items: center;
  flex: 0 0 auto;
}
.rec-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.rec-thumb span {
  color: #fff;
  font-family: var(--font-display);
  font-size: 28px;
}
.score {
  text-align: right;
  min-width: 64px;
}
.score strong {
  display: block;
  font-family: var(--font-display);
  font-size: 1.55rem;
  line-height: 1;
  color: var(--accent);
}
.score span {
  font-size: 12px;
  color: var(--ink-soft);
}
.score[data-level="高匹配"] strong { color: #2f6f6a; }
.score[data-level="可主推"] strong { color: #b7791f; }
.score[data-level="备选"] strong { color: #6a7a84; }
.rec .title {
  margin: 0;
  font-size: 14px;
  line-height: 1.4;
  font-weight: 600;
  max-height: calc(1.4em * 2);
  overflow: hidden;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.rec .meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
  min-width: 0;
  width: 100%;
}
.rec .brand {
  flex: 1 1 0;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: var(--ink-soft);
}
.rec .type {
  flex: 0 0 auto;
  max-width: 45%;
  font-size: 12px;
  line-height: 1.2;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(47, 111, 106, 0.1);
  color: #2f6f6a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.angle {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.45;
  color: #9a4a1f;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.reasons {
  margin: 8px 0 0;
  padding-left: 16px;
  color: var(--ink-soft);
  font-size: 12px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
.rec-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}
.rec-tags span {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(44,58,66,0.06);
  color: var(--ink-soft);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rec .card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: auto;
  padding-top: 12px;
  width: 100%;
}
.rec .card-actions :deep(.el-button) {
  margin: 0;
}
.rec .card-actions :deep(.similar-btn.el-button) {
  margin-left: -4px;
  padding-left: 4px;
  padding-right: 8px;
}

.toolbar {
  padding: 14px 16px;
  display: grid;
  gap: 12px;
}
.toolbar-filters {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  border: 1.5px solid rgba(44, 58, 66, 0.2);
  background: #fff;
  border-radius: 999px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 13px;
  color: var(--ink);
}
.chip em {
  margin-left: 6px;
  font-style: normal;
  color: var(--ink-soft);
  font-size: 12px;
}
.chip.on {
  background: rgba(47, 111, 106, 0.12);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.section-head .sketch-title {
  margin: 0;
  font-size: 1.2rem;
}
.section-head p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 13px;
}

.similar-btn,
.similar-btn.is-text,
.similar-btn.el-button,
.similar-btn:deep(span) {
  color: #2f6f6a !important;
}
.similar-btn.el-button.is-text {
  /* text 按钮默认左右 padding 偏大，文字看起来往右飘 */
  padding-left: 4px !important;
  padding-right: 8px !important;
  margin-left: -2px;
}
.similar-btn:hover,
.similar-btn.is-text:hover,
.similar-btn.el-button:hover,
.similar-btn:hover:deep(span),
.similar-btn:focus,
.similar-btn:focus:deep(span) {
  color: #1b4542 !important;
}

.similar-section {
  display: grid;
  gap: 0;
  min-width: 0;
  max-width: 100%;
}
.similar-section .section-head {
  margin-bottom: 12px;
}

.recent-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding-bottom: 4px;
}
.recent-pill {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 8px 8px;
  cursor: pointer;
  border: 1.5px solid rgba(44, 58, 66, 0.18);
  background: rgba(255,255,255,0.7);
  max-width: 100%;
}
.recent-pill img {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  object-fit: cover;
  flex: 0 0 auto;
}
.recent-pill span {
  max-width: 160px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
}
.recent-pill.on {
  border-color: var(--accent);
  box-shadow: 2px 3px 0 rgba(47, 111, 106, 0.18);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 200px), 1fr));
  gap: 14px;
  width: 100%;
  min-width: 0;
}
.card {
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  min-width: 0;
  max-width: 100%;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  animation: rise 0.45s ease both;
}
.card:hover {
  transform: translate(-2px, -2px);
  box-shadow: 5px 6px 0 rgba(36, 48, 56, 0.14);
}
.card.selected {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}
.thumb {
  height: 132px;
  flex: 0 0 auto;
  background: linear-gradient(145deg, var(--tone, #2f6f6a), rgba(255,255,255,0.28));
  position: relative;
  display: grid;
  place-items: center;
  overflow: hidden;
}
.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.fallback {
  color: #fff;
  font-size: 42px;
  font-family: var(--font-display);
}
.body {
  padding: 12px 14px 14px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0;
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
}
.title {
  margin: 0;
  width: 100%;
  font-size: 14px;
  line-height: 1.45;
  font-weight: 600;
  max-height: calc(1.45em * 2);
  overflow: hidden;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.meta {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
  margin-top: 8px;
}
.brand {
  margin: 0;
  flex: 1 1 0;
  min-width: 0;
  font-size: 12px;
  line-height: 1.3;
  color: var(--ink-soft);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.type {
  margin: 0;
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  max-width: 42%;
  font-size: 12px;
  line-height: 1.2;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(47, 111, 106, 0.1);
  color: #2f6f6a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.feats {
  margin: 8px 0 0;
  padding-left: 16px;
  width: 100%;
  color: var(--ink-soft);
  font-size: 12px;
  line-height: 1.45;
  max-height: calc(1.45em * 2);
  overflow: hidden;
}
.feats li { margin: 0; }
.card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: auto;
  padding-top: 10px;
  width: 100%;
}
.card-actions :deep(.el-button) {
  margin: 0;
}
.card-actions :deep(.similar-btn.el-button) {
  margin-left: -4px;
  padding-left: 4px;
  padding-right: 8px;
}

.select-bar {
  position: fixed;
  z-index: 40;
  left: max(246px, calc((100vw - 1100px) / 2 + 246px));
  right: 24px;
  bottom: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.94);
  border: 2px solid rgba(47, 111, 106, 0.28);
  box-shadow: 4px 6px 0 rgba(36, 48, 56, 0.12);
  backdrop-filter: blur(8px);
  max-width: 920px;
  margin-inline: auto;
}
.select-bar-thumb {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  overflow: hidden;
  flex: 0 0 auto;
  background: linear-gradient(145deg, #2f6f6a, #1b4542);
  display: grid;
  place-items: center;
}
.select-bar-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.select-bar-thumb span {
  color: #fff;
  font-family: var(--font-display);
  font-size: 20px;
}
.select-bar-copy {
  flex: 1 1 auto;
  min-width: 0;
  display: grid;
  gap: 2px;
}
.select-bar-copy strong {
  font-size: 14px;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.select-bar-copy > span {
  font-size: 12px;
  color: var(--ink-soft);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.select-bar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  flex: 0 0 auto;
  justify-content: flex-end;
}
.select-bar-actions :deep(.el-button) {
  margin: 0;
}
.select-bar-actions :deep(.similar-btn.el-button) {
  margin-left: -2px;
  padding-left: 10px;
  padding-right: 12px;
}
.select-bar-enter-active,
.select-bar-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.select-bar-enter-from,
.select-bar-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

.skeleton .thumb { background: rgba(44,58,66,0.08); }
.sk-line {
  height: 12px;
  border-radius: 6px;
  background: rgba(44,58,66,0.08);
  margin-top: 8px;
}
.sk-line.short { width: 55%; }

@keyframes rise {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 1100px) {
  .select-bar {
    left: 246px;
    right: 16px;
    max-width: none;
  }
}
@media (max-width: 900px) {
  .mode-tabs { grid-template-columns: 1fr; }
  .campaign-brief { grid-template-columns: 1fr; }
  .campaign-results,
  .grid {
    grid-template-columns: 1fr;
  }
  .select-bar {
    left: 12px;
    right: 12px;
    bottom: 12px;
    flex-wrap: wrap;
  }
  .select-bar-actions {
    width: 100%;
  }
}
</style>
