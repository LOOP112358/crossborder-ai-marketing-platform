<template>
  <div class="poster-page sketch-shell">
    <h1>海报合成</h1>
    <p class="subtitle">模板 + 商品图 + 背景图 · 支持多文字层样式（颜色 / 字体 / 艺术字 / 坐标）</p>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="never">
          <h3>生成海报</h3>

          <label>选择模板</label>
          <el-select v-model="form.template_id" style="width:100%" @change="onTemplateChange">
            <el-option
              v-for="t in templates"
              :key="t.id"
              :value="t.id"
              :label="`${t.id} - ${t.name}${t.purpose ? ' · ' + t.purpose : ''}（使用 ${t.usage_count} 次）`"
            />
          </el-select>
          <p class="hint">可切换不同用途模板：主图 / 种草 / 大促 / 短视频封面 / 横幅等</p>

          <h4 class="section-title">图片上传</h4>
          <label>商品图上传</label>
          <el-upload :auto-upload="false" :show-file-list="false" :on-change="(f) => onUpload(f, 'product')" accept="image/*">
            <el-button>上传商品图</el-button>
          </el-upload>
          <el-input v-model="form.matted_url" placeholder="/static/.../product.png" size="small" style="margin-top:4px" />

          <label>背景图上传</label>
          <el-upload :auto-upload="false" :show-file-list="false" :on-change="(f) => onUpload(f, 'bg')" accept="image/*">
            <el-button>上传背景图</el-button>
          </el-upload>
          <el-input v-model="form.bg_url" placeholder="/static/.../background.png" size="small" style="margin-top:4px" />

          <h4 class="section-title">文案内容</h4>
          <div class="action-row" style="margin-top:0;margin-bottom:8px">
            <el-button type="warning" @click="fillFromCatalog" :disabled="!appStore.selectedProductId && !appStore.posterConfig.title">
              使用库内商品文案
            </el-button>
            <el-button @click="fillChineseDemo">填入中文示例</el-button>
          </div>
          <label>主标题</label>
          <el-input v-model="form.title" placeholder="如：Portable Blender" />
          <label>副标题 / 核心卖点</label>
          <el-input v-model="form.subtitle" placeholder="如：Blend Anywhere, Anytime" />
          <label>卖点1</label>
          <el-input v-model="form.selling_point_1" placeholder="如：USB Rechargeable" />
          <label>卖点2</label>
          <el-input v-model="form.selling_point_2" placeholder="如：Easy to Clean" />
          <label>按钮文案 / 行动号召</label>
          <el-input v-model="form.cta_text" placeholder="如：Shop Now" />

          <h4 class="section-title">文字样式设置</h4>
          <p class="hint">展开每一层即可设置颜色、字体、艺术字、坐标与字号。</p>

          <el-collapse v-model="openPanels">
            <el-collapse-item
              v-for="layer in layers"
              :key="layer.prefix"
              :title="layer.title"
              :name="layer.prefix"
            >
              <el-row :gutter="10">
                <el-col :span="layer.isButton ? 12 : 8">
                  <label class="mini">颜色</label>
                  <div class="color-row">
                    <input type="color" v-model="form[layer.prefix + '_color']" />
                    <el-input v-model="form[layer.prefix + '_color']" size="small" />
                  </div>
                </el-col>
                <el-col :span="layer.isButton ? 12 : 8">
                  <label class="mini">字体</label>
                  <el-select v-model="form[layer.prefix + '_font_name']" style="width:100%" size="small">
                    <el-option v-for="f in fonts" :key="f.v" :label="f.l" :value="f.v" />
                  </el-select>
                </el-col>
                <el-col v-if="!layer.isButton" :span="8">
                  <label class="mini">艺术字</label>
                  <el-select v-model="form[layer.prefix + '_art_style']" style="width:100%" size="small">
                    <el-option v-for="a in artStyles" :key="a.v" :label="a.l" :value="a.v" />
                  </el-select>
                </el-col>
              </el-row>

              <el-row :gutter="10" style="margin-top:8px">
                <el-col :span="8">
                  <label class="mini">X 坐标</label>
                  <el-input-number v-model="form[layer.prefix + '_x']" :controls="false" placeholder="默认" style="width:100%" size="small" />
                </el-col>
                <el-col :span="8">
                  <label class="mini">Y 坐标</label>
                  <el-input-number v-model="form[layer.prefix + '_y']" :controls="false" placeholder="默认" style="width:100%" size="small" />
                </el-col>
                <el-col :span="8">
                  <label class="mini">字号</label>
                  <el-input-number v-model="form[layer.prefix + '_font_size']" :min="12" :max="200" :controls="false" placeholder="默认" style="width:100%" size="small" />
                </el-col>
              </el-row>

              <div v-if="layer.isButton" style="margin-top:8px">
                <label class="mini">按钮背景色</label>
                <div class="color-row">
                  <input type="color" v-model="form.cta_button_color" />
                  <el-input v-model="form.cta_button_color" size="small" />
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>

          <div class="action-row">
            <el-button type="primary" :loading="composing" @click="composePoster">生成海报</el-button>
            <el-button type="success" @click="useWhiteStyle">白底推荐样式</el-button>
            <el-button @click="resetStyle">恢复默认样式</el-button>
          </div>
          <p v-if="statusMsg" class="status-text">{{ statusMsg }}</p>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <h3>生成结果预览</h3>
          <div class="preview-box">
            <img v-if="posterUrl" :src="posterUrl" alt="poster" />
            <span v-else>暂无生成结果</span>
          </div>
        </el-card>

        <el-card shadow="never" style="margin-top:16px">
          <h3>历史记录</h3>
          <el-button @click="loadHistory">刷新历史记录</el-button>
          <el-button type="warning" @click="loadFavorites">查看收藏列表</el-button>
          <div v-if="listItems.length === 0" class="empty-tip">暂无数据</div>
          <div v-for="item in listItems" :key="item.id || item.poster_id" class="history-row">
            <div class="history-info">
              <strong>{{ item.title || '未命名海报' }}</strong>
              <div class="history-meta">
                副标题：{{ item.discount || '-' }} | 按钮：{{ item.price || '-' }} | 下载：{{ item.downloads || 0 }}次
              </div>
            </div>
            <div class="history-actions">
              <el-button size="small" @click="posterUrl = item.poster_url">预览</el-button>
              <a :href="`/api/poster/download/${item.poster_id || item.id}`" target="_blank">
                <el-button size="small">下载</el-button>
              </a>
              <el-button size="small" type="warning" @click="doFav(item.poster_id || item.id)">收藏</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import request from '@/api/request'
import { getPosterCopy } from '@/api/writing'
import { useAppStore } from '@/store/useAppStore'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const composing = ref(false)
const posterUrl = ref('')
const statusMsg = ref('')
const templates = ref([])
const listItems = ref([])
const openPanels = ref(['title'])

const fonts = [
  { v: 'msyh', l: '微软雅黑' },
  { v: 'simhei', l: '黑体' },
  { v: 'simsun', l: '宋体' },
  { v: 'kaiti', l: '楷体' },
  { v: 'arial', l: 'Arial' },
  { v: 'impact', l: 'Impact' },
]
const artStyles = [
  { v: 'normal', l: '普通' },
  { v: 'stroke', l: '描边' },
  { v: 'shadow', l: '阴影' },
  { v: 'stroke_shadow', l: '描边+阴影' },
  { v: 'glow', l: '发光' },
  { v: 'strong', l: '加粗' },
]

const layers = [
  { prefix: 'title', title: '主标题样式' },
  { prefix: 'subtitle', title: '副标题样式' },
  { prefix: 'selling_point_1', title: '卖点1样式' },
  { prefix: 'selling_point_2', title: '卖点2样式' },
  { prefix: 'cta_text', title: '按钮样式', isButton: true },
]

const form = reactive({
  matted_url: '',
  bg_url: '',
  template_id: 3,
  title: '',
  subtitle: '',
  selling_point_1: '',
  selling_point_2: '',
  cta_text: '',
  discount: '',
  price: '',
  ratio: '1:1',
  title_color: '#111111',
  title_font_name: 'msyh',
  title_art_style: 'stroke_shadow',
  title_x: null,
  title_y: null,
  title_font_size: null,
  subtitle_color: '#D81B60',
  subtitle_font_name: 'msyh',
  subtitle_art_style: 'stroke_shadow',
  subtitle_x: null,
  subtitle_y: null,
  subtitle_font_size: null,
  selling_point_1_color: '#111111',
  selling_point_1_font_name: 'msyh',
  selling_point_1_art_style: 'shadow',
  selling_point_1_x: null,
  selling_point_1_y: null,
  selling_point_1_font_size: null,
  selling_point_2_color: '#111111',
  selling_point_2_font_name: 'msyh',
  selling_point_2_art_style: 'shadow',
  selling_point_2_x: null,
  selling_point_2_y: null,
  selling_point_2_font_size: null,
  cta_text_color: '#FFFFFF',
  cta_button_color: '#111111',
  cta_text_font_name: 'msyh',
  cta_text_art_style: 'normal',
  cta_text_x: null,
  cta_text_y: null,
  cta_text_font_size: null,
  text_stroke_enabled: true,
  text_stroke_color: '#FFFFFF',
  text_stroke_width: 2,
  text_shadow_enabled: true,
})

async function onUpload(files, type) {
  const fd = new FormData()
  fd.append('file', files.raw)
  try {
    const data = await request.post('/poster/upload/image', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (type === 'product') form.matted_url = data.url
    else form.bg_url = data.url
    ElMessage.success('上传成功')
  } catch {}
}

async function loadTemplates() {
  try {
    templates.value = await request.get('/poster/templates')
    const ids = templates.value.map((t) => t.id)
    if (!ids.includes(form.template_id)) {
      form.template_id = ids.includes(3) ? 3 : (ids[0] || 3)
    }
    onTemplateChange(form.template_id, true)
  } catch {}
}

async function loadHistory() {
  try {
    const d = await request.get('/poster/history')
    listItems.value = d.items || []
  } catch {}
}

async function loadFavorites() {
  try {
    listItems.value = await request.get('/poster/favorites')
  } catch {}
}

async function composePoster() {
  if (!form.matted_url || !form.bg_url) {
    ElMessage.warning('请输入商品图和背景图 URL')
    return
  }
  if (form.matted_url.includes('/static/abo-images/')) {
    ElMessage.error('当前商品图还是库内原图（带白底）。请回到第1步完成抠图后再合成。')
    return
  }
  if (!form.matted_url.includes('/static/matte/') && !form.matted_url.includes('/static/poster/uploads/')) {
    ElMessage.warning('建议使用第1步抠图结果（/static/matte/...）作为商品图')
  }
  composing.value = true
  statusMsg.value = '正在生成海报...'
  try {
    const data = await request.post('/poster/compose', { ...form })
    posterUrl.value = data.poster_url
    statusMsg.value = '海报生成成功！'
    ElMessage.success('海报合成成功')
    loadTemplates()
    loadHistory()
  } catch (e) {
    statusMsg.value = '生成失败：' + (e?.response?.data?.detail || e?.message || '')
  } finally {
    composing.value = false
  }
}

function onTemplateChange(id, silent = false) {
  const t = templates.value.find((x) => x.id === id)
  const defaults = t?.config?.text_defaults
  if (!defaults) return
  const map = {
    title: 'title',
    subtitle: 'subtitle',
    selling_point_1: 'selling_point_1',
    selling_point_2: 'selling_point_2',
    cta_text: 'cta_text',
  }
  Object.entries(map).forEach(([key, prefix]) => {
    const d = defaults[key]
    if (!d) return
    if (d.color) form[`${prefix}_color`] = d.color
    if (d.font_name) form[`${prefix}_font_name`] = d.font_name
    if (d.art_style) form[`${prefix}_art_style`] = d.art_style
    if (d.x != null) form[`${prefix}_x`] = d.x
    if (d.y != null) form[`${prefix}_y`] = d.y
    if (d.font_size != null) form[`${prefix}_font_size`] = d.font_size
    if (key === 'cta_text' && d.button_color) form.cta_button_color = d.button_color
  })
  if (!silent) ElMessage.success(`已应用「${t.name}」推荐排版`)
}

function doFav(pid) {
  request.post(`/poster/favorite/${pid}`).then((d) => ElMessage.success(d.message || '已更新收藏')).catch(() => {})
}

function fillChineseDemo() {
  form.title = '便携式榨汁杯'
  form.subtitle = '户外旅行随身带'
  form.selling_point_1 = '无线充电'
  form.selling_point_2 = '清洗方便'
  form.cta_text = '立即购买'
}

function applyPosterCopy(copy) {
  if (!copy) return
  form.title = copy.title || form.title
  form.subtitle = copy.subtitle || form.subtitle
  form.selling_point_1 = copy.selling_point_1 || form.selling_point_1
  form.selling_point_2 = copy.selling_point_2 || form.selling_point_2
  form.cta_text = copy.cta_text || form.cta_text
  form.discount = copy.discount || form.discount
  form.price = copy.price || copy.cta_text || form.price
}

async function fillFromCatalog() {
  const cfg = appStore.posterConfig
  if (cfg?.title) {
    applyPosterCopy(cfg)
    if (appStore.mattedUrl) form.matted_url = appStore.mattedUrl
    if (appStore.enhancedBgUrl) form.bg_url = appStore.enhancedBgUrl
    ElMessage.success('已填入库内商品海报文案')
    return
  }
  if (!appStore.selectedProductId) {
    ElMessage.warning('请先在「商品抠图」步骤从商品库选品')
    return
  }
  try {
    const data = await getPosterCopy(appStore.selectedProductId, 'zh')
    appStore.setSelectedProduct(data.product, data.poster_copy)
    applyPosterCopy(data.poster_copy)
    if (data.product?.image_url) form.matted_url = data.product.image_url
    ElMessage.success('已根据商品库生成海报文案')
  } catch {}
}

function resetStyle() {
  ;['title', 'subtitle', 'selling_point_1', 'selling_point_2', 'cta_text'].forEach((p) => {
    form[`${p}_x`] = null
    form[`${p}_y`] = null
    form[`${p}_font_size`] = null
  })
  form.title_color = '#111111'
  form.subtitle_color = '#D81B60'
  form.selling_point_1_color = '#111111'
  form.selling_point_2_color = '#111111'
  form.cta_text_color = '#FFFFFF'
  form.cta_button_color = '#111111'
}

function useWhiteStyle() {
  resetStyle()
  form.title_x = 80
  form.title_y = 80
  form.title_font_size = 64
  form.subtitle_x = 80
  form.subtitle_y = 165
  form.subtitle_font_size = 42
  openPanels.value = ['title', 'subtitle']
}

onMounted(() => {
  loadTemplates()
  loadHistory()
  // 优先使用第1步抠图结果
  if (appStore.mattedUrl && appStore.mattedUrl.includes('/static/matte/')) {
    form.matted_url = appStore.mattedUrl
  } else if (appStore.mattedUrl && !appStore.mattedUrl.includes('/static/abo-images/')) {
    form.matted_url = appStore.mattedUrl
  } else {
    form.matted_url = ''
  }
  if (appStore.enhancedBgUrl) form.bg_url = appStore.enhancedBgUrl
  if (appStore.posterConfig?.title) applyPosterCopy(appStore.posterConfig)
})

watch(
  () => [appStore.mattedUrl, appStore.enhancedBgUrl, appStore.posterConfig],
  () => {
    if (appStore.mattedUrl && appStore.mattedUrl.includes('/static/matte/')) {
      form.matted_url = appStore.mattedUrl
    }
    if (appStore.enhancedBgUrl) form.bg_url = appStore.enhancedBgUrl
    if (appStore.posterConfig?.title && !form.title) applyPosterCopy(appStore.posterConfig)
  },
  { deep: true }
)
</script>

<style scoped>
.poster-page { padding: 0; }
.subtitle { color: var(--ink-soft, #666); margin-bottom: 16px; }
label { display: block; margin-top: 12px; margin-bottom: 4px; font-weight: 600; font-size: 14px; }
label.mini { margin-top: 0; font-size: 12px; font-weight: 500; color: #666; }
.section-title { margin-top: 20px; padding-top: 16px; border-top: 1px dashed rgba(44,58,66,.2); }
.hint { color: #777; font-size: 13px; margin: 4px 0 10px; }
.color-row { display: flex; gap: 8px; align-items: center; }
.color-row input[type='color'] { width: 42px; height: 32px; border: 1px solid #ccc; border-radius: 6px; padding: 0; background: #fff; }
.action-row { margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap; }
.preview-box {
  border: 2px dashed #dcdfe6;
  border-radius: 10px;
  padding: 12px;
  background: #fafafa;
  min-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}
.preview-box img { max-width: 100%; border-radius: 8px; }
.status-text { margin-top: 12px; color: #2f6f6a; font-weight: 600; word-break: break-all; }
.empty-tip { padding: 20px; text-align: center; color: #999; }
.history-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
  gap: 8px;
}
.history-info { flex: 1; min-width: 0; }
.history-meta { color: #666; font-size: 13px; word-break: break-all; }
.history-actions { display: flex; gap: 6px; flex-shrink: 0; }
</style>
