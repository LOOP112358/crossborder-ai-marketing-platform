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
                  <div
                    v-if="m.role === 'assistant'"
                    class="msg-md"
                    v-html="renderMarkdown(m.content)"
                  />
                  <div v-else class="msg-text">{{ m.content }}</div>

                  <div v-if="m.products?.length" class="product-strip">
                    <div
                      v-for="p in m.products"
                      :key="p.item_id"
                      class="product-card"
                      :data-id="p.item_id"
                    >
                      <div class="product-thumb" :style="thumbStyle(p)">
                        <img
                          v-if="resolveProductImage(p)"
                          :src="resolveProductImage(p)"
                          :alt="p.name"
                          loading="lazy"
                          @error="onImgError($event, p)"
                        />
                        <span
                          v-show="!resolveProductImage(p)"
                          class="thumb-fallback"
                        >{{ (p.name || '?').slice(0, 1).toUpperCase() }}</span>
                      </div>
                      <div class="product-body">
                        <div class="product-name">{{ p.name }}</div>
                        <div class="product-brand" v-if="p.brand">{{ p.brand }}</div>
                        <div class="product-type" v-if="p.product_type">{{ p.product_type }}</div>
                        <ul class="product-highlights" v-if="p.highlights?.length">
                          <li v-for="(h, i) in p.highlights.slice(0, 2)" :key="i">{{ h }}</li>
                        </ul>
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
const brokenImgIds = ref(new Set())

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

function thumbStyle(p) {
  const i = Math.abs(String(p.item_id || p.name || '').split('').reduce((a, c) => a + c.charCodeAt(0), 0)) % THUMB_COLORS.length
  return { '--thumb': THUMB_COLORS[i] }
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
  const url = (p.image_url || '').trim()
  return url || demoImageForProduct(p)
}

function onImgError(e, p) {
  const img = e?.target
  if (!img) return
  if (!img.dataset.fallbackTried) {
    img.dataset.fallbackTried = '1'
    img.src = demoImageForProduct(p)
    return
  }
  img.style.display = 'none'
  const id = String(p?.item_id || '')
  if (!id) return
  const next = new Set(brokenImgIds.value)
  next.add(id)
  brokenImgIds.value = next
}

/** 修复模型常写的「** 文字**」（星号后空格导致无法加粗） */
function normalizeMarkdown(text) {
  let s = String(text || '')
  // **  content** / **content ** / ** content ** → **content**
  s = s.replace(/\*\*[ \t]+([^*\n]+?)\*\*/g, (_, inner) => `**${String(inner).trim()}**`)
  s = s.replace(/\*\*([^*\n]+?)[ \t]+\*\*/g, (_, inner) => `**${String(inner).trim()}**`)
  s = s.replace(/__[ \t]+([^_\n]+?)__/g, (_, inner) => `**${String(inner).trim()}**`)
  s = s.replace(/＊＊/g, '**')
  return s
}

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(normalizeMarkdown(text))
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

async function typewriterReveal(msgRef, fullText) {
  const text = fullText || ''
  msgRef.content = ''
  msgRef.streaming = true
  const step = Math.max(1, Math.floor(text.length / 80))
  for (let i = 0; i < text.length; i += step) {
    msgRef.content = text.slice(0, Math.min(i + step, text.length))
    if (i % (step * 4) === 0) scrollBottom()
    await sleep(18)
  }
  msgRef.content = text
  msgRef.streaming = false
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
    messages.value = (rows || []).map((m) => ({ ...m, products: m.products || [] }))
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
    })
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
    const assistant = {
      ...(data?.assistant_message || {
        id: `a-${Date.now()}`,
        role: 'assistant',
        created_at: new Date().toISOString(),
        language: 'auto',
      }),
      content: '',
      products: data?.products || [],
      streaming: true,
    }
    messages.value.push(assistant)
    await typewriterReveal(assistant, full)
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
.msg-md :deep(strong), .msg-md :deep(b) {
  color: #143834;
  font-weight: 700;
}
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
}
.product-card {
  flex: 0 0 168px;
  border: 1.5px solid rgba(44, 58, 66, 0.2);
  border-radius: 14px;
  background: #f7faf8;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.product-thumb {
  height: 96px;
  background: linear-gradient(145deg, var(--thumb, #2f6f6a), rgba(255,255,255,0.35));
  display: grid;
  place-items: center;
  position: relative;
}
.product-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.thumb-fallback {
  color: #fff;
  font-size: 28px;
  font-family: var(--font-display);
  font-weight: 600;
}
.product-body { padding: 8px 10px 10px; }
.product-name {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.product-brand { font-size: 11px; color: var(--ink-soft); margin-top: 2px; }
.product-type {
  display: inline-block;
  margin-top: 4px;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(47, 111, 106, 0.12);
  color: #2f6f6a;
}
.product-highlights {
  margin: 6px 0 0;
  padding-left: 14px;
  font-size: 11px;
  color: var(--ink-soft);
  line-height: 1.4;
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
