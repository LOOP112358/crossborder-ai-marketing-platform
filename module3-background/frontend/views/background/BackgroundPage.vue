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
              <el-input v-model="form.category" placeholder="如：咖啡桌、平板保护套..." />
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

            <el-button type="primary" size="large" :loading="generating" block @click="handleGenerate">
              <el-icon><MagicStick /></el-icon> 用 Seedream 生成背景
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="15">
        <el-card v-if="result" shadow="never">
          <template #header>Seedream 生成结果</template>
          <img :src="result.bg_url" class="result-img" />
          <el-button type="primary" style="margin-top:12px" @click="pick">
            选用该背景进入海报
          </el-button>
          <el-descriptions :column="2" border size="small" style="margin-top:16px">
            <el-descriptions-item label="类别">{{ result.product_category }}</el-descriptions-item>
            <el-descriptions-item label="风格">{{ result.style }}</el-descriptions-item>
            <el-descriptions-item label="Prompt" :span="2">{{ result.prompt_used }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
        <el-empty v-else description="设置左侧选项后生成 Seedream 背景" />
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
})

const product = computed(() => appStore.selectedProduct || {})
const productHint = computed(() => {
  const p = product.value
  if (!p?.name && !p?.brand) return ''
  return [p.brand, p.name || p.item_name, p.product_type || p.category].filter(Boolean).join(' / ')
})

const suggestedCategory = computed(() => {
  const p = product.value
  const name = `${p.name || ''} ${p.item_name || ''} ${p.product_type || ''}`.toLowerCase()
  if (/tablet|kindle|ipad|sleeve|case/.test(name)) return '数码保护套 / 桌面陈列'
  if (/headphone|earbud/.test(name)) return '耳机配件'
  if (/coffee.?table|\btable\b/.test(name)) return '咖啡桌 / 客厅家具'
  if (p.category) return p.category
  return appStore.category || ''
})

function pick() {
  if (!result.value?.bg_url) return
  appStore.chooseBackground('seedream')
  ElMessage.success('已选用 Seedream 背景进入海报')
}

async function handleGenerate() {
  if (!form.category) {
    ElMessage.warning('请输入场景品类')
    return
  }
  generating.value = true
  const tip = ElMessage({
    message: '正在用豆包 Seedream 生成背景（lite 约 20～60 秒；未开通则回退 pro，约 1～2 分钟）…',
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
    result.value = await request.post('/background/generate', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 210000,
    })
    appStore.setBackgroundResult(
      { bg_url: result.value.bg_url, enhanced_url: result.value.enhanced_url || result.value.bg_url },
      form.style,
      'seedream',
    )
    ElMessage.success(result.value.cached ? '已命中缓存背景' : 'Seedream 背景生成完成')
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
  const name = `${product.value.name || ''} ${product.value.product_type || ''}`.toLowerCase()
  if (/table|sofa|chair|furniture/.test(name) && !form.scene_preset) {
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
.result-img { width: 100%; border-radius: 4px; display: block; }
</style>
