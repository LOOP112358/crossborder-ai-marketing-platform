import request from './request'

export function generateCopywriting(params) {
  return request.post('/writing/generate', params)
}

export function getWritingHistory(page = 1, pageSize = 20) {
  return request.get('/writing/history', { params: { page, page_size: pageSize } })
}

export function deleteWritingHistory(id) {
  return request.delete(`/writing/history/${id}`)
}

export function searchWritingProducts(q = '', limit = 20, hasImage = false, extra = {}) {
  return request.get('/writing/products/search', {
    params: { q, limit, has_image: hasImage, diverse: extra.diverse ?? true, product_type: extra.product_type || '' },
  })
}

export function listProductCategories(hasImage = false) {
  return request.get('/writing/products/categories', {
    params: { has_image: hasImage },
  })
}


export function getPosterCopy(productId, language = 'zh', llm = true) {
  return request.get(`/writing/products/${productId}/poster-copy`, {
    params: {
      language,
      llm,
      // 防浏览器/代理缓存旧商品文案
      _ts: Date.now(),
    },
    timeout: llm ? 60000 : 15000,
    headers: {
      'Cache-Control': 'no-cache',
      Pragma: 'no-cache',
    },
  })
}

export function listCampaigns() {
  return request.get('/writing/campaigns')
}

export function recommendCampaign(payload) {
  return request.post('/writing/campaigns/recommend', payload)
}

