<template>
  <div class="works-page sketch-shell">
    <div class="page-head">
      <div>
        <h1>我的作品</h1>
        <p class="subtitle">文案与海报导出记录集中管理，可互相跳转复用</p>
      </div>
      <div class="head-actions">
        <el-button @click="reload" :loading="loading">刷新</el-button>
        <el-button v-if="mainTab === 'writing'" type="primary" plain @click="$router.push('/writing')">去写文案</el-button>
        <template v-else>
          <el-button plain @click="$router.push('/gallery')">作品广场</el-button>
          <el-button type="primary" plain @click="$router.push('/poster-workflow?step=poster')">去生成海报</el-button>
        </template>
      </div>
    </div>

    <el-tabs v-model="mainTab" @tab-change="onMainTabChange">
      <el-tab-pane label="文案历史" name="writing" />
      <el-tab-pane label="海报作品" name="poster" />
    </el-tabs>

    <!-- ===== 文案 ===== -->
    <div v-show="mainTab === 'writing'">
      <el-empty v-if="!loading && writings.length === 0" description="暂无文案记录，去「文案生成」创作一条吧" />
      <div v-else class="writing-list">
        <el-card v-for="item in writings" :key="item.id" class="writing-card" shadow="hover">
          <div class="writing-top">
            <div>
              <strong class="writing-product">{{ item.product_name }}</strong>
              <div class="tag-row">
                <el-tag size="small" v-if="item.platform">{{ item.platform }}</el-tag>
                <el-tag size="small" type="info" v-if="item.language">{{ item.language }}</el-tag>
                <el-tag size="small" type="success" v-if="item.style">{{ item.style }}</el-tag>
              </div>
            </div>
            <span class="time">{{ item.created_at }}</span>
          </div>
          <h3 class="writing-title">{{ item.title }}</h3>
          <p class="writing-body">{{ item.body }}</p>
          <p v-if="item.tags" class="writing-tags">{{ item.tags }}</p>

          <div v-if="relatedPosters(item).length" class="related">
            <span class="related-label">相关海报</span>
            <button
              v-for="p in relatedPosters(item).slice(0, 3)"
              :key="posterId(p)"
              type="button"
              class="related-thumb"
              @click="openPreview(p)"
            >
              <img :src="p.poster_url" :alt="p.title" />
            </button>
            <el-button link type="primary" @click="jumpToRelatedPosters(item)">筛选相关</el-button>
          </div>
          <p v-else class="related-none">暂无对应海报（标题特征词未匹配到历史海报）</p>

          <div class="card-actions">
            <el-button size="small" @click="copyWriting(item)">复制全文</el-button>
            <el-button size="small" type="primary" @click="reuseInWriting(item)">重新编辑</el-button>
            <el-button size="small" type="success" @click="useForPoster(item)">用于海报</el-button>
            <el-button size="small" type="danger" plain :loading="deletingWritingId === item.id" @click="removeWriting(item)">
              删除
            </el-button>
          </div>
        </el-card>
      </div>
      <div v-if="writingTotal > writingPageSize" class="pager">
        <el-pagination
          v-model:current-page="writingPage"
          :page-size="writingPageSize"
          :total="writingTotal"
          layout="prev, pager, next"
          @current-change="loadWritings"
        />
      </div>
    </div>

    <!-- ===== 海报 ===== -->
    <div v-show="mainTab === 'poster'">
      <div class="poster-toolbar">
        <el-radio-group v-model="posterMode" size="default" @change="loadPosters">
          <el-radio-button label="final">成稿</el-radio-button>
          <el-radio-button label="base">底图素材</el-radio-button>
          <el-radio-button label="favorites">我的收藏</el-radio-button>
        </el-radio-group>
        <el-input
          v-model="posterFilter"
          clearable
          size="small"
          style="width:240px"
          placeholder="筛选海报标题/卖点关键词"
        />
        <el-button v-if="posterFilter" size="small" @click="clearPosterFilter">清除筛选</el-button>
      </div>

      <el-empty
        v-if="!loading && filteredPosters.length === 0"
        :description="posterEmptyHint"
      >
        <el-button v-if="posters.length && posterFilter" type="primary" @click="clearPosterFilter">
          显示全部海报
        </el-button>
      </el-empty>

      <el-row v-else :gutter="16">
        <el-col v-for="item in filteredPosters" :key="itemKey(item)" :xs="24" :sm="12" :md="8" :lg="6">
          <el-card shadow="hover" class="poster-card" @click="openPreview(item)">
            <div class="thumb-wrap">
              <img v-if="item.poster_url" :src="item.poster_url" :alt="item.title || 'poster'" loading="lazy" />
              <div v-else class="thumb-empty">无预览</div>
            </div>
            <div class="card-body">
              <strong class="card-title">{{ item.title || (item.asset_kind === 'base' || posterMode === 'base' ? '无字底图' : '未命名海报') }}</strong>
              <p class="card-meta">
                {{ item.discount || item.subtitle || '—' }}
                <span v-if="item.price"> · {{ item.price }}</span>
              </p>
              <p class="card-meta faint">
                <template v-if="posterMode === 'favorites' && item.username">
                  @{{ item.username }} ·
                </template>
                <el-tag v-if="item.asset_kind === 'base' || posterMode === 'base'" size="small" type="warning" effect="plain">底图</el-tag>
                下载 {{ item.downloads || 0 }} 次
                <span v-if="item.created_at"> · {{ formatTime(item.created_at) }}</span>
              </p>
              <p v-if="posterMode === 'final'" class="card-meta faint">
                <el-tag size="small" :type="item.is_public ? 'success' : 'info'" effect="plain">
                  {{ item.is_public ? '已发布到广场' : '未发布' }}
                </el-tag>
              </p>
              <div class="card-actions" @click.stop>
                <el-button size="small" @click="openPreview(item)">预览</el-button>
                <a :href="downloadUrl(item)" target="_blank" rel="noopener">
                  <el-button size="small" type="primary">下载</el-button>
                </a>
                <el-button
                  v-if="item.asset_kind === 'base' || posterMode === 'base'"
                  size="small"
                  type="success"
                  @click="useBaseForText(item)"
                >用于加字</el-button>
                <el-button
                  v-if="posterMode === 'final'"
                  size="small"
                  :type="item.is_public ? 'info' : 'success'"
                  plain
                  :loading="publishingId === posterId(item)"
                  @click="togglePublish(item)"
                >
                  {{ item.is_public ? '取消发布' : '发布到广场' }}
                </el-button>
                <el-button size="small" type="warning" @click="toggleFav(item)">
                  {{ posterMode === 'favorites' ? '取消收藏' : '收藏' }}
                </el-button>
                <el-button
                  v-if="posterMode !== 'favorites' || item.is_own"
                  size="small"
                  type="danger"
                  plain
                  :loading="deletingPosterId === posterId(item)"
                  @click="removePoster(item)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-dialog v-model="previewVisible" title="海报预览" width="720px" destroy-on-close>
      <div class="dialog-preview">
        <img v-if="previewItem?.poster_url" :src="previewItem.poster_url" alt="preview" />
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <a v-if="previewItem" :href="downloadUrl(previewItem)" target="_blank" rel="noopener">
          <el-button type="primary">下载原图</el-button>
        </a>
        <el-button
          v-if="previewItem && posterMode === 'final'"
          :type="previewItem.is_public ? 'info' : 'success'"
          plain
          :loading="publishingId === posterId(previewItem)"
          @click="togglePublish(previewItem)"
        >
          {{ previewItem.is_public ? '取消发布' : '发布到广场' }}
        </el-button>
        <el-button
          v-if="previewItem && (previewItem.asset_kind === 'base' || posterMode === 'base')"
          type="success"
          @click="useBaseForText(previewItem)"
        >用于加字</el-button>
        <el-button
          v-if="previewItem && (posterMode !== 'favorites' || previewItem.is_own)"
          type="danger"
          plain
          @click="removePoster(previewItem)"
        >
          删除
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import request from '@/api/request'
import { getWritingHistory, deleteWritingHistory } from '@/api/writing'
import { publishPoster, unpublishPoster, getPosterHistory } from '@/api/poster'
import { useAppStore } from '@/store/useAppStore'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const mainTab = ref(route.query.tab === 'poster' ? 'poster' : 'writing')
const loading = ref(false)

const writings = ref([])
const writingPage = ref(1)
const writingPageSize = 12
const writingTotal = ref(0)
const deletingWritingId = ref(null)

const posters = ref([])
const posterMode = ref('final')
const posterFilter = ref('')
const deletingPosterId = ref(null)
const publishingId = ref(null)
const previewVisible = ref(false)
const previewItem = ref(null)

/** 通用停用词：过短/过泛的词不做关联，避免「Amazon / Brand」乱配 */
const TOKEN_STOP = new Set([
  'amazon', 'brand', 'collective', 'women', 'womens', 'men', 'mens', 'unisex',
  'white', 'black', 'grey', 'gray', 'blue', 'red', 'green', 'brown', 'steel',
  'modern', 'classic', 'new', 'value', 'everyday', 'the', 'and', 'for', 'with',
  'from', 'inch', 'inches', 'cm', 'mm', 'size', 'pack', 'set', 'pcs', 'pair',
  'product', 'item', 'usa', 'us', 'uk', 'eu', 'de', 'of', 'in', 'on', 'by',
  '沙发', '商品', '品牌', '系列',
])

const filteredPosters = computed(() => {
  const q = posterFilter.value.trim().toLowerCase()
  if (!q) return posters.value
  // 支持多关键词：空格分隔，需全部命中（更准）；单段则模糊包含
  const parts = q.split(/\s+/).filter(Boolean)
  return posters.value.filter((p) => {
    const blob = `${p.title || ''} ${p.discount || ''} ${p.price || ''}`.toLowerCase()
    if (parts.length <= 1) return blob.includes(q)
    return parts.every((part) => blob.includes(part))
  })
})

const posterEmptyHint = computed(() => {
  if (posters.value.length && posterFilter.value.trim() && !filteredPosters.value.length) {
    return '没有匹配当前筛选的海报'
  }
  if (posterMode.value === 'favorites') return '暂无收藏海报'
  if (posterMode.value === 'base') return '暂无底图素材，去工作流第3步生成'
  return '暂无成稿记录'
})

function itemKey(item) {
  return item.poster_id || item.id || item.favorite_id || item.poster_url
}
function posterId(item) {
  return item.poster_id || item.id
}
function downloadUrl(item) {
  return `/api/poster/download/${posterId(item)}`
}
function formatTime(s) {
  const t = String(s || '').replace('T', ' ')
  return t.length > 19 ? t.slice(0, 19) : t
}

function significantTokens(text) {
  return String(text || '')
    .toLowerCase()
    .replace(/[()（）\[\]【】«»""'']/g, ' ')
    .split(/[\s,/|·\-_~,，、]+/)
    .map((t) => t.replace(/[^\p{L}\p{N}]/gu, ''))
    .filter((t) => t.length >= 3 && !TOKEN_STOP.has(t) && !/^\d+$/.test(t))
}

function relatedPosters(writing) {
  const wTokens = significantTokens(
    `${writing.product_name || ''} ${writing.title || ''}`,
  )
  if (!wTokens.length) return []

  const scored = posters.value
    .map((p) => {
      const blob = `${p.title || ''} ${p.discount || ''}`.toLowerCase()
      const hits = wTokens.filter((t) => blob.includes(t))
      // 至少 1 个较长特征词，或 2 个普通词同时命中
      const strong = hits.some((h) => h.length >= 5)
      const ok = hits.length >= 2 || (hits.length >= 1 && strong)
      return { p, score: hits.length + (strong ? 1 : 0), ok }
    })
    .filter((x) => x.ok)
    .sort((a, b) => b.score - a.score)

  return scored.map((x) => x.p)
}

function onMainTabChange(name) {
  router.replace({ query: { ...route.query, tab: name } })
  if (name === 'poster') {
    // 切到海报时清掉误带的筛选，并强制刷新列表
    if (posterFilter.value && !filteredPosters.value.length) {
      posterFilter.value = ''
    }
    loadPosters()
  }
  if (name === 'writing' && !writings.value.length) loadWritings()
}

function jumpToRelatedPosters(writing) {
  const related = relatedPosters(writing)
  mainTab.value = 'poster'
  router.replace({ query: { ...route.query, tab: 'poster' } })
  if (!related.length) {
    posterFilter.value = ''
    ElMessage.info('暂无与该文案明确对应的海报，已显示全部海报')
    loadPosters()
    return
  }
  // 用命中的特征词筛选，而不是整段商品名（否则容易滤空）
  const tokens = significantTokens(writing.product_name).filter((t) => t.length >= 4)
  posterFilter.value = tokens.slice(0, 2).join(' ')
  loadPosters()
}

function clearPosterFilter() {
  posterFilter.value = ''
}

function openPreview(item) {
  previewItem.value = item
  previewVisible.value = true
}

async function loadWritings() {
  loading.value = true
  try {
    const data = await getWritingHistory(writingPage.value, writingPageSize)
    writings.value = data?.items || []
    writingTotal.value = data?.total || 0
  } catch (e) {
    ElMessage.error(e?.message || '加载文案失败')
    writings.value = []
  } finally {
    loading.value = false
  }
}

async function loadPosters() {
  loading.value = true
  try {
    if (posterMode.value === 'favorites') {
      posters.value = (await request.get('/poster/favorites')) || []
    } else {
      const kind = posterMode.value === 'base' ? 'base' : 'final'
      const d = await getPosterHistory(1, 60, kind)
      posters.value = d?.items || []
    }
  } catch (e) {
    ElMessage.error(e?.message || '加载海报失败')
    posters.value = []
  } finally {
    loading.value = false
  }
}

async function reload() {
  if (mainTab.value === 'writing') await loadWritings()
  else await loadPosters()
  // 文案页也预加载成稿，便于「相关海报」
  if (mainTab.value === 'writing' && !posters.value.length) {
    try {
      const d = await getPosterHistory(1, 60, 'final')
      posters.value = d?.items || []
    } catch { /* ignore */ }
  }
}

function useBaseForText(item) {
  const base = {
    id: posterId(item),
    poster_url: item.poster_url,
    template_id: item.template_id,
    matted_url: item.matted_url,
    bg_url: item.bg_url,
  }
  appStore.setBasePoster(base)
  sessionStorage.setItem('poster_base_override', JSON.stringify(base))
  previewVisible.value = false
  ElMessage.success('已选择底图，进入加文案')
  router.push({ path: '/poster-workflow', query: { step: '3' } })
}

async function copyWriting(item) {
  const text = [item.title, item.body, item.tags].filter(Boolean).join('\n\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制全文')
  } catch {
    ElMessage.error('复制失败，请手动选择文本')
  }
}

function reuseInWriting(item) {
  sessionStorage.setItem('writing_reuse', JSON.stringify({
    product_name: item.product_name,
    product_features: item.product_features,
    platforms: String(item.platform || '').split(/[,，]/).map((s) => s.trim()).filter(Boolean),
    language: item.language || 'zh',
    style: item.style || 'default',
    title: item.title,
    body: item.body,
    tags: item.tags,
  }))
  router.push('/writing')
}

function useForPoster(item) {
  // 把长文案拆成海报叠字可用的短字段
  const lines = String(item.body || '')
    .split(/[\n。！？!?；;]/)
    .map((s) => s.trim())
    .filter(Boolean)
  const copy = {
    title: (item.title || item.product_name || '').slice(0, 40),
    subtitle: (lines[0] || item.product_features || '').slice(0, 48),
    selling_point_1: (lines[1] || '').slice(0, 36),
    selling_point_2: (lines[2] || '').slice(0, 36),
    cta_text: '立即选购',
    discount: (lines[0] || '').slice(0, 48),
    price: '立即选购',
  }
  // 一次性带入海报页，避免被全局旧缓存污染；进入后不再自动覆盖
  sessionStorage.setItem('poster_copy_override', JSON.stringify(copy))
  appStore.clearPosterConfig()
  appStore.setPosterConfig(copy, appStore.mattedProductId || appStore.selectedProductId)
  ElMessage.success('已带入海报文案，进入海报合成')
  router.push({ path: '/poster-workflow', query: { step: 'poster' } })
}

async function removeWriting(item) {
  try {
    await ElMessageBox.confirm(
      `确定删除「${item.product_name || item.title || '文案'}」吗？`,
      '删除文案',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  deletingWritingId.value = item.id
  try {
    await deleteWritingHistory(item.id)
    ElMessage.success('已删除')
    writings.value = writings.value.filter((x) => x.id !== item.id)
    writingTotal.value = Math.max(0, writingTotal.value - 1)
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '删除失败')
  } finally {
    deletingWritingId.value = null
  }
}

async function toggleFav(item) {
  const pid = posterId(item)
  if (!pid) return
  try {
    const d = await request.post(`/poster/favorite/${pid}`)
    ElMessage.success(d?.is_favorite === false ? '已取消收藏' : '收藏成功')
    if (posterMode.value === 'favorites') loadPosters()
  } catch { /* handled */ }
}

async function togglePublish(item) {
  const pid = posterId(item)
  if (!pid) return
  publishingId.value = pid
  try {
    if (item.is_public) {
      await unpublishPoster(pid)
      item.is_public = false
      ElMessage.success('已取消发布')
    } else {
      const d = await publishPoster(pid)
      item.is_public = true
      item.published_at = d?.published_at || item.published_at
      ElMessage.success('已发布到作品广场')
    }
    if (previewItem.value && posterId(previewItem.value) === pid) {
      previewItem.value.is_public = item.is_public
    }
  } catch {
    /* handled */
  } finally {
    publishingId.value = null
  }
}

async function removePoster(item) {
  const pid = posterId(item)
  if (!pid) return
  try {
    await ElMessageBox.confirm(
      `确定删除「${item.title || '未命名海报'}」吗？删除后不可恢复。`,
      '删除海报',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  deletingPosterId.value = pid
  try {
    await request.delete(`/poster/history/${pid}`)
    ElMessage.success('已删除')
    if (previewItem.value && posterId(previewItem.value) === pid) {
      previewVisible.value = false
      previewItem.value = null
    }
    posters.value = posters.value.filter((x) => posterId(x) !== pid)
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '删除失败')
  } finally {
    deletingPosterId.value = null
  }
}

watch(
  () => route.query.tab,
  (tab) => {
    if (tab === 'poster' || tab === 'writing') mainTab.value = tab
  },
)

onMounted(async () => {
  if (route.query.tab === 'poster') mainTab.value = 'poster'
  posterFilter.value = ''
  await Promise.all([loadWritings(), loadPosters()])
})
</script>

<style scoped>
.works-page { padding: 0; }
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.page-head h1 { margin: 0 0 6px; font-size: 22px; }
.subtitle { margin: 0; color: var(--ink-soft, #666); }
.head-actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }

.writing-list { display: flex; flex-direction: column; gap: 12px; }
.writing-card { border-radius: 12px; }
.writing-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}
.writing-product { font-size: 15px; }
.tag-row { margin-top: 6px; display: flex; gap: 6px; flex-wrap: wrap; }
.time { color: #999; font-size: 12px; white-space: nowrap; }
.writing-title { margin: 12px 0 8px; font-size: 16px; line-height: 1.4; }
.writing-body {
  margin: 0;
  color: #555;
  font-size: 14px;
  line-height: 1.65;
  white-space: pre-wrap;
  max-height: 160px;
  overflow: auto;
}
.writing-tags { margin: 8px 0 0; font-size: 12px; color: #888; }
.related {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.related-label { font-size: 12px; color: #666; }
.related-none { margin: 10px 0 0; font-size: 12px; color: #aaa; }
.related-thumb {
  width: 48px;
  height: 48px;
  padding: 0;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: #fff;
}
.related-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }

.poster-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.poster-card {
  margin-bottom: 16px;
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
}
.poster-card :deep(.el-card__body) { padding: 0; }
.thumb-wrap {
  aspect-ratio: 1;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.thumb-wrap img { width: 100%; height: 100%; object-fit: cover; }
.thumb-empty { color: #999; font-size: 13px; }
.card-body { padding: 12px 14px 14px; }
.card-title {
  display: block;
  font-size: 15px;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-meta {
  margin: 6px 0 0;
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-meta.faint { color: #999; }
.card-actions {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.pager { margin-top: 16px; display: flex; justify-content: center; }
.dialog-preview {
  display: flex;
  justify-content: center;
  background: #f7f7f7;
  border-radius: 8px;
  padding: 12px;
}
.dialog-preview img { max-width: 100%; max-height: 70vh; border-radius: 6px; }
</style>
