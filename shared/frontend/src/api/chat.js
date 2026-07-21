import request from './request'

export function listSessions() {
  return request.get('/chat/sessions')
}

export function createSession(payload) {
  return request.post('/chat/sessions', payload)
}

export function deleteSession(id) {
  return request.delete(`/chat/sessions/${id}`)
}

export function getMessages(sessionId) {
  return request.get(`/chat/messages/${sessionId}`)
}

export function sendMessage(payload) {
  return request.post('/chat/message', payload)
}

export function uploadDoc(formData) {
  return request.post('/chat/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function submitFeedback(payload) {
  return request.post('/chat/feedback', payload)
}
