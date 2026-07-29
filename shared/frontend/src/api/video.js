import request from './request'

export function generateVideoScript(params) {
  return request.post('/video/generate', params, { timeout: 60000 })
}

export function getVideoHistory(page = 1, pageSize = 20) {
  return request.get('/video/history', {
    params: { page, page_size: pageSize },
  })
}

export function deleteVideoHistory(id) {
  return request.delete(`/video/history/${id}`)
}
