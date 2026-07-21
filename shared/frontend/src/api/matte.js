import request from './request'

export function processMatte(formData) {
  return request.post('/matte/process', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
}

export function processMatteFromUrl(imageUrl, edgeSmoothing = 1, category = '', categoryEn = '') {
  const form = new FormData()
  form.append('image_url', imageUrl)
  form.append('edge_smoothing', String(edgeSmoothing))
  if (category) form.append('category', category)
  if (categoryEn) form.append('category_en', categoryEn)
  return request.post('/matte/process-url', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
}


export function getMatteHistory(page = 1, pageSize = 20) {
  return request.get('/matte/history', { params: { page, page_size: pageSize } })
}

export function getMatteDownloadUrl(id) {
  return `/api/matte/download/${id}`
}
