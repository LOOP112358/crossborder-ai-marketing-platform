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
              <el-button size="small" text type="danger" class="del-btn" @click.stop="deleteSession(s.id)">×</el-button>
            </div>
            <el-empty v-if="sessions.length === 0" description="还没有会话，点右上角新建" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="18">
        <el-card shadow="never" class="chat-panel" v-if="currentSessionId">
          <template #header>
            <div class="chat-head">
              <span>{{ currentTitle }}</span>
              <div class="chat-tools">
                <el-radio-group v-model="replyLang" size="small">
                  <el-radio-button label="auto">自动</el-radio-button>
                  <el-radio-button label="zh">中文</el-radio-button>
                  <el-radio-button label="en">EN</el-radio-button>
                </el-radio-group>
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

          <div class="message-area" ref="msgArea">
            <div v-for="m in messages" :key="m.id" class="msg-row" :class="m.role">
              <div class="msg-bubble">
                <div class="msg-text">{{ m.content }}</div>
                <div class="msg-meta">
                  <span v-if="m.role === 'assistant'">
                    <el-button size="small" text :type="m.feedback === 'like' ? 'primary' : ''" @click="feedback(m.id, 'like')">👍</el-button>
                    <el-button size="small" text :type="m.feedback === 'dislike' ? 'danger' : ''" @click="feedback(m.id, 'dislike')">👎</el-button>
                  </span>
                  <span class="msg-time">{{ formatTime(m.created_at) }}</span>
                </div>
              </div>
            </div>
            <div v-if="loading" class="msg-row assistant">
              <div class="msg-bubble typing">正在思考...</div>
            </div>
          </div>

          <div class="input-area">
            <el-input
              v-model="inputText"
              placeholder="问产品、售后、政策… 支持中英"
              size="large"
              @keyup.enter="sendMsg"
              :disabled="loading"
            >
              <template #append>
                <el-button :loading="loading" @click="sendMsg" type="primary">发送</el-button>
              </template>
            </el-input>
          </div>
        </el-card>

        <el-empty v-else description="选择或创建一个会话开始聊天" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const sessions = ref([])
const messages = ref([])
const currentSessionId = ref(null)
const inputText = ref('')
const loading = ref(false)
const uploading = ref(false)
const replyLang = ref('auto')
const msgArea = ref(null)

const currentTitle = computed(() => {
  const s = sessions.value.find((x) => x.id === currentSessionId.value)
  return s ? (s.doc_name || s.title || '新会话') : ''
})

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

async function loadSessions() {
  try {
    sessions.value = await request.get('/chat/sessions')
    if (!currentSessionId.value && sessions.value.length) {
      switchSession(sessions.value[0].id)
    }
  } catch {}
}

async function newSession() {
  try {
    const data = await request.post('/chat/sessions', { title: '新会话' })
    sessions.value.unshift(data)
    switchSession(data.id)
  } catch {}
}

function switchSession(id) {
  currentSessionId.value = id
  loadMessages()
}

async function loadMessages() {
  if (!currentSessionId.value) return
  try {
    messages.value = await request.get(`/chat/messages/${currentSessionId.value}`)
    scrollBottom()
  } catch {}
}

async function sendMsg() {
  if (!inputText.value.trim() || loading.value) return
  loading.value = true
  try {
    const data = await request.post('/chat/message', {
      session_id: currentSessionId.value,
      content: inputText.value,
      language: replyLang.value,
    })
    if (data?.user_message && data?.assistant_message) {
      messages.value.push(data.user_message, data.assistant_message)
    } else if (data?.content) {
      messages.value.push(
        { id: `u-${Date.now()}`, role: 'user', content: inputText.value, created_at: new Date().toISOString() },
        data,
      )
    }
    inputText.value = ''
    scrollBottom()
  } catch {} finally {
    loading.value = false
  }
}

async function onUploadDoc(uploadFile) {
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('session_id', String(currentSessionId.value))
    fd.append('file', uploadFile.raw)
    await request.post('/chat/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success('文档上传成功，索引已建立')
    loadSessions()
  } catch {} finally {
    uploading.value = false
  }
}

async function feedback(msgId, type) {
  try {
    await request.post('/chat/feedback', { message_id: msgId, feedback_type: type })
    messages.value = messages.value.map((m) => (m.id === msgId ? { ...m, feedback: type } : m))
  } catch {}
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
  } catch {}
}

onMounted(loadSessions)
</script>

<style scoped>
.chat-page { height: calc(100vh - 140px); }
.session-panel, .chat-panel { height: 100%; }
.session-list { max-height: calc(100vh - 260px); overflow-y: auto; }
.session-item {
  padding: 10px 12px;
  border-bottom: 1.5px dashed rgba(44, 58, 66, 0.15);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  position: relative;
  border-radius: 12px;
  margin-bottom: 4px;
}
.session-item:hover { background: rgba(47, 111, 106, 0.08); }
.session-item.active {
  background: rgba(47, 111, 106, 0.14);
  border-left: 3px solid var(--accent);
}
.session-doc { font-size: 12px; color: var(--ink-soft); }
.del-btn { position: absolute; right: 4px; top: 4px; }
.chat-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.chat-tools { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.message-area {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  min-height: 300px;
  max-height: calc(100vh - 360px);
}
.msg-row { display: flex; margin-bottom: 12px; }
.msg-row.user { justify-content: flex-end; }
.msg-bubble {
  max-width: 72%;
  padding: 10px 14px;
  border: 1.5px solid var(--line);
  border-radius: 18px 14px 16px 20px / 16px 18px 14px 18px;
  white-space: pre-wrap;
  word-break: break-word;
  background: #fff;
}
.msg-row.user .msg-bubble {
  background: rgba(47, 111, 106, 0.9);
  color: #fff;
  border-color: #1f4f4b;
}
.msg-bubble.typing { color: #888; font-style: italic; }
.msg-meta { display: flex; align-items: center; gap: 4px; margin-top: 4px; font-size: 12px; }
.msg-time { color: #999; margin-left: auto; }
.msg-row.user .msg-time { color: rgba(255,255,255,0.75); }
.input-area { margin-top: 12px; }
</style>
