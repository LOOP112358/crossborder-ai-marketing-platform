<template>
  <div class="video-page sketch-shell">
    <div class="page-head sketch-card">
      <div>
        <h1>视频脚本试运营</h1>
        <p class="subtitle">
          先生成可执行的口播稿和分镜表，不生成视频文件。可带入智能选品上下文，结果会保存到“我的作品”。
        </p>
      </div>
      <el-button plain @click="$router.push('/my-works?tab=video')">我的视频脚本</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card shadow="never" class="form-card">
          <h3>生成参数</h3>
          <el-alert
            v-if="productLabel"
            type="success"
            :closable="false"
            show-icon
            :title="`已带入商品：${productLabel}`"
            style="margin-bottom: 12px"
          />
          <el-alert
            v-else
            type="info"
            :closable="false"
            show-icon
            title="可先在智能选品中心选择商品，也可以手动填写商品名"
            style="margin-bottom: 12px"
          />

          <label>商品名称</label>
          <el-input v-model="form.product_name" placeholder="例如：便携榨汁杯" />

          <label>卖点 / 特征</label>
          <el-input
            v-model="form.product_features"
            type="textarea"
            :rows="3"
            placeholder="材质、功能、使用场景等，用逗号或分号分隔"
          />

          <label>平台</label>
          <el-select v-model="form.platform" style="width: 100%">
            <el-option label="TikTok" value="TikTok" />
            <el-option label="Instagram Reels" value="Instagram" />
            <el-option label="YouTube Shorts" value="YouTube" />
            <el-option label="小红书" value="Xiaohongshu" />
          </el-select>

          <label>语言</label>
          <el-select v-model="form.language" style="width: 100%">
            <el-option label="中文" value="zh" />
            <el-option label="English" value="en" />
            <el-option label="日本語" value="ja" />
            <el-option label="한국어" value="ko" />
            <el-option label="Español" value="es" />
          </el-select>

          <label>时长（秒）</label>
          <el-slider v-model="form.duration_sec" :min="10" :max="60" :step="5" show-stops />

          <label>风格</label>
          <el-select v-model="form.style" style="width: 100%">
            <el-option label="活泼种草" value="casual" />
            <el-option label="专业商务" value="professional" />
            <el-option label="情感共鸣" value="emotional" />
            <el-option label="幽默风趣" value="humorous" />
          </el-select>

          <el-button
            type="primary"
            style="width: 100%; margin-top: 16px"
            :loading="loading"
            @click="onGenerate"
          >
            生成脚本 + 分镜
          </el-button>
          <p class="hint">
            试运营说明：当前输出文字策划方案，便于先验证短视频选题、口播和分镜需求。
          </p>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card shadow="never" class="result-card">
          <div class="result-head">
            <h3>生成结果</h3>
            <el-button v-if="result" size="small" @click="copyAll">复制全文</el-button>
          </div>

          <el-empty v-if="!result" description="填写左侧参数后生成" />
          <template v-else>
            <div class="block">
              <div class="label">开头钩子</div>
              <p>{{ result.hook }}</p>
            </div>
            <div class="block">
              <div class="label">完整口播</div>
              <p class="voice">{{ result.voiceover }}</p>
            </div>
            <div class="block">
              <div class="label">行动号召</div>
              <p>{{ result.cta }}</p>
            </div>
            <div class="block">
              <div class="label">标签</div>
              <p>{{ result.hashtags }}</p>
            </div>

            <h4>分镜表（{{ (result.storyboard || []).length }} 镜）</h4>
            <el-timeline>
              <el-timeline-item
                v-for="shot in result.storyboard || []"
                :key="shot.idx"
                :timestamp="`${shot.start_sec}s - ${shot.end_sec}s`"
                placement="top"
              >
                <div class="shot">
                  <strong>画面：</strong>{{ shot.visual }}
                  <div><strong>旁白：</strong>{{ shot.voiceover }}</div>
                  <div v-if="shot.on_screen_text"><strong>字幕：</strong>{{ shot.on_screen_text }}</div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/store/useAppStore'
import { generateVideoScript } from '@/api/video'

const appStore = useAppStore()
const loading = ref(false)
const result = ref(null)

const form = reactive({
  product_name: '',
  product_features: '',
  product_id: null,
  platform: 'TikTok',
  language: 'zh',
  duration_sec: 15,
  style: 'casual',
})

const productLabel = computed(() => {
  const product = appStore.selectedProduct
  if (!product) return ''
  return [product.brand, product.name || product.item_name].filter(Boolean).join(' / ').slice(0, 64)
})

function hydrateFromStore() {
  try {
    const raw = sessionStorage.getItem('video_reuse')
    if (raw) {
      const data = JSON.parse(raw)
      sessionStorage.removeItem('video_reuse')
      Object.assign(form, {
        product_name: data.product_name || '',
        product_features: data.product_features || '',
        product_id: data.product_id || null,
        platform: data.platform || 'TikTok',
        language: data.language || 'zh',
        duration_sec: data.duration_sec || 15,
        style: data.style || 'casual',
      })
      return
    }
  } catch {
    // Ignore malformed session data.
  }

  const product = appStore.selectedProduct
  if (!product) return
  form.product_id = product.id || null
  form.product_name = product.name || product.item_name || product.label || form.product_name
  const featureList = Array.isArray(product.feature_list) ? product.feature_list.join('，') : ''
  form.product_features = featureList || product.features || product.bullet_points || form.product_features
}

async function onGenerate() {
  if (!form.product_name.trim()) {
    ElMessage.warning('请填写商品名称')
    return
  }
  loading.value = true
  try {
    const data = await generateVideoScript({ ...form, product_name: form.product_name.trim() })
    result.value = data
    ElMessage.success('已生成并保存到“我的作品 / 视频脚本”')
  } catch (error) {
    ElMessage.error(error?.message || '生成失败')
  } finally {
    loading.value = false
  }
}

async function copyAll() {
  if (!result.value) return
  const shots = (result.value.storyboard || [])
    .map((shot) => `[${shot.start_sec}-${shot.end_sec}s] ${shot.visual}\n旁白：${shot.voiceover}\n字幕：${shot.on_screen_text || ''}`)
    .join('\n\n')
  const text = [
    `钩子：${result.value.hook}`,
    `口播：${result.value.voiceover}`,
    `CTA：${result.value.cta}`,
    `标签：${result.value.hashtags}`,
    '',
    '分镜：',
    shots,
  ].join('\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

onMounted(hydrateFromStore)
</script>

<style scoped>
.video-page { max-width: 1200px; }
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 18px;
  margin-bottom: 14px;
}
.page-head h1 { margin: 0 0 6px; font-size: 22px; }
.subtitle { margin: 0; color: #64748b; font-size: 13px; line-height: 1.5; }
.form-card label,
.result-card .label {
  display: block;
  margin: 12px 0 6px;
  font-size: 13px;
  color: #475569;
  font-weight: 600;
}
.hint { margin-top: 10px; color: #94a3b8; font-size: 12px; line-height: 1.5; }
.result-head { display: flex; justify-content: space-between; align-items: center; }
.block { margin-bottom: 14px; }
.block p { margin: 0; line-height: 1.6; color: #1e293b; }
.voice { white-space: pre-wrap; }
.shot { line-height: 1.55; color: #334155; font-size: 13px; }
h3,
h4 { margin: 0 0 8px; color: #0f172a; }
</style>
