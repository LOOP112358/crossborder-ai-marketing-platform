import request from './request'

export function uploadImage(file) {
  const fd = new FormData()
  fd.append('file', file)
  return request.post('/poster/upload/image', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getTemplates() {
  return request.get('/poster/templates')
}

export function composePoster(params) {
  return request.post('/poster/compose', params)
}

export function getPosterHistory(page = 1, pageSize = 20) {
  return request.get('/poster/history', { params: { page, page_size: pageSize } })
}

export function toggleFavorite(posterId) {
  return request.post(`/poster/favorite/${posterId}`)
}

export function getFavorites() {
  return request.get('/poster/favorites')
}
