import request from './request'

export function getBackgroundStyles() {
  return request.get('/background/styles')
}

export function generateBackground(formData) {
  return request.post('/background/generate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getBackgroundHistory(page = 1, pageSize = 20) {
  return request.get('/background/history', { params: { page, page_size: pageSize } })
}

export function getBackgroundCache(category, style) {
  return request.get(`/background/cache/${encodeURIComponent(category)}/${encodeURIComponent(style)}`)
}
