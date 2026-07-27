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

  // 成员3：双模型背景（默认优先 Seedream 场景图）
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

  function setMatteResult(url, cat, catEn, conf) {
    mattedUrl.value = url
    category.value = cat
    categoryEn.value = catEn
    confidence.value = conf
  }

  function setSelectedProduct(product, posterCopy = null) {
    selectedProduct.value = product
    selectedProductId.value = product?.id ?? null
    productImageUrl.value = product?.image_url || ''
    if (product) {
      // 优先用库内品类；避免误判品类覆盖正确信息
      if (product.category) category.value = product.category
      categoryEn.value = product.category_en || product.product_type || categoryEn.value
    }
    if (posterCopy) {
      setPosterConfig(posterCopy)
    }
  }

  function setBackgroundResult(urls, style, preferred = 'seedream') {
    const seedream = typeof urls === 'string' ? '' : (urls?.bg_url || '')
    const enhanced = typeof urls === 'string' ? urls : (urls?.enhanced_url || '')
    seedreamBgUrl.value = seedream
    enhancedBgUrl.value = enhanced || (typeof urls === 'string' ? urls : '')
    bgStyle.value = style
    if (preferred === 'sd' && enhancedBgUrl.value) {
      preferredBgUrl.value = enhancedBgUrl.value
    } else {
      preferredBgUrl.value = seedreamBgUrl.value || enhancedBgUrl.value
    }
  }

  function chooseBackground(which) {
    if (which === 'sd' && enhancedBgUrl.value) preferredBgUrl.value = enhancedBgUrl.value
    else if (seedreamBgUrl.value) preferredBgUrl.value = seedreamBgUrl.value
  }

  function setPosterConfig(config) {
    posterConfig.value = { ...posterConfig.value, ...config }
  }

  return {
    mattedUrl, category, categoryEn, confidence,
    selectedProductId, selectedProduct, productImageUrl,
    seedreamBgUrl, enhancedBgUrl, preferredBgUrl, bgStyle,
    posterConfig,
    setMatteResult, setSelectedProduct, setBackgroundResult, chooseBackground, setPosterConfig,
  }
})
