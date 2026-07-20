import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const chatApi = {
  createSession: (title) => api.post('/chat/sessions', { title }),
  listSessions: () => api.get('/chat/sessions'),
  getMessages: (sessionId) => api.get(`/chat/messages/${sessionId}`),
  uploadDoc: (sessionId, file) => {
    const form = new FormData()
    form.append('session_id', sessionId)
    form.append('file', file)
    return api.post('/chat/upload', form)
  },
  sendMessage: (sessionId, content, language) =>
    api.post('/chat/message', { session_id: sessionId, content, language }),
  feedback: (messageId, feedbackType) =>
    api.post('/chat/feedback', { message_id: messageId, feedback_type: feedbackType }),
}

export const dashboardApi = {
  stats: () => api.get('/dashboard/stats'),
  trend: () => api.get('/dashboard/trend'),
  advice: () => api.get('/dashboard/advice'),
  exportExcel: () => api.get('/dashboard/export/excel', { responseType: 'blob' }),
  exportPdf: () => api.get('/dashboard/export/pdf', { responseType: 'blob' }),
}

export default api
