<template>
  <section class="matte-workspace">
    <input type="file" accept="image/jpeg,image/png,image/webp" @change="pick" />
    <button :disabled="!file || loading" @click="process">{{ loading ? '处理中…' : '开始智能抠图' }}</button>
    <div class="preview">
      <img v-if="originalPreview" :src="originalPreview" alt="原图" />
      <img v-if="result" class="checker" :src="apiBase + result.matted_url" alt="透明底结果" />
    </div>
    <div v-if="result">
      <strong>{{ result.category }} / {{ result.category_en }}</strong>
      <span>置信度 {{ Math.round(result.confidence * 100) }}%</span>
      <a :href="`${apiBase}/api/matte/download/${result.id}`">下载 PNG</a>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </section>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({ apiBase: { type: String, default: '' }, userId: { type: Number, default: 1 } })
const emit = defineEmits(['completed'])
const file = ref(null), originalPreview = ref(''), result = ref(null), loading = ref(false), error = ref('')
function pick(event) { file.value = event.target.files?.[0] || null; originalPreview.value = file.value ? URL.createObjectURL(file.value) : ''; result.value = null }
async function process() {
  loading.value = true; error.value = ''
  const form = new FormData(); form.append('file', file.value); form.append('user_id', String(props.userId)); form.append('edge_smoothing', '2')
  try {
    const response = await fetch(`${props.apiBase}/api/matte/process`, { method: 'POST', body: form })
    const body = await response.json(); if (!response.ok) throw new Error(body.detail || body.message)
    result.value = body.data
    // 父组件/Pinia在这里接收matted_url、category和attributes，传给成员3。
    emit('completed', body.data)
  } catch (e) { error.value = e.message || '处理失败' } finally { loading.value = false }
}
</script>

<style scoped>
.preview{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:20px 0}.preview img{width:100%;max-height:360px;object-fit:contain}.checker{background:#eee}.error{color:#c33}
</style>

