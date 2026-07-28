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
          <el-alert
            v-if="copyMismatch"
            type="error"
            :closable="false"
            show-icon
            style="margin-bottom:10px"
            title="图文可能不一致：当前抠图与文案商品不是同一件。请点「AI 精炼短文案」同步，或回到第1步重新选品抠图。"
          />
          <el-alert
            v-else-if="boundProductLabel"
            type="success"
            :closable="false"
            show-icon
            style="margin-bottom:10px"
            :title="`当前绑定商品：${boundProductLabel}`"
          />
          <p class="hint">每次进入会按当前商品重新 AI 精炼（自动清空旧缓存）；也可点「仅用库内原文」跳过 AI。</p>
          <div class="action-row" style="margin-top:0;margin-bottom:8px">
            <el-button type="primary" :loading="refiningCopy" @click="refineWithAI" :disabled="!copyProductId">
              AI 精炼短文案
            </el-button>
            <el-button type="warning" plain @click="fillFromCatalog" :disabled="!appStore.selectedProductId && !appStore.mattedProductId && !appStore.posterConfig.title">
              仅用库内原文
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
            <el-checkbox v-model="form.auto_layout">自动排版（按模板安全区换行/间距）</el-checkbox>
            <el-checkbox v-model="form.text_stroke_enabled">文字描边</el-checkbox>
            <el-checkbox v-model="form.text_shadow_enabled">文字阴影</el-checkbox>
          </div>
          <div class="action-row">
            <el-checkbox v-model="form.refine_enabled">融合精修（画文字前）</el-checkbox>
            <el-select v-model="form.refine_engine" style="width:220px" size="small" :disabled="!form.refine_enabled">
              <el-option value="seedream" label="Seedream 精修" />
            </el-select>
          </div>
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
          <div class="preview-head">
            <h3>生成结果预览</h3>
            <el-button type="primary" link @click="$router.push('/my-works?tab=poster')">查看全部历史 →</el-button>
          </div>
          <div class="preview-box">
            <img v-if="posterUrl" :src="posterUrl" alt="poster" />
            <span v-else>暂无生成结果</span>
          </div>
          <div v-if="posterUrl" class="preview-actions">
            <el-button type="primary" @click="$router.push('/my-works?tab=poster')">打开我的作品</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import request from '@/api/request'
import { getPosterCopy } from '@/api/writing'
import { useAppStore } from '@/store/useAppStore'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const composing = ref(false)
const refiningCopy = ref(false)
const posterUrl = ref('')
const statusMsg = ref('')
const templates = ref([])
const openPanels = ref(['title'])

/** 优先用「抠图绑定」的商品 id，保证图文同源 */
const copyProductId = computed(() => appStore.mattedProductId || appStore.selectedProductId)
const copyMismatch = computed(() => {
  if (!appStore.mattedProductId || !appStore.selectedProductId) return false
  return Number(appStore.mattedProductId) !== Number(appStore.selectedProductId)
})
const boundProductLabel = computed(() => {
  const p = appStore.selectedProduct
  if (!p) return ''
  const name = p.name || p.item_name || p.label || ''
  const brand = p.brand || ''
  return [brand, name].filter(Boolean).join(' · ').slice(0, 80)
})

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
  template_id: 9,
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
  title_art_style: 'shadow',
  title_x: null,
  title_y: null,
  title_font_size: null,
  subtitle_color: '#D81B60',
  subtitle_font_name: 'msyh',
  subtitle_art_style: 'normal',
  subtitle_x: null,
  subtitle_y: null,
  subtitle_font_size: null,
  selling_point_1_color: '#111111',
  selling_point_1_font_name: 'msyh',
  selling_point_1_art_style: 'normal',
  selling_point_1_x: null,
  selling_point_1_y: null,
  selling_point_1_font_size: null,
  selling_point_2_color: '#111111',
  selling_point_2_font_name: 'msyh',
  selling_point_2_art_style: 'normal',
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
  text_stroke_enabled: false,
  text_stroke_color: '#FFFFFF',
  text_stroke_width: 2,
  text_shadow_enabled: true,
  auto_layout: true,
  refine_enabled: true,
  refine_engine: 'seedream',
  sd_refine: false,
  sd_refine_strength: 0.28,
  product_hint: '',
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
      form.template_id = ids.includes(9) ? 9 : (ids.includes(2) ? 2 : (ids[0] || 9))
    }
    onTemplateChange(form.template_id, true)
  } catch {}
}

async function composePoster() {
  if (!form.matted_url || !form.bg_url) {
    ElMessage.warning('请输入商品图和背景图 URL')
    return
  }
  if (copyMismatch.value) {
    ElMessage.error('图文商品不一致，请先点「AI 精炼短文案」同步，或回第1步重新抠图')
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
  statusMsg.value = form.refine_enabled
    ? '正在合成并用 Seedream 融合精修（约 15～45 秒）...'
    : '正在生成海报...'
  try {
    const p = appStore.selectedProduct || {}
    const payload = {
      ...form,
      sd_refine: false,
      refine_enabled: form.refine_enabled,
      refine_engine: 'seedream',
      product_hint: [p.brand, p.name || p.item_name, p.product_type].filter(Boolean).join(' / '),
    }
    const data = await request.post('/poster/compose', payload, {
      timeout: form.refine_enabled ? 180000 : 60000,
    })
    posterUrl.value = data.poster_url
    statusMsg.value = '海报生成成功！'
    ElMessage.success('海报合成成功，可在「我的海报」中查看历史')
    loadTemplates()
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
    // 自动排版时不锁死模板坐标，交给后端安全区堆叠
    if (!form.auto_layout) {
      if (d.x != null) form[`${prefix}_x`] = d.x
      if (d.y != null) form[`${prefix}_y`] = d.y
    } else {
      form[`${prefix}_x`] = null
      form[`${prefix}_y`] = null
    }
    if (d.font_size != null) form[`${prefix}_font_size`] = d.font_size
    if (key === 'cta_text' && d.button_color) form.cta_button_color = d.button_color
  })
  if (!silent) ElMessage.success(`已应用「${t.name}」推荐样式${form.auto_layout ? '（自动排版开启）' : ''}`)
}

function fillChineseDemo() {
  form.title = '便携式榨汁杯'
  form.subtitle = '户外旅行随身带'
  form.selling_point_1 = '无线充电'
  form.selling_point_2 = '清洗方便'
  form.cta_text = '立即购买'
}

function cleanCopyText(s) {
  return String(s || '')
    .replace(/[…]+$/g, '')
    .replace(/\.{3,}$/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function applyPosterCopy(copy) {
  if (!copy) return
  // 整组覆盖，禁止 || 旧值（否则会串上一件商品）
  form.title = cleanCopyText(copy.title)
  form.subtitle = cleanCopyText(copy.subtitle)
  form.selling_point_1 = cleanCopyText(copy.selling_point_1)
  form.selling_point_2 = cleanCopyText(copy.selling_point_2)
  form.cta_text = cleanCopyText(copy.cta_text)
  form.discount = cleanCopyText(copy.discount)
  form.price = cleanCopyText(copy.price || copy.cta_text)
}

function clearFormCopy() {
  form.title = ''
  form.subtitle = ''
  form.selling_point_1 = ''
  form.selling_point_2 = ''
  form.cta_text = ''
  form.discount = ''
  form.price = ''
}

async function fillFromCatalog() {
  const pid = copyProductId.value
  if (!pid) {
    ElMessage.warning('请先在「商品抠图」步骤从商品库选品并抠图')
    return
  }
  try {
    clearFormCopy()
    appStore.clearPosterConfig()
    const data = await getPosterCopy(pid, 'zh', false)
    appStore.setSelectedProduct(data.product, data.poster_copy)
    applyPosterCopy(data.poster_copy)
    ElMessage.success(`已填入「${boundProductLabel.value || data.product?.name || '当前商品'}」库内原文（未走 AI）`)
  } catch (e) {
    ElMessage.error('拉取文案失败：' + (e?.message || ''))
  }
}

async function refineWithAI() {
  const pid = copyProductId.value
  if (!pid) {
    ElMessage.warning('请先从商品库选品并抠图')
    return
  }
  refiningCopy.value = true
  // 先清缓存，避免请求期间仍显示上一件商品文案
  clearFormCopy()
  appStore.clearPosterConfig()
  try {
    const data = await getPosterCopy(pid, 'zh', true)
    const returnedId = data?.product?.id
    if (returnedId != null && Number(returnedId) !== Number(pid)) {
      throw new Error('返回文案商品与当前抠图不一致，已丢弃')
    }
    // 精炼完成时若用户已换品，丢弃结果
    if (Number(copyProductId.value) !== Number(pid)) {
      ElMessage.warning('商品已切换，已丢弃过期文案')
      return
    }
    appStore.setSelectedProduct(data.product, data.poster_copy)
    applyPosterCopy(data.poster_copy)
    const src = data.poster_copy?.source === 'kb+llm' ? '知识库 + DeepSeek' : '知识库规则（LLM 未就绪，已回退）'
    ElMessage.success(`已用${src}精炼短文案`)
  } catch (e) {
    ElMessage.error('精炼失败：' + (e?.response?.data?.detail || e?.message || ''))
  } finally {
    refiningCopy.value = false
  }
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

onMounted(async () => {
  loadTemplates()
  // 优先使用第1步抠图结果
  if (appStore.mattedUrl && appStore.mattedUrl.includes('/static/matte/')) {
    form.matted_url = appStore.mattedUrl
  } else if (appStore.mattedUrl && !appStore.mattedUrl.includes('/static/abo-images/')) {
    form.matted_url = appStore.mattedUrl
  } else {
    form.matted_url = ''
  }
  form.bg_url = appStore.preferredBgUrl || appStore.seedreamBgUrl || appStore.enhancedBgUrl || form.bg_url
  clearFormCopy()

  // 从「我的作品」一键带入的文案：优先使用，不再自动 AI 覆盖
  let override = null
  try {
    const raw = sessionStorage.getItem('poster_copy_override')
    if (raw) {
      override = JSON.parse(raw)
      sessionStorage.removeItem('poster_copy_override')
    }
  } catch { /* ignore */ }

  if (override?.title) {
    applyPosterCopy(override)
    appStore.setPosterConfig(override, appStore.mattedProductId || appStore.selectedProductId)
    ElMessage.success('已应用从作品库带入的文案')
    return
  }

  const pid = appStore.mattedProductId || appStore.selectedProductId
  if (pid) {
    if (!appStore.isPosterConfigForProduct(pid)) {
      appStore.clearPosterConfig()
    }
    try {
      await refineWithAI()
    } catch {
      /* refineWithAI 内部已提示 */
    }
  } else {
    appStore.clearPosterConfig()
  }
})

watch(
  () => [appStore.mattedUrl, appStore.preferredBgUrl, appStore.seedreamBgUrl, appStore.enhancedBgUrl],
  () => {
    if (appStore.mattedUrl && appStore.mattedUrl.includes('/static/matte/')) {
      form.matted_url = appStore.mattedUrl
    }
    const bg = appStore.preferredBgUrl || appStore.seedreamBgUrl || appStore.enhancedBgUrl
    if (bg) form.bg_url = bg
  },
)

watch(
  () => appStore.mattedProductId,
  (pid, prev) => {
    if (pid == null || (prev != null && Number(pid) !== Number(prev))) {
      clearFormCopy()
      appStore.clearPosterConfig()
    }
    if (pid) refineWithAI()
  },
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
.preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.preview-head h3 { margin: 0; }
.preview-actions { margin-top: 12px; }
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
</style>

