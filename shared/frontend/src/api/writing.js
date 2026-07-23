import request from './request'

export function generateCopywriting(params) {
  return request.post('/writing/generate', params)
}

export function getWritingHistory(page = 1, pageSize = 20) {
  return request.get('/writing/history', { params: { page, page_size: pageSize } })
}
