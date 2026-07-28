<template>
  <div class="chat-page sketch-shell">
    <el-row :gutter="16" style="height:100%">
      <el-col :span="6">
        <el-card shadow="never" class="session-panel">
          <template #header>
            <span>会话列表</span>
            <el-button size="small" type="primary" style="float:right" @click="newSession">新建</el-button>
          </template>
          <div class="session-list">
            <div
              v-for="s in sessions"
              :key="s.id"
              class="session-item"
              :class="{ active: s.id === currentSessionId }"
              @click="switchSession(s.id)"
            >
              <strong>{{ s.title || '新会话' }}</strong>
              <span class="session-doc" v-if="s.doc_name">📄 {{ s.doc_name }}</span>
              <el-button size="small" text type="danger" class="del-btn" @click.stop="deleteSession(s.id)">
                <el-icon :size="14"><Delete /></el-icon>
              </el-button>
            </div>
            <el-empty v-if="sessions.length === 0" description="还没有会话，点右上角新建" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="18">
        <el-card shadow="never" class="chat-panel">
          <template #header>
            <div class="chat-head">
              <span>{{ currentTitle || '新对话' }}</span>
              <div class="chat-tools">
                <el-upload
                  :auto-upload="false"
                  :show-file-list="false"
                  :on-change="onUploadDoc"
                  accept=".pdf,.doc,.docx,.txt,.md"
                >
                  <el-button size="small" :loading="uploading">
                    <el-icon><Upload /></el-icon> 上传文档
                  </el-button>
                </el-upload>
              </div>
            </div>
          </template>

          <div class="chat-body">
            <div class="message-area" ref="msgArea">
              <div v-for="m in messages" :key="m.id" class="msg-row" :class="m.role">
                <div class="msg-bubble">
                  <!-- 流式阶段用纯文本，避免 marked 反复解析半截 Markdown 卡死 UI -->
                  <div v-if="m.role === 'assistant' && m.streaming" class="msg-text msg-stream">{{ m.content }}<span class="caret">▍</span></div>
                  <div
                    v-else-if="m.role === 'assistant'"
                    class="msg-md"
                    v-html="renderMarkdown(m.content)"
                  />
                  <div v-else class="msg-text">{{ m.content }}</div>

                  <div v-if="m.products?.length" class="product-strip">
                    <div v-for="p in m.products" :key="p.item_id" class="product-card">
                      <div class="product-thumb" :style="thumbStyle(p)">
                        <img
                          v-if="resolveProductImage(p)"
                          :src="resolveProductImage(p)"
                          :alt="productDisplayName(p)"
                          loading="lazy"
                          @error="onImgError($event, p)"
                        />
                        <span v-else class="thumb-fallback">{{ productInitial(p) }}</span>
                      </div>
                      <div class="product-body">
                        <div class="product-name">{{ productDisplayName(p) }}</div>
                        <div class="product-brand">{{ productBrandLabel(p) }}</div>
                        <div class="product-type" v-if="productTypeLabel(p)">{{ productTypeLabel(p) }}</div>
                      </div>
                    </div>
                  </div>

                  <div class="msg-meta">
                    <span v-if="m.role === 'assistant' && !m.streaming" class="fb-btns">
                      <button
                        type="button"
                        class="fb-btn"
                        :class="{ on: m.feedback === 'like' }"
                        title="有帮助"
                        @click="feedback(m.id, 'like')"
                      >👍</button>
                      <button
                        type="button"
                        class="fb-btn"
                        :class="{ on: m.feedback === 'dislike' }"
                        title="没帮助"
                        @click="feedback(m.id, 'dislike')"
                      >👎</button>
                    </span>
                    <span class="msg-time">{{ formatTime(m.created_at) }}</span>
                  </div>
                </div>
              </div>
              <div v-if="loading" class="msg-row assistant">
                <div class="msg-bubble typing">
                  <span class="dot" /><span class="dot" /><span class="dot" />
                  <span class="typing-label">正在生成回复</span>
                </div>
              </div>
            </div>

            <div class="composer">
              <div class="quick-prompts" v-if="!loading">
                <button
                  v-for="q in quickPrompts"
                  :key="q"
                  type="button"
                  class="chip"
                  @click="useQuickPrompt(q)"
                >{{ q }}</button>
              </div>
              <div class="input-area">
                <el-input
                  v-model="inputText"
                  placeholder="用什么语言问，就用什么语言答…"
                  size="large"
                  @keyup.enter="sendMsg"
                  :disabled="loading"
                >
                  <template #append>
                    <el-button :loading="loading" @click="sendMsg" type="primary">发送</el-button>
                  </template>
                </el-input>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import request from '@/api/request'

marked.setOptions({ breaks: true, gfm: true })

const sessions = ref([])
const messages = ref([])
const currentSessionId = ref(null)
const inputText = ref('')
const loading = ref(false)
const uploading = ref(false)
const msgArea = ref(null)

const quickPrompts = [
  '推荐几款蓝牙耳机',
  '有什么运动鞋？',
  '保温杯保冷多久？',
  '还有别的吗',
]

const currentTitle = computed(() => {
  const s = sessions.value.find((x) => x.id === currentSessionId.value)
  return s ? (s.doc_name || s.title || '新会话') : ''
})

const THUMB_COLORS = ['#2f6f6a', '#c45c26', '#4a6fa5', '#b7791f', '#3d7a52']
const brokenImgIds = ref(new Set())
const PRODUCT_CACHE_KEY = 'chat_msg_products_v1'

function readProductCache() {
  try {
    return JSON.parse(sessionStorage.getItem(PRODUCT_CACHE_KEY) || '{}') || {}
  } catch {
    return {}
  }
}

function cacheMessageProducts(messageId, products) {
  if (!messageId || !products?.length) return
  try {
    const all = readProductCache()
    all[String(messageId)] = normalizeProductList(products)
    const keys = Object.keys(all)
    if (keys.length > 200) keys.slice(0, keys.length - 200).forEach((k) => delete all[k])
    sessionStorage.setItem(PRODUCT_CACHE_KEY, JSON.stringify(all))
  } catch {
    /* ignore quota */
  }
}

function cachedProductsFor(messageId) {
  if (!messageId) return []
  const hit = readProductCache()[String(messageId)]
  return Array.isArray(hit) ? normalizeProductList(hit) : []
}

function pickProducts(payload) {
  const fromAsst = payload?.assistant_message?.products
  if (Array.isArray(fromAsst) && fromAsst.length) return normalizeProductList(fromAsst)
  if (Array.isArray(payload?.products) && payload.products.length) return normalizeProductList(payload.products)
  return []
}

function normalizeImageUrl(url) {
  const u = String(url || '').trim()
  if (!u) return ''
  if (/^https?:\/\//i.test(u) || u.startsWith('data:') || u.startsWith('/')) return u
  return `/${u}`
}

function thumbStyle(p) {
  const key = productDisplayName(p) || p?.item_id || ''
  const i = Math.abs(String(key).split('').reduce((a, c) => a + c.charCodeAt(0), 0)) % THUMB_COLORS.length
  return { '--thumb': THUMB_COLORS[i] }
}

function productDisplayName(p) {
  const raw = [p?.name, p?.name_en, p?.product_type, p?.brand, '商品']
    .map((x) => String(x || '').trim())
    .find(Boolean)
  return raw || '商品'
}

function productBrandLabel(p) {
  const brand = String(p?.brand || '').trim()
  if (brand) return brand
  const type = String(p?.product_type || '').trim()
  if (type && type !== productDisplayName(p)) return type
  return '商品'
}

function productTypeLabel(p) {
  const type = String(p?.product_type || '').trim()
  if (!type) return ''
  if (type === productDisplayName(p) || type === productBrandLabel(p)) return ''
  return type
}

function productInitial(p) {
  const name = productDisplayName(p)
  return (name || '?').slice(0, 1).toUpperCase()
}

function normalizeProductCard(p) {
  if (!p || typeof p !== 'object') return p
  return {
    ...p,
    name: productDisplayName(p),
    brand: String(p.brand || '').trim(),
    product_type: String(p.product_type || '').trim(),
  }
}

function normalizeProductList(list) {
  return (Array.isArray(list) ? list : []).map(normalizeProductCard).filter(Boolean)
}

function demoImageForProduct(p) {
  const pt = String(p?.product_type || '').toUpperCase()
  let name = 'product.svg'
  if (/HEADPHONE|EARPHONE|EARBUD|AUDIO|ELECTRONIC/.test(pt)) name = 'headphones.svg'
  else if (/SHOE|FOOTWEAR|SANDAL|BOOT|SNEAKER/.test(pt)) name = 'shoes.svg'
  else if (/BOTTLE|KITCHEN|CUP|MUG/.test(pt)) name = 'bottle.svg'
  else if (/APPAREL|SHIRT|DRESS|CLOTH/.test(pt)) name = 'apparel.svg'
  else if (/HOME|LAMP|FURNITURE|SOFA|CHAIR/.test(pt)) name = 'home.svg'
  return `/static/demo-products/${name}`
}

function resolveProductImage(p) {
  if (!p || brokenImgIds.value.has(String(p.item_id))) return ''
  return normalizeImageUrl(p.image_url) || demoImageForProduct(p)
}

function onImgError(e, p) {
  const img = e?.target
  if (!img) return
  if (!img.dataset.fallbackTried) {
    img.dataset.fallbackTried = '1'
    img.src = demoImageForProduct(p)
    return
  }
  brokenImgIds.value.add(String(p?.item_id || ''))
  img.style.display = 'none'
}

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(String(text))
  } catch {
    return String(text).replace(/</g, '&lt;')
  }
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(String(iso).endsWith('Z') ? iso : `${iso}Z`)
  if (Number.isNaN(d.getTime())) return String(iso).slice(11, 19)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function scrollBottom() {
  nextTick(() => {
    if (msgArea.value) msgArea.value.scrollTop = msgArea.value.scrollHeight
  })
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

function patchMessage(messageId, partial) {
  const i = messages.value.findIndex((m) => m.id === messageId)
  if (i < 0) return
  // 必须替换数组项，不能改 push 前的裸对象——否则 Vue 不触发重绘，字会「卡死」
  messages.value[i] = { ...messages.value[i], ...partial }
}

async function typewriterReveal(messageId, fullText) {
  const text = fullText || ''
  patchMessage(messageId, { content: '', streaming: true })
  if (!text) {
    patchMessage(messageId, { content: '', streaming: false })
    return
  }
  const step = Math.max(1, Math.ceil(text.length / 60))
  for (let i = 0; i < text.length; i += step) {
    patchMessage(messageId, {
      content: text.slice(0, Math.min(i + step, text.length)),
      streaming: true,
    })
    if (i === 0 || i % (step * 3) === 0) scrollBottom()
    await sleep(14)
  }
  patchMessage(messageId, { content: text, streaming: false })
  scrollBottom()
}

function useQuickPrompt(q) {
  inputText.value = q
  sendMsg()
}

async function loadSessions() {
  try {
    sessions.value = await request.get('/chat/sessions')
    if (!currentSessionId.value && sessions.value.length) {
      switchSession(sessions.value[0].id)
    }
  } catch (e) {
    console.error(e)
  }
}

async function newSession() {
  try {
    const data = await request.post('/chat/sessions', { title: '新会话' })
    sessions.value.unshift(data)
    switchSession(data.id)
  } catch (e) {
    console.error(e)
  }
}

function switchSession(id) {
  currentSessionId.value = id
  loadMessages()
}

async function loadMessages() {
  if (!currentSessionId.value) return
  try {
    const rows = await request.get(`/chat/messages/${currentSessionId.value}`)
    messages.value = (rows || []).map((m) => {
      const fromApi = Array.isArray(m.products) && m.products.length ? normalizeProductList(m.products) : []
      const products = fromApi.length ? fromApi : cachedProductsFor(m.id)
      if (products.length) cacheMessageProducts(m.id, products)
      return { ...m, products }
    })
    scrollBottom()
  } catch (e) {
    console.error(e)
  }
}

async function sendMsg() {
  if (!inputText.value.trim() || loading.value) return
  loading.value = true
  const text = inputText.value.trim()
  inputText.value = ''
  try {
    if (!currentSessionId.value) {
      const created = await request.post('/chat/sessions', { title: '新会话' })
      sessions.value.unshift(created)
      currentSessionId.value = created.id
    }
    const data = await request.post('/chat/message', {
      session_id: currentSessionId.value,
      content: text,
      language: 'auto',
    }, { timeout: 90000 })
    if (data?.session_title) {
      const sid = data.session_id || currentSessionId.value
      sessions.value = sessions.value.map((s) =>
        s.id === sid ? { ...s, title: data.session_title } : s,
      )
    }
    if (data?.user_message) {
      messages.value.push({ ...data.user_message, products: [] })
    } else {
      messages.value.push({
        id: `u-${Date.now()}`,
        role: 'user',
        content: text,
        created_at: new Date().toISOString(),
        products: [],
      })
    }
    scrollBottom()
    loading.value = false

    const full = data?.assistant_message?.content || data?.content || ''
    const products = pickProducts(data)
    const assistantId = data?.assistant_message?.id || `a-${Date.now()}`
    const assistant = {
      ...(data?.assistant_message || {
        role: 'assistant',
        created_at: new Date().toISOString(),
        language: 'auto',
      }),
      id: assistantId,
      content: '',
      products,
      streaming: true,
    }
    cacheMessageProducts(assistantId, products)
    messages.value.push(assistant)
    // 商品卡先展示；正文通过响应式 patch 打字，避免图出来后字停住
    await typewriterReveal(assistantId, full)
  } catch (e) {
    console.error(e)
    loading.value = false
  }
}

async function onUploadDoc(uploadFile) {
  uploading.value = true
  try {
    if (!currentSessionId.value) {
      const created = await request.post('/chat/sessions', {
        title: uploadFile.name?.slice(0, 40) || '文档会话',
      })
      sessions.value.unshift(created)
      currentSessionId.value = created.id
    }
    const fd = new FormData()
    fd.append('session_id', String(currentSessionId.value))
    fd.append('file', uploadFile.raw)
    const res = await request.post('/chat/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success(
      res?.chunks != null ? `文档上传成功，已索引 ${res.chunks} 段` : '文档上传成功，索引已建立',
    )
    loadSessions()
  } catch (e) {
    console.error(e)
  } finally {
    uploading.value = false
  }
}

async function feedback(msgId, type) {
  const id = Number(msgId)
  if (!Number.isFinite(id)) {
    ElMessage.warning('消息还未保存完成，请稍后再试')
    return
  }
  // 先本地高亮，避免“点了没反应”
  const prev = messages.value.find((m) => Number(m.id) === id)?.feedback
  messages.value = messages.value.map((m) =>
    Number(m.id) === id ? { ...m, feedback: type } : m,
  )
  try {
    await request.post('/chat/feedback', { message_id: id, feedback_type: type })
    ElMessage.success(type === 'like' ? '已点赞' : '已点踩')
  } catch (e) {
    console.error(e)
    // 回滚
    messages.value = messages.value.map((m) =>
      Number(m.id) === id ? { ...m, feedback: prev } : m,
    )
  }
}

async function deleteSession(id) {
  try {
    await ElMessageBox.confirm('确定删除此会话？', '提示', { type: 'warning' })
    await request.delete(`/chat/sessions/${id}`)
    if (currentSessionId.value === id) {
      currentSessionId.value = null
      messages.value = []
    }
    loadSessions()
  } catch (e) {
    /* cancel */
  }
}

onMounted(loadSessions)
</script>

<style scoped>
.chat-page {
  height: calc(100vh - 140px);
  min-height: 480px;
}
.chat-page :deep(.el-row),
.chat-page :deep(.el-col) {
  height: 100%;
}
.session-panel,
.chat-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.session-panel :deep(.el-card__body),
.chat-panel :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 12px 14px;
}
.session-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
.session-item {
  padding: 8px 10px;
  border-bottom: 1.5px dashed rgba(44, 58, 66, 0.15);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  position: relative;
  border-radius: 12px;
  margin-bottom: 4px;
  gap: 2px;
}
.session-item strong {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
  padding-right: 22px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.session-item:hover { background: rgba(47, 111, 106, 0.08); }
.session-item.active {
  background: rgba(47, 111, 106, 0.14);
  border-left: 3px solid var(--accent);
}
.session-doc { font-size: 11px; color: var(--ink-soft); }
.del-btn { position: absolute; right: 4px; top: 4px; }
.chat-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.chat-tools { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }

.chat-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.message-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 4px 2px 12px;
}
.composer {
  flex-shrink: 0;
  padding-top: 10px;
  border-top: 1.5px dashed rgba(44, 58, 66, 0.15);
  background: #fff;
}
.msg-row { display: flex; margin-bottom: 14px; }
.msg-row.user { justify-content: flex-end; }
.msg-bubble {
  max-width: 78%;
  padding: 10px 14px;
  border: 1.5px solid var(--line);
  border-radius: 18px 14px 16px 20px / 16px 18px 14px 18px;
  word-break: break-word;
  background: #fff;
}
.msg-row.user .msg-bubble {
  background: rgba(47, 111, 106, 0.9);
  color: #fff;
  border-color: #1f4f4b;
  white-space: pre-wrap;
}
.msg-text { white-space: pre-wrap; }
.msg-stream { min-height: 1.2em; }
.msg-stream .caret {
  display: inline-block;
  margin-left: 1px;
  color: #2f6f6a;
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  50% { opacity: 0; }
}
.msg-md :deep(p) { margin: 0 0 0.55em; line-height: 1.65; }
.msg-md :deep(p:last-child) { margin-bottom: 0; }
.msg-md :deep(ul), .msg-md :deep(ol) {
  margin: 0.35em 0 0.55em;
  padding-left: 1.25em;
}
.msg-md :deep(li) { margin: 0.2em 0; line-height: 1.55; }
.msg-md :deep(h1), .msg-md :deep(h2), .msg-md :deep(h3) {
  margin: 0.4em 0 0.35em;
  font-family: var(--font-display);
  font-size: 1.05em;
  font-weight: 600;
}
.msg-md :deep(strong) { color: #1f4f4b; font-weight: 650; }
.msg-md :deep(code) {
  background: rgba(44, 58, 66, 0.08);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.92em;
}

.product-strip {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 10px 0 4px;
  margin-top: 6px;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
}
.product-card {
  flex: 0 0 228px;
  width: 228px;
  height: 96px;
  box-sizing: border-box;
  border: 1.5px solid rgba(44, 58, 66, 0.2);
  border-radius: 14px;
  background: #f7faf8;
  overflow: hidden;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0;
  position: relative;
}
.product-thumb {
  flex: 0 0 80px;
  width: 80px;
  height: 80px;
  margin: 0 0 0 8px;
  border-radius: 10px;
  background: linear-gradient(145deg, var(--thumb, #2f6f6a), rgba(255,255,255,0.35));
  display: grid;
  place-items: center;
  overflow: hidden;
  position: relative;
  z-index: 0;
}
.product-thumb img {
  width: 80px;
  height: 80px;
  max-width: 80px;
  max-height: 80px;
  object-fit: cover;
  object-position: center;
  display: block;
}
.thumb-fallback {
  color: #fff;
  font-size: 22px;
  font-family: var(--font-display);
  font-weight: 600;
  line-height: 1;
}
.product-body {
  flex: 1 1 auto;
  min-width: 0;
  height: 100%;
  padding: 10px 12px 10px 10px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  position: relative;
  z-index: 1;
  background: #f7faf8;
}
.product-name {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--ink, #2c3a42);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}
.product-brand {
  font-size: 11px;
  color: var(--ink-soft);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.product-type {
  align-self: flex-start;
  max-width: 100%;
  margin-top: 2px;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(47, 111, 106, 0.12);
  color: #2f6f6a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.msg-bubble.typing {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--ink-soft);
  min-width: 120px;
}
.typing-label { font-size: 12px; }
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #2f6f6a;
  animation: bounce 1.2s ease-in-out infinite;
}
.dot:nth-child(2) { animation-delay: 0.15s; }
.dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.45; }
  40% { transform: translateY(-5px); opacity: 1; }
}

.msg-meta { display: flex; align-items: center; gap: 4px; margin-top: 6px; font-size: 12px; }
.msg-time { color: #999; margin-left: auto; }
.msg-row.user .msg-time { color: rgba(255,255,255,0.75); }
.fb-btns { display: inline-flex; gap: 4px; }
.fb-btn {
  border: 1.5px solid rgba(44, 58, 66, 0.18);
  background: #fff;
  border-radius: 999px;
  width: 30px;
  height: 28px;
  cursor: pointer;
  line-height: 1;
  font-size: 14px;
  opacity: 0.7;
  transition: 0.15s ease;
}
.fb-btn:hover { opacity: 1; border-color: #2f6f6a; }
.fb-btn.on {
  opacity: 1;
  border-color: #2f6f6a;
  background: rgba(47, 111, 106, 0.12);
  transform: scale(1.06);
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 8px;
}
.chip {
  border: 1.5px solid rgba(44, 58, 66, 0.25);
  background: #fff;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 12px;
  cursor: pointer;
  color: var(--ink);
}
.chip:hover {
  border-color: #2f6f6a;
  background: rgba(47, 111, 106, 0.08);
}
.input-area { margin-top: 0; }
</style>
