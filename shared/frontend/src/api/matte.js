import request from './request'

export function processMatte(formData) {
  return request.post('/matte/process', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getMatteHistory(page = 1, pageSize = 20) {
  return request.get('/matte/history', { params: { page, page_size: pageSize } })
}

export function getMatteDownloadUrl(id) {
  return `/api/matte/download/${id}`
}
