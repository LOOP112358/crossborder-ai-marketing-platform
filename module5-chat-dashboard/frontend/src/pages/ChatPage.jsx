import { useState, useEffect, useRef, useCallback } from 'react'
import { chatApi } from '../api/client'

/* ---- helpers ---- */
function formatTime(iso) {
  if (!iso) return ''
  // Backend stores UTC without Z, frontend temp msgs have Z; normalize
  const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z')
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  const pad = (n) => String(n).padStart(2, '0')
  const time = `${pad(d.getHours())}:${pad(d.getMinutes())}`
  return isToday ? time : `${d.getMonth() + 1}/${d.getDate()} ${time}`
}

function truncate(str, max = 30) {
  if (!str) return ''
  return str.length > max ? str.slice(0, max) + '…' : str
}

/* ================================================================
   ChatPage — 智能客服主页面
   ================================================================ */
export default function ChatPage() {
  /* state */
  const [sessions, setSessions] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [loadingSessions, setLoadingSessions] = useState(true)

  const messagesEnd = useRef(null)
  const fileInput = useRef(null)
  const inputRef = useRef(null)

  /* scroll to bottom */
  const scrollBottom = useCallback(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => { scrollBottom() }, [messages, scrollBottom])

  /* load sessions */
  const loadSessions = useCallback(async () => {
    try {
      setLoadingSessions(true)
      const res = await chatApi.listSessions()
      setSessions(res.data)
      return res.data
    } catch (e) {
      console.error('加载会话列表失败', e)
      return []
    } finally {
      setLoadingSessions(false)
    }
  }, [])

  useEffect(() => { loadSessions() }, [loadSessions])

  /* auto-select first session */
  useEffect(() => {
    if (!activeId && sessions.length > 0) {
      setActiveId(sessions[0].id)
    }
  }, [sessions, activeId])

  /* load messages when session changes */
  useEffect(() => {
    if (!activeId) return
    let cancelled = false
    chatApi.getMessages(activeId).then(res => {
      if (!cancelled) setMessages(res.data)
    }).catch(console.error)
    return () => { cancelled = true }
  }, [activeId])

  /* create session */
  const createSession = async () => {
    try {
      const res = await chatApi.createSession('新会话')
      setSessions(prev => [res.data, ...prev])
      setActiveId(res.data.id)
      setMessages([])
      inputRef.current?.focus()
    } catch (e) {
      console.error('创建会话失败', e)
    }
  }

  /* switch session */
  const switchSession = (id) => {
    setActiveId(id)
    setMessages([])
  }

  /* upload document */
  const handleUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file || !activeId) return

    // auto-create session if none
    let targetId = activeId
    if (!targetId) {
      try {
        const res = await chatApi.createSession(file.name.replace(/\.[^.]+$/, ''))
        setSessions(prev => [res.data, ...prev])
        targetId = res.data.id
        setActiveId(targetId)
      } catch (err) {
        console.error(err)
        return
      }
    }

    setUploading(true)
    try {
      await chatApi.uploadDoc(targetId, file)
      await loadSessions()
      // reload messages to show any system note
      chatApi.getMessages(targetId).then(res => setMessages(res.data)).catch(() => {})
    } catch (err) {
      alert('文档上传失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  /* send message */
  const sendMessage = async () => {
    const text = input.trim()
    if (!text || sending) return

    let targetId = activeId
    if (!targetId) {
      try {
        const res = await chatApi.createSession('新会话')
        setSessions(prev => [res.data, ...prev])
        targetId = res.data.id
        setActiveId(targetId)
      } catch (err) {
        console.error(err)
        return
      }
    }

    // optimistically add user message
    const tempUser = {
      id: Date.now(),
      session_id: targetId,
      role: 'user',
      content: text,
      language: 'auto',
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempUser])
    setInput('')
    setSending(true)

    try {
      const res = await chatApi.sendMessage(targetId, text, 'auto')
      // replace temp user + add real assistant
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== tempUser.id)
        return [...filtered, res.data.user_message, res.data.assistant_message]
      })
      // refresh session list (title may have changed)
      loadSessions()
    } catch (err) {
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== tempUser.id)
        return [...filtered, {
          ...tempUser,
          id: tempUser.id,
          content: text,
        }, {
          id: Date.now() + 1,
          session_id: targetId,
          role: 'assistant',
          content: '⚠️ 回复生成失败，请稍后重试。',
          language: 'auto',
          created_at: new Date().toISOString(),
        }]
      })
    } finally {
      setSending(false)
    }
  }

  /* feedback */
  const handleFeedback = async (msgId, type) => {
    try {
      await chatApi.feedback(msgId, type)
      setMessages(prev => prev.map(m =>
        m.id === msgId ? { ...m, feedback: type } : m
      ))
    } catch (e) {
      console.error('反馈提交失败', e)
    }
  }

  /* keyboard */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  /* ---- render ---- */
  const activeSession = sessions.find(s => s.id === activeId)

  return (
    <div className="chat-layout">
      {/* ---- sidebar ---- */}
      <aside className="chat-sidebar">
        <div className="sidebar-header">
          <h3>会话列表</h3>
          <button className="btn-new-session" onClick={createSession}>
            ＋ 新建会话
          </button>
        </div>

        <div className="session-list">
          {loadingSessions ? (
            <div className="loading-center" style={{ height: 80 }}>
              <span className="spinner" />
            </div>
          ) : sessions.length === 0 ? (
            <div style={{ padding: 20, textAlign: 'center', color: 'var(--gray-400)', fontSize: 13 }}>
              暂无会话，点击上方按钮创建
            </div>
          ) : (
            sessions.map(s => (
              <div
                key={s.id}
                className={`session-item${s.id === activeId ? ' active' : ''}`}
                onClick={() => switchSession(s.id)}
              >
                <div className="session-title">{s.title}</div>
                <div className="session-meta">
                  {s.doc_name ? `📎 ${s.doc_name}` : formatTime(s.created_at)}
                </div>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* ---- main chat ---- */}
      <section className="chat-main">
        {/* header */}
        <div className="chat-header">
          <h2>{activeSession ? activeSession.title : '智能客服'}</h2>
          <div className="chat-header-actions">
            {activeSession?.doc_name && (
              <span className="doc-badge">📄 {activeSession.doc_name}</span>
            )}
          </div>
        </div>

        {/* messages */}
        <div className="messages-area">
          {messages.length === 0 ? (
            <div className="empty-chat">
              <div className="icon">💬</div>
              <p>上传商品文档或直接提问，AI 客服将为您解答</p>
              <p style={{ fontSize: 12, color: 'var(--gray-300)' }}>
                支持 PDF / Word / TXT / Markdown
              </p>
            </div>
          ) : (
            messages.map((msg, i) => (
              <MessageBubble
                key={msg.id}
                msg={msg}
                onFeedback={(type) => handleFeedback(msg.id, type)}
              />
            ))
          )}

          {/* typing indicator */}
          {sending && (
            <div className="message-row assistant">
              <div className="msg-avatar">🤖</div>
              <div className="msg-bubble typing-bubble">
                <div className="typing-indicator">
                  <span /><span /><span />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEnd} />
        </div>

        {/* input */}
        <div className="chat-input-area">
          <div className="input-row">
            {/* hidden file input */}
            <input
              ref={fileInput}
              type="file"
              accept=".pdf,.doc,.docx,.txt,.md,.markdown"
              style={{ display: 'none' }}
              onChange={handleUpload}
            />
            <button
              className="btn-attach"
              onClick={() => fileInput.current?.click()}
              disabled={uploading}
              title="上传文档"
            >
              {uploading ? <span className="spinner" /> : '+'}
            </button>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入商品相关问题，Enter 发送，Shift+Enter 换行"
              rows={1}
              disabled={sending}
            />
            <button
              className="btn-send"
              onClick={sendMessage}
              disabled={!input.trim() || sending}
              title="发送"
            >➤</button>
          </div>
        </div>
      </section>
    </div>
  )
}

/* ================================================================
   MessageBubble — 单条消息组件
   ================================================================ */
function MessageBubble({ msg, onFeedback }) {
  const isUser = msg.role === 'user'

  return (
    <div className={`message-row ${msg.role}`}>
      <div className="msg-avatar">{isUser ? '👤' : '🤖'}</div>
      <div>
        <div className="msg-bubble">{msg.content}</div>
        <div className="msg-footer">
          <span className="msg-time">{formatTime(msg.created_at)}</span>

          {!isUser && (
            <>
              <button
                className={`btn-feedback${msg.feedback === 'like' ? ' active-like' : ''}`}
                onClick={() => onFeedback('like')}
                title="有帮助"
              >👍</button>
              <button
                className={`btn-feedback${msg.feedback === 'dislike' ? ' active-dislike' : ''}`}
                onClick={() => onFeedback('dislike')}
                title="没帮助"
              >👎</button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
