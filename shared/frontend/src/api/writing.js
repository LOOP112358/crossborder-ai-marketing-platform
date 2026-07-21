import request from './request'

export function generateCopywriting(params) {
  return request.post('/writing/generate', params)
}

export function getWritingHistory(page = 1, pageSize = 20) {
  return request.get('/writing/history', { params: { page, page_size: pageSize } })
}

export function searchWritingProducts(q = '', limit = 20, hasImage = false, extra = {}) {
  return request.get('/writing/products/search', {
    params: { q, limit, has_image: hasImage, diverse: extra.diverse ?? true, product_type: extra.product_type || '' },
  })
}

export function listProductCategories() {
  return request.get('/writing/products/categories')
}


export function getPosterCopy(productId, language = 'zh') {
  return request.get(`/writing/products/${productId}/poster-copy`, { params: { language } })
}

