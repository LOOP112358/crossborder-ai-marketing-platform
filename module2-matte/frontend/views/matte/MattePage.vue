<template>
  <div class="matte-page sketch-shell">
    <el-row :gutter="20">
      <el-col :span="10">
        <el-card shadow="never">
          <template #header>
            <span class="panel-title">商品抠图 / 选品</span>
          </template>

          <el-form label-position="top" size="default">
            <el-form-item label="从 ABO 商品库选择（推荐）">
              <div class="cat-chips">
                <el-tag
                  v-for="c in quickCats"
                  :key="c.product_type"
                  class="cat-chip"
                  :effect="activeType === c.product_type ? 'dark' : 'plain'"
                  round
                  @click="pickCategory(c)"
                >{{ c.label }}</el-tag>
                <el-tag class="cat-chip" :effect="!activeType ? 'dark' : 'plain'" round @click="pickCategory(null)">混合推荐</el-tag>
              </div>
              <el-select
                v-model="selectedId"
                filterable
                remote
                clearable
                :remote-method="remoteSearch"
                :loading="searching"
                placeholder="搜：沙发 / shoe / 耳机 / grocery…"
                style="width:100%"
                @change="onCatalogPick"
                @focus="() => { if (!productOptions.length) remoteSearch('') }"
              >
                <el-option
                  v-for="p in productOptions"
                  :key="p.id"
                  :label="p.label"
                  :value="p.id"
                >
                  <div class="opt-row">
                    <img v-if="p.image_url" :src="p.image_url" class="opt-thumb" alt="" />
                    <div class="opt-text">
                      <div class="opt-name">{{ p.name }}</div>
                      <div class="opt-meta">{{ p.category }} · {{ p.has_image ? '有主图' : '无图' }}</div>
                    </div>
                  </div>
                </el-option>
              </el-select>
              <p class="hint">库里手机壳最多；点上方品类或搜「沙发 / 鞋 / 耳机」可换一批。选品后请抠图。</p>
            </el-form-item>
          </el-form>

          <el-button
            v-if="catalogProduct?.image_url"
            type="primary"
            size="large"
            block
            :loading="processing"
            @click="matteCatalogProduct"
          >
            {{ processing ? '正在抠图...' : '对库内主图抠图并进入工作流' }}
          </el-button>

          <div class="upload-area">
            <input type="file" ref="fileInput" accept="image/jpeg,image/png,image/webp"
              @change="onFilePicked" style="display:none" />
            <el-button size="large" @click="$refs.fileInput.click()" :disabled="processing">
              或自行上传图片抠图
            </el-button>
            <p class="hint">支持 JPG / PNG / WEBP，最大 10MB</p>
            <img v-if="originalPreview" :src="originalPreview" class="preview-img" alt="原图" />
          </div>
          <el-form v-if="file" class="options-form">
            <el-form-item label="边缘优化">
              <el-radio-group v-model="smoothing">
                <el-radio :label="0">无</el-radio>
                <el-radio :label="1">轻度</el-radio>
                <el-radio :label="2">中度</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-button type="primary" size="large" :loading="processing" block @click="processMatte">
              {{ processing ? '处理中...' : '开始智能抠图' }}
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card v-if="result || catalogProduct" shadow="never" class="result-card">
          <template #header>
            <span class="panel-title">商品信息 / 抠图结果</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="12">
              <p class="img-label">原图 / 库内主图</p>
              <img :src="originalPreview || catalogProduct?.image_url" class="result-img" />
            </el-col>
            <el-col :span="12">
              <p class="img-label">透明底 PNG（供海报使用）</p>
              <img
                v-if="resultImageUrl"
                :src="resultImageUrl"
                class="result-img checker-bg"
              />
              <el-empty v-else description="请先完成抠图" :image-size="64" />
            </el-col>
          </el-row>
          <el-descriptions :column="2" border class="info-table" size="small">
            <el-descriptions-item label="商品类别">{{ displayCategory }}</el-descriptions-item>
            <el-descriptions-item label="英文类别">{{ displayCategoryEn }}</el-descriptions-item>
            <el-descriptions-item label="置信度">{{ Math.round(displayConfidence * 100) }}%</el-descriptions-item>
            <el-descriptions-item label="颜色">{{ displayColor }}</el-descriptions-item>
            <el-descriptions-item v-if="catalogProduct" label="品牌" :span="2">
              {{ catalogProduct.brand || '-' }}
            </el-descriptions-item>
          </el-descriptions>
          <div class="actions">
            <el-button v-if="result" type="success" @click="downloadResult">下载 PNG</el-button>
            <el-tag v-if="isRealMatted" type="success" style="margin-left:12px">
              抠图结果已写入全局状态 → 海报将使用透明底
            </el-tag>
            <el-tag v-else-if="catalogProduct" type="warning" style="margin-left:12px">
              尚未抠图，请先点击上方按钮
            </el-tag>
          </div>
        </el-card>

        <el-empty v-else description="从商品库选品，或上传图片开始抠图" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { processMatte as processMatteApi, processMatteFromUrl, getMatteDownloadUrl } from '@/api/matte'
import { searchWritingProducts, getPosterCopy, listProductCategories } from '@/api/writing'
import { useAppStore } from '@/store/useAppStore'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const fileInput = ref(null)
const file = ref(null)
const originalPreview = ref('')
const smoothing = ref(1)
const processing = ref(false)
const result = ref(null)
const resultImageUrl = ref('')

const selectedId = ref(null)
const productOptions = ref([])
const searching = ref(false)
const catalogProduct = ref(null)
const activeType = ref('')
const quickCats = ref([
  { product_type: 'SHOES', label: '鞋子' },
  { product_type: 'SOFA', label: '沙发' },
  { product_type: 'CHAIR', label: '椅子' },
  { product_type: 'GROCERY', label: '食品' },
  { product_type: 'HEADPHONES', label: '耳机' },
  { product_type: 'CELLULAR_PHONE_CASE', label: '手机壳' },
  { product_type: 'BOOT', label: '靴子' },
  { product_type: 'WRIST_WATCH', label: '手表' },
])
let searchTimer = null

const isRealMatted = computed(() => (appStore.mattedUrl || '').includes('/static/matte/'))

const displayCategory = computed(
  () => result.value?.category || catalogProduct.value?.category || appStore.category || '-'
)
const displayCategoryEn = computed(
  () => result.value?.category_en || catalogProduct.value?.category_en || appStore.categoryEn || '-'
)
const displayConfidence = computed(() => {
  if (result.value?.confidence != null) return result.value.confidence
  return appStore.confidence || 0
})
const displayColor = computed(
  () => result.value?.attributes?.color || catalogProduct.value?.color || '-'
)

async function remoteSearch(query) {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    searching.value = true
    try {
      const data = await searchWritingProducts(query || '', 24, true, {
        diverse: !activeType.value && !query,
        product_type: activeType.value,
      })
      productOptions.value = data.items || []
    } catch {
      productOptions.value = []
    } finally {
      searching.value = false
    }
  }, 200)
}

function pickCategory(c) {
  activeType.value = c?.product_type || ''
  selectedId.value = null
  remoteSearch('')
}

async function loadCategories() {
  try {
    const data = await listProductCategories()
    const items = data.items || []
    if (items.length) {
      // 取前若干热门，但把手机壳排后一点
      const preferred = ['SHOES', 'SOFA', 'CHAIR', 'GROCERY', 'HEADPHONES', 'BOOT', 'TABLE', 'WRIST_WATCH', 'BACKPACK', 'CELLULAR_PHONE_CASE']
      const map = Object.fromEntries(items.map((x) => [x.product_type, x]))
      const ordered = preferred.map((pt) => map[pt]).filter(Boolean)
      const rest = items.filter((x) => !preferred.includes(x.product_type)).slice(0, 4)
      quickCats.value = [...ordered, ...rest].slice(0, 10)
    }
  } catch {
    // keep defaults
  }
}

async function onCatalogPick(id) {
  if (!id) {
    catalogProduct.value = null
    return
  }
  const p = productOptions.value.find((x) => x.id === id)
  if (!p) return
  catalogProduct.value = p
  originalPreview.value = p.image_url || ''
  result.value = null
  resultImageUrl.value = ''
  try {
    const data = await getPosterCopy(id, 'zh')
    appStore.setSelectedProduct(data.product, data.poster_copy)
    catalogProduct.value = data.product
    ElMessage.success('已选库内商品，请点击「对库内主图抠图」')
  } catch {
    appStore.setSelectedProduct(p)
  }
}

async function matteCatalogProduct() {
  if (!catalogProduct.value?.image_url) {
    ElMessage.warning('该商品暂无主图')
    return
  }
  processing.value = true
  try {
    const data = await processMatteFromUrl(
      catalogProduct.value.image_url,
      smoothing.value,
      catalogProduct.value.category || '',
      catalogProduct.value.category_en || catalogProduct.value.product_type || ''
    )
    result.value = data
    resultImageUrl.value = data.matted_url
    originalPreview.value = data.original_url || catalogProduct.value.image_url
    appStore.setMatteResult(data.matted_url, data.category, data.category_en, data.confidence)
    ElMessage.success('抠图完成，可进入背景生成 / 海报合成')
  } catch {
    // handled
  } finally {
    processing.value = false
  }
}

function onFilePicked(e) {
  file.value = e.target.files?.[0]
  if (file.value) {
    originalPreview.value = URL.createObjectURL(file.value)
    result.value = null
    resultImageUrl.value = ''
  }
}

async function processMatte() {
  if (!file.value) return
  processing.value = true
  try {
    const form = new FormData()
    form.append('file', file.value)
    form.append('edge_smoothing', String(smoothing.value))
    const data = await processMatteApi(form)
    result.value = data
    resultImageUrl.value = data.matted_url
    appStore.setMatteResult(data.matted_url, data.category, data.category_en, data.confidence)
    ElMessage.success('抠图与识别完成')
  } catch {
    // handled
  } finally {
    processing.value = false
  }
}

function downloadResult() {
  if (result.value) {
    window.open(getMatteDownloadUrl(result.value.id), '_blank')
  }
}

onMounted(() => {
  loadCategories()
  remoteSearch('')
  if (appStore.selectedProduct) {
    catalogProduct.value = appStore.selectedProduct
    selectedId.value = appStore.selectedProductId
    originalPreview.value = appStore.productImageUrl || ''
  }
  if (isRealMatted.value) {
    resultImageUrl.value = appStore.mattedUrl
    result.value = {
      matted_url: appStore.mattedUrl,
      category: appStore.category,
      category_en: appStore.categoryEn,
      confidence: appStore.confidence,
    }
  }
})
</script>

<style scoped>
.matte-page { padding: 0; }
.panel-title { display: flex; align-items: center; gap: 6px; font-weight: 600; }
.upload-area { text-align: center; padding: 16px 0; }
.hint { color: #909399; font-size: 12px; margin: 8px 0 0; line-height: 1.4; }
.preview-img { max-width: 100%; max-height: 200px; margin-top: 12px; border-radius: 4px; }
.options-form { margin-top: 16px; }
.result-card { margin-bottom: 0; }
.result-img { width: 100%; max-height: 300px; object-fit: contain; border-radius: 4px; }
.checker-bg { background: repeating-conic-gradient(#eee 0% 25%, #fff 0% 50%) 50% / 20px 20px; }
.img-label { text-align: center; font-size: 13px; color: #909399; margin-bottom: 8px; }
.info-table { margin-top: 16px; }
.actions { margin-top: 16px; display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.opt-row { display: flex; gap: 8px; align-items: center; max-width: 360px; }
.opt-thumb { width: 36px; height: 36px; object-fit: cover; border-radius: 6px; border: 1px solid #ddd; flex-shrink: 0; }
.opt-text { min-width: 0; }
.opt-name { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.opt-meta { font-size: 11px; color: #909399; }
.cat-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.cat-chip { cursor: pointer; user-select: none; }
</style>
