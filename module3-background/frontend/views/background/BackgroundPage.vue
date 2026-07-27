<template>
  <div class="bg-page sketch-shell">
    <el-row :gutter="20">
      <el-col :span="9">
        <el-card shadow="never">
          <template #header>
            <span class="panel-title"><el-icon><PictureFilled /></el-icon> 背景生成</span>
          </template>
          <el-alert
            v-if="productHint"
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom:12px"
            :title="`商品上下文：${productHint}`"
          />
          <el-form label-position="top" class="bg-form">
            <el-form-item label="场景品类（可改）">
              <el-input v-model="form.category" placeholder="如：咖啡桌、平板保护套…" />
              <el-button
                v-if="suggestedCategory && suggestedCategory !== form.category"
                size="small"
                type="success"
                style="margin-top:8px"
                @click="form.category = suggestedCategory"
              >
                使用推荐：{{ suggestedCategory }}
              </el-button>
            </el-form-item>

            <el-form-item label="场景预设">
              <el-select v-model="form.scene_preset" clearable filterable style="width:100%" placeholder="自动按商品推断">
                <el-option v-for="s in options.scenes" :key="s.value || 'auto'" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>

            <el-form-item label="视觉风格">
              <el-select v-model="form.style" style="width:100%">
                <el-option v-for="s in options.styles" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>

            <el-form-item label="色调">
              <el-select v-model="form.color_hint" allow-create filterable clearable style="width:100%" placeholder="自定义或选择">
                <el-option v-for="c in options.colors" :key="c.value || 'c0'" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>

            <el-form-item label="光照">
              <el-select v-model="form.lighting" clearable style="width:100%">
                <el-option v-for="l in options.lightings" :key="l.value || 'l0'" :label="l.label" :value="l.value" />
              </el-select>
            </el-form-item>

            <el-form-item label="氛围">
              <el-select v-model="form.mood" clearable style="width:100%">
                <el-option v-for="m in options.moods" :key="m.value || 'm0'" :label="m.label" :value="m.value" />
              </el-select>
            </el-form-item>

            <el-form-item label="机位 / 构图">
              <el-select v-model="form.camera" clearable style="width:100%">
                <el-option v-for="c in options.cameras" :key="c.value || 'cam0'" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>

            <el-form-item label="补充说明（可选）">
              <el-input
                v-model="form.extra_note"
                type="textarea"
                :rows="2"
                maxlength="200"
                show-word-limit
                placeholder="例如：留出地面空间放咖啡桌；不要出现其他家具"
              />
            </el-form-item>

            <el-form-item label="生成引擎">
              <el-checkbox v-model="form.use_sd">同时调用 Stable Diffusion（耗额度，可选对照）</el-checkbox>
              <p class="hint">默认只用豆包 Seedream，够用进海报；SD 额度不足时请保持关闭。</p>
            </el-form-item>

            <el-button type="primary" size="large" :loading="generating" block @click="handleGenerate">
              <el-icon><MagicStick /></el-icon> 生成背景
            </el-button>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="15">
        <el-card v-if="result" shadow="never">
          <template #header>
            生成结果（点击选用，默认推荐 Seedream）
          </template>
          <el-row :gutter="16">
            <el-col :span="12">
              <div
                class="pick-card"
                :class="{ active: preferred === 'seedream' }"
                @click="pick('seedream')"
              >
                <p class="img-label">豆包 Seedream（推荐进海报）</p>
                <img :src="result.bg_url" class="result-img" />
              </div>
            </el-col>
            <el-col :span="12">
              <div
                class="pick-card"
                :class="{ active: preferred === 'sd' }"
                @click="pick('sd')"
              >
                <p class="img-label">Stable Diffusion</p>
                <img :src="result.enhanced_url" class="result-img" />
              </div>
            </el-col>
          </el-row>
          <el-descriptions :column="2" border size="small" style="margin-top:16px">
            <el-descriptions-item label="类别">{{ result.product_category }}</el-descriptions-item>
            <el-descriptions-item label="风格">{{ result.style }}</el-descriptions-item>
            <el-descriptions-item label="Prompt" :span="2">{{ result.prompt_used }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
        <el-empty v-else description="设置左侧选项后生成背景；可点选结果进入海报" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAppStore } from '@/store/useAppStore'
import request from '@/api/request'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const generating = ref(false)
const result = ref(null)
const preferred = ref('seedream')

const options = reactive({
  styles: [],
  scenes: [],
  lightings: [],
  moods: [],
  cameras: [],
  colors: [],
})

const form = reactive({
  category: '',
  style: 'warm',
  color_hint: '',
  scene_preset: '',
  lighting: '',
  mood: '',
  camera: '',
  extra_note: '',
  use_sd: false,
})

const product = computed(() => appStore.selectedProduct || {})
const productHint = computed(() => {
  const p = product.value
  if (!p?.name && !p?.brand) return ''
  return [p.brand, p.name || p.item_name, p.product_type || p.category].filter(Boolean).join(' · ')
})

const suggestedCategory = computed(() => {
  const p = product.value
  const name = `${p.name || ''} ${p.item_name || ''} ${p.product_type || ''}`.toLowerCase()
  if (/tablet|kindle|ipad|sleeve|case|保护套|手机壳|平板/.test(name)) return '数码保护套 / 桌面陈列'
  if (/headphone|earbud|耳机/.test(name)) return '耳机配件'
  if (/coffee.?table|茶几|咖啡桌|\btable\b/.test(name)) return '咖啡桌 / 客厅家具'
  if (p.category) return p.category
  return appStore.category || ''
})

function pick(which) {
  preferred.value = which
  appStore.chooseBackground(which)
  ElMessage.success(which === 'seedream' ? '已选用 Seedream 背景进入海报' : '已选用 SD 背景进入海报')
}

async function handleGenerate() {
  if (!form.category) { ElMessage.warning('请输入场景品类'); return }
  generating.value = true
  const tip = ElMessage({
    message: form.use_sd
      ? '正在生成背景（Seedream + SD），约 30～90 秒…'
      : '正在用豆包 Seedream 生成背景（未调用 SD），约 20～60 秒…',
    type: 'info',
    duration: 0,
  })
  try {
    const p = product.value
    const fd = new FormData()
    fd.append('category', form.category)
    fd.append('style', form.style)
    fd.append('color_hint', form.color_hint || p.color || '')
    fd.append('product_name', p.name || p.item_name || '')
    fd.append('brand', p.brand || '')
    fd.append('product_type', p.product_type || p.category_en || '')
    fd.append('scene_preset', form.scene_preset || '')
    fd.append('lighting', form.lighting || '')
    fd.append('mood', form.mood || '')
    fd.append('camera', form.camera || '')
    fd.append('extra_note', form.extra_note || '')
    fd.append('use_sd', form.use_sd ? '1' : '0')
    result.value = await request.post('/background/generate', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000,
    })
    preferred.value = 'seedream'
    appStore.setBackgroundResult(
      { bg_url: result.value.bg_url, enhanced_url: result.value.enhanced_url },
      form.style,
      'seedream',
    )
    ElMessage.success(result.value.cached ? '已命中缓存背景' : '背景生成完成，默认已选用 Seedream')
  } catch (e) {
    ElMessage.error(e?.message || '背景生成失败，请查看后端日志')
  } finally {
    tip.close()
    generating.value = false
  }
}

onMounted(async () => {
  try {
    const data = await request.get('/background/options')
    Object.assign(options, data || {})
    if (!options.styles?.length) {
      options.styles = await request.get('/background/styles')
    }
  } catch {
    try { options.styles = await request.get('/background/styles') } catch {}
  }
  form.category = suggestedCategory.value || appStore.category || ''
  if (product.value?.color) form.color_hint = product.value.color
  // 家具类默认给更贴切的场景
  const name = `${product.value.name || ''} ${product.value.product_type || ''}`.toLowerCase()
  if (/table|sofa|chair|家具|桌子|沙发|椅子|茶几/.test(name) && !form.scene_preset) {
    form.scene_preset = 'bright living room corner with empty floor space'
    form.style = 'scandi'
    form.mood = 'fresh and airy'
    form.lighting = 'soft daylight from large window'
  }
})
</script>

<style scoped>
.bg-page { padding: 0; }
.panel-title { display: flex; align-items: center; gap: 6px; font-weight: 600; }
.bg-form :deep(.el-form-item) { margin-bottom: 12px; }
.hint { margin: 4px 0 0; font-size: 12px; color: #888; line-height: 1.4; }
.result-img { width: 100%; border-radius: 4px; display: block; }
.img-label { text-align: center; font-size: 13px; color: #909399; margin-bottom: 8px; }
.pick-card {
  border: 2px solid transparent;
  border-radius: 10px;
  padding: 8px;
  cursor: pointer;
  transition: border-color .15s, box-shadow .15s;
}
.pick-card:hover { border-color: rgba(47,111,106,.35); }
.pick-card.active {
  border-color: #2f6f6a;
  box-shadow: 0 0 0 3px rgba(47,111,106,.15);
}
</style>
