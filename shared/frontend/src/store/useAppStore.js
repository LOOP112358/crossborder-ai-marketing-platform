import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 全局应用状态（成员2/3/4协作共享）
 * 支持 ABO 商品库选品：图文一体带入海报工作流
 */
export const useAppStore = defineStore('app', () => {
  const mattedUrl = ref('')
  const category = ref('')
  const categoryEn = ref('')
  const confidence = ref(0)

  const selectedProductId = ref(null)
  const selectedProduct = ref(null)
  const productImageUrl = ref('')
  /** 与当前抠图结果绑定的商品 id，用于防止图文串货 */
  const mattedProductId = ref(null)

  // 成员3：Seedream 背景
  const seedreamBgUrl = ref('')
  const enhancedBgUrl = ref('')
  const preferredBgUrl = ref('')
  const bgStyle = ref('')

  const posterConfig = ref({
    templateId: null,
    title: '',
    subtitle: '',
    selling_point_1: '',
    selling_point_2: '',
    cta_text: '',
    discount: '',
    price: '',
  })
  /** 当前 posterConfig 对应的商品 id，换品必须清掉旧文案 */
  const posterConfigProductId = ref(null)

  const EMPTY_COPY = {
    title: '',
    subtitle: '',
    selling_point_1: '',
    selling_point_2: '',
    cta_text: '',
    discount: '',
    price: '',
  }

  /** 活动选品助手带入文案页的建议 */
  const campaignHint = ref(null)

  function clearPosterConfig() {
    posterConfig.value = {
      templateId: posterConfig.value?.templateId ?? null,
      ...EMPTY_COPY,
    }
    posterConfigProductId.value = null
  }

  function setMatteResult(url, cat, catEn, conf, productId = undefined) {
    mattedUrl.value = url
    category.value = cat
    categoryEn.value = catEn
    confidence.value = conf
    if (productId !== undefined) {
      const prev = mattedProductId.value
      mattedProductId.value = productId
      // 换绑商品或清空抠图时，丢掉旧海报文案缓存
      if (productId == null || (prev != null && Number(prev) !== Number(productId))) {
        clearPosterConfig()
      }
    }
  }

  function setCampaignHint(hint) {
    campaignHint.value = hint || null
  }

  function setSelectedProduct(product, posterCopy = null) {
    const nextId = product?.id ?? null
    const prevId = selectedProductId.value
    selectedProduct.value = product
    selectedProductId.value = nextId
    productImageUrl.value = product?.image_url || ''
    if (product) {
      if (product.category) category.value = product.category
      categoryEn.value = product.category_en || product.product_type || categoryEn.value
    }
    // 换品：先清空旧文案，避免和下一件商品串货
    if (prevId != null && nextId != null && Number(prevId) !== Number(nextId)) {
      clearPosterConfig()
    }
    if (posterCopy) {
      setPosterConfig(posterCopy, nextId)
    }
  }

  function setBackgroundResult(urls, style, preferred = 'seedream') {
    const seedream = typeof urls === 'string' ? urls : (urls?.bg_url || urls?.enhanced_url || '')
    seedreamBgUrl.value = seedream
    enhancedBgUrl.value = (typeof urls === 'string' ? urls : (urls?.enhanced_url || seedream)) || seedream
    bgStyle.value = style
    preferredBgUrl.value = seedream
  }

  function chooseBackground(which) {
    if (seedreamBgUrl.value) preferredBgUrl.value = seedreamBgUrl.value
    else if (enhancedBgUrl.value) preferredBgUrl.value = enhancedBgUrl.value
  }

  function setPosterConfig(config, productId = undefined) {
    const cleaned = { ...config }
    ;['title', 'subtitle', 'selling_point_1', 'selling_point_2', 'cta_text', 'discount', 'price'].forEach((k) => {
      if (typeof cleaned[k] === 'string') {
        cleaned[k] = cleaned[k].replace(/[…]+$/g, '').replace(/\.{3,}$/g, '').trim()
      }
    })
    // 文案字段整组覆盖，不与旧缓存合并
    posterConfig.value = {
      templateId: cleaned.templateId ?? posterConfig.value.templateId ?? null,
      title: cleaned.title || '',
      subtitle: cleaned.subtitle || '',
      selling_point_1: cleaned.selling_point_1 || '',
      selling_point_2: cleaned.selling_point_2 || '',
      cta_text: cleaned.cta_text || '',
      discount: cleaned.discount || '',
      price: cleaned.price || cleaned.cta_text || '',
    }
    if (productId !== undefined) {
      posterConfigProductId.value = productId
    } else if (selectedProductId.value != null) {
      posterConfigProductId.value = selectedProductId.value
    }
  }

  /** 图文是否仍指向同一商品 */
  function isPosterCopyInSync() {
    if (!mattedProductId.value || !selectedProductId.value) return true
    return Number(mattedProductId.value) === Number(selectedProductId.value)
  }

  /** 缓存文案是否属于指定商品 */
  function isPosterConfigForProduct(productId) {
    if (productId == null || posterConfigProductId.value == null) return false
    return Number(posterConfigProductId.value) === Number(productId)
  }

  return {
    mattedUrl, category, categoryEn, confidence,
    selectedProductId, selectedProduct, productImageUrl, mattedProductId,
    seedreamBgUrl, enhancedBgUrl, preferredBgUrl, bgStyle,
    posterConfig, posterConfigProductId, campaignHint,
    setMatteResult, setSelectedProduct, setBackgroundResult, chooseBackground,
    setPosterConfig, clearPosterConfig, isPosterCopyInSync, isPosterConfigForProduct, setCampaignHint,
  }
})
