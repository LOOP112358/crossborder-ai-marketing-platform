<template>
  <div class="bg-page sketch-shell">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <span class="panel-title"><el-icon><PictureFilled /></el-icon> 背景生成</span>
          </template>
          <el-form label-position="top">
            <el-form-item label="商品类别">
              <el-input v-model="form.category" placeholder="如：运动鞋、耳机..."
                :disabled="autoCategory" />
              <el-button v-if="appStore.category" size="small" type="success" style="margin-top:8px"
                @click="useCategory">
                从抠图结果填入：{{ appStore.category }}
              </el-button>
            </el-form-item>
            <el-form-item label="风格">
              <el-select v-model="form.style" style="width:100%">
                <el-option v-for="s in styles" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="色调偏好">
              <el-input v-model="form.color_hint" placeholder="如：蓝色、暖色调、暗色..." />
            </el-form-item>
            <el-button type="primary" size="large" :loading="generating" block @click="handleGenerate">
              <el-icon><MagicStick /></el-icon> 生成背景
            </el-button>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card v-if="result" shadow="never">
          <template #header>生成结果</template>
          <el-row :gutter="16">
            <el-col :span="12">
              <p class="img-label">原始背景 (1024×1024)</p>
              <img :src="result.bg_url" class="result-img" />
            </el-col>
            <el-col :span="12">
              <p class="img-label">超分增强 (2048×2048)</p>
              <img :src="result.enhanced_url" class="result-img" />
            </el-col>
          </el-row>
          <el-descriptions :column="2" border size="small" style="margin-top:16px">
            <el-descriptions-item label="类别">{{ result.product_category }}</el-descriptions-item>
            <el-descriptions-item label="风格">{{ result.style }}</el-descriptions-item>
            <el-descriptions-item label="Prompt" :span="2">{{ result.prompt_used }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
        <el-empty v-else description="选择商品类别 → 生成背景" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAppStore } from '@/store/useAppStore'
import request from '@/api/request'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const generating = ref(false)
const result = ref(null)
const autoCategory = ref(false)
const styles = ref([])

const form = reactive({ category: '', style: 'default', color_hint: '' })

function useCategory() {
  form.category = appStore.category
  autoCategory.value = true
}

async function handleGenerate() {
  if (!form.category) { ElMessage.warning('请输入商品类别'); return }
  generating.value = true
  try {
    const fd = new FormData()
    fd.append('category', form.category)
    fd.append('style', form.style)
    fd.append('color_hint', form.color_hint)
    result.value = await request.post('/background/generate', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    appStore.setBackgroundResult(result.value.enhanced_url, form.style)
    ElMessage.success('背景生成完成')
  } catch {} finally { generating.value = false }
}

onMounted(async () => {
  try { styles.value = await request.get('/background/styles') } catch {}
  if (appStore.category) useCategory()
})
</script>

<style scoped>
.bg-page { padding: 0; }
.panel-title { display: flex; align-items: center; gap: 6px; font-weight: 600; }
.result-img { width: 100%; border-radius: 4px; }
.img-label { text-align: center; font-size: 13px; color: #909399; margin-bottom: 8px; }
</style>
