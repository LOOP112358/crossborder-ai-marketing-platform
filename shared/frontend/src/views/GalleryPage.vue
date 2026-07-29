<template>
  <div class="gallery-page sketch-shell">
    <div class="page-head">
      <div>
        <h1>作品广场</h1>
        <p class="subtitle">浏览所有用户发布的海报，可收藏到「我的作品」</p>
      </div>
      <div class="head-actions">
        <el-button @click="load" :loading="loading">刷新</el-button>
        <el-button type="primary" plain @click="$router.push('/my-works?tab=poster')">我的作品</el-button>
      </div>
    </div>

    <div class="toolbar">
      <el-input
        v-model="keyword"
        clearable
        size="small"
        style="width:260px"
        placeholder="搜索标题 / 作者 / 卖点"
      />
    </div>

    <el-empty v-if="!loading && filteredItems.length === 0" :description="emptyHint">
      <el-button type="primary" @click="$router.push('/my-works?tab=poster')">去发布我的海报</el-button>
    </el-empty>

    <el-row v-else :gutter="16">
      <el-col v-for="item in filteredItems" :key="item.id" :xs="24" :sm="12" :md="8" :lg="6">
        <el-card shadow="hover" class="poster-card" @click="openPreview(item)">
          <div class="thumb-wrap">
            <img v-if="item.poster_url" :src="item.poster_url" :alt="item.title || 'poster'" loading="lazy" />
            <div v-else class="thumb-empty">无预览</div>
            <el-tag v-if="item.is_own" class="own-badge" size="small" type="success" effect="dark">我的</el-tag>
          </div>
          <div class="card-body">
            <strong class="card-title">{{ item.title || '未命名海报' }}</strong>
            <p class="card-meta">
              {{ item.discount || '—' }}
              <span v-if="item.price"> · {{ item.price }}</span>
            </p>
            <p class="card-meta faint">
              @{{ item.username || '未知' }}
              · 下载 {{ item.downloads || 0 }} 次
              <span v-if="item.published_at"> · {{ formatTime(item.published_at) }}</span>
            </p>
            <div class="card-actions" @click.stop>
              <el-button size="small" @click="openPreview(item)">预览</el-button>
              <a :href="downloadUrl(item)" target="_blank" rel="noopener">
                <el-button size="small" type="primary">下载</el-button>
              </a>
              <el-button
                size="small"
                :type="item.is_favorite ? 'warning' : 'default'"
                :loading="togglingId === item.id"
                @click="toggleFav(item)"
              >
                {{ item.is_favorite ? '已收藏' : '收藏' }}
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div v-if="total > pageSize" class="pager">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="load"
      />
    </div>

    <el-dialog v-model="previewVisible" title="海报预览" width="720px" destroy-on-close>
      <div class="dialog-preview">
        <img v-if="previewItem?.poster_url" :src="previewItem.poster_url" alt="preview" />
      </div>
      <template #footer>
        <div class="dialog-meta" v-if="previewItem">
          <span>{{ previewItem.title || '未命名海报' }}</span>
          <span class="faint">@{{ previewItem.username }}</span>
        </div>
        <el-button @click="previewVisible = false">关闭</el-button>
        <a v-if="previewItem" :href="downloadUrl(previewItem)" target="_blank" rel="noopener">
          <el-button type="primary">下载原图</el-button>
        </a>
        <el-button
          v-if="previewItem"
          :type="previewItem.is_favorite ? 'warning' : 'default'"
          :loading="togglingId === previewItem.id"
          @click="toggleFav(previewItem)"
        >
          {{ previewItem.is_favorite ? '已收藏' : '收藏' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getPosterGallery, toggleFavorite } from '@/api/poster'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const items = ref([])
const page = ref(1)
const pageSize = 24
const total = ref(0)
const keyword = ref('')
const togglingId = ref(null)
const previewVisible = ref(false)
const previewItem = ref(null)

const filteredItems = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return items.value
  const parts = q.split(/\s+/).filter(Boolean)
  return items.value.filter((p) => {
    const blob = `${p.title || ''} ${p.discount || ''} ${p.price || ''} ${p.username || ''}`.toLowerCase()
    if (parts.length <= 1) return blob.includes(q)
    return parts.every((part) => blob.includes(part))
  })
})

const emptyHint = computed(() => {
  if (items.value.length && keyword.value.trim() && !filteredItems.value.length) {
    return '没有匹配当前搜索的作品'
  }
  return '广场暂无作品，去「我的作品」发布第一张吧'
})

function downloadUrl(item) {
  return `/api/poster/download/${item.id}`
}

function formatTime(s) {
  const t = String(s || '').replace('T', ' ')
  return t.length > 19 ? t.slice(0, 19) : t
}

function openPreview(item) {
  previewItem.value = item
  previewVisible.value = true
}

async function load() {
  loading.value = true
  try {
    const data = await getPosterGallery(page.value, pageSize)
    items.value = data?.items || []
    total.value = data?.total || 0
  } catch (e) {
    ElMessage.error(e?.message || '加载作品广场失败')
    items.value = []
  } finally {
    loading.value = false
  }
}

async function toggleFav(item) {
  if (!item?.id) return
  togglingId.value = item.id
  try {
    const d = await toggleFavorite(item.id)
    const next = !!d?.is_favorite
    item.is_favorite = next
    if (previewItem.value?.id === item.id) {
      previewItem.value.is_favorite = next
    }
    const row = items.value.find((x) => x.id === item.id)
    if (row) row.is_favorite = next
    ElMessage.success(d?.message || (next ? '收藏成功' : '已取消收藏'))
  } catch {
    /* handled by interceptor */
  } finally {
    togglingId.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.gallery-page { padding: 0; }
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.page-head h1 { margin: 0 0 6px; font-size: 22px; }
.subtitle { margin: 0; color: var(--ink-soft, #666); }
.head-actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.toolbar { margin-bottom: 14px; }
.poster-card {
  margin-bottom: 16px;
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
}
.poster-card :deep(.el-card__body) { padding: 0; }
.thumb-wrap {
  position: relative;
  aspect-ratio: 1;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.thumb-wrap img { width: 100%; height: 100%; object-fit: cover; }
.thumb-empty { color: #999; font-size: 13px; }
.own-badge {
  position: absolute;
  top: 8px;
  left: 8px;
}
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
.card-meta.faint, .faint { color: #999; }
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
.dialog-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-right: auto;
  font-size: 13px;
}
</style>
