<template>
  <div class="chat-page">
    <el-row :gutter="16" style="height:100%">
      <!-- 左侧：会话列表 -->
      <el-col :span="6">
        <el-card shadow="never" class="session-panel">
          <template #header>
            <span><el-icon><ChatDotRound /></el-icon> 会话列表</span>
            <el-button size="small" type="primary" style="float:right" @click="newSession">
              新建
            </el-button>
          </template>
          <div class="session-list">
            <div v-for="s in sessions" :key="s.id"
              class="session-item" :class="{ active: s.id === currentSessionId }"
              @click="switchSession(s.id)">
              <strong>{{ s.title }}</strong>
              <span class="session-doc" v-if="s.doc_name">{{ s.doc_name }}</span>
              <el-button size="small" text type="danger" class="del-btn"
                @click.stop="deleteSession(s.id)">×</el-button>
            </div>
            <el-empty v-if="sessions.length===0" description="暂无会话" />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：聊天区域 -->
      <el-col :span="18">
        <el-card shadow="never" class="chat-panel" v-if="currentSessionId">
          <template #header>
            <span>{{ currentTitle }}</span>
            <el-upload
              :auto-upload="false" :show-file-list="false"
              :on-change="onUploadDoc" accept=".pdf,.doc,.docx,.txt,.md"
              style="float:right"
            >
              <el-button size="small" :loading="uploading">
                <el-icon><Upload /></el-icon> 上传文档
              </el-button>
            </el-upload>
          </template>

          <!-- 消息列表 -->
          <div class="message-area" ref="msgArea">
            <div v-for="m in messages" :key="m.id"
              class="msg-row" :class="m.role">
              <div class="msg-bubble">
                <div class="msg-text">{{ m.content }}</div>
                <div class="msg-meta">
                  <span v-if="m.role==='assistant'">
                    <el-button size="small" text :type="m.feedback==='like'?'primary':''"
                      @click="feedback(m.id,'like')">👍</el-button>
                    <el-button size="small" text :type="m.feedback==='dislike'?'danger':''"
                      @click="feedback(m.id,'dislike')">👎</el-button>
                  </span>
                  <span class="msg-time">{{ m.created_at?.slice(11,19) || '' }}</span>
                </div>
              </div>
            </div>
            <div v-if="loading" class="msg-row assistant">
              <div class="msg-bubble typing">思考中...</div>
            </div>
          </div>

          <!-- 输入框 -->
          <div class="input-area">
            <el-input v-model="inputText" placeholder="输入问题，支持中英文..." size="large"
              @keyup.enter="sendMsg" :disabled="loading">
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
const msgArea = ref(null)

const currentTitle = computed(() => {
  const s = sessions.value.find(x => x.id === currentSessionId.value)
  return s ? (s.doc_name || s.title) : ''
})

function scrollBottom() {
  nextTick(() => {
    if (msgArea.value) msgArea.value.scrollTop = msgArea.value.scrollHeight
  })
}

async function loadSessions() {
  try { sessions.value = await request.get('/chat/sessions') } catch {}
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
      session_id: currentSessionId.value, content: inputText.value, language: 'zh'
    })
    messages.value.push(data.user_message, data.assistant_message)
    inputText.value = ''
    scrollBottom()
  } catch {} finally { loading.value = false }
}

async function onUploadDoc(uploadFile) {
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('session_id', String(currentSessionId.value))
    fd.append('file', uploadFile.raw)
    await request.post('/chat/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('文档上传成功，索引已建立')
    loadSessions()
  } catch {} finally { uploading.value = false }
}

async function feedback(msgId, type) {
  try { await request.post('/chat/feedback', { message_id: msgId, feedback_type: type }) }
  catch {}
  loadMessages()
}

async function deleteSession(id) {
  try {
    await ElMessageBox.confirm('确定删除此会话？', '提示', { type: 'warning' })
    await request.delete(`/chat/sessions/${id}`)
    if (currentSessionId.value === id) { currentSessionId.value = null; messages.value = [] }
    loadSessions()
  } catch {}
}

onMounted(loadSessions)
</script>

<style scoped>
.chat-page { height: calc(100vh - 120px); }
.session-panel { height: 100%; }
.session-list { max-height: calc(100vh - 240px); overflow-y: auto; }
.session-item {
  padding: 10px 12px; border-bottom: 1px solid #f0f0f0; cursor: pointer;
  display: flex; flex-direction: column; position: relative;
}
.session-item:hover { background: #f5f7fa; }
.session-item.active { background: #ecf5ff; border-left: 3px solid #409eff; }
.session-doc { font-size: 12px; color: #909399; }
.del-btn { position: absolute; right: 4px; top: 4px; font-size: 16px; }
.chat-panel { height: 100%; display: flex; flex-direction: column; }
.message-area {
  flex: 1; overflow-y: auto; padding: 12px;
  min-height: 300px; max-height: calc(100vh - 350px);
}
.msg-row { display: flex; margin-bottom: 12px; }
.msg-row.user { justify-content: flex-end; }
.msg-bubble {
  max-width: 70%; padding: 10px 14px; border-radius: 12px;
  white-space: pre-wrap; word-break: break-word;
}
.msg-row.user .msg-bubble { background: #409eff; color: #fff; border-bottom-right-radius: 4px; }
.msg-row.assistant .msg-bubble { background: #f0f2f5; color: #303133; border-bottom-left-radius: 4px; }
.msg-bubble.typing { color: #999; font-style: italic; }
.msg-meta { display: flex; align-items: center; gap: 4px; margin-top: 4px; font-size: 12px; }
.msg-time { color: #999; margin-left: auto; }
.msg-row.user .msg-time { color: rgba(255,255,255,0.7); }
.input-area { margin-top: 12px; }
</style>
