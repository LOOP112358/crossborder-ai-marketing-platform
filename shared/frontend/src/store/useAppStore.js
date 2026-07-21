import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 全局应用状态（成员2/3/4协作共享）
 * 支持 ABO 商品库选品：图文一体带入海报工作流
 */
export const useAppStore = defineStore('app', () => {
  // 成员2：抠图结果
  const mattedUrl = ref('')
  const category = ref('')
  const categoryEn = ref('')
  const confidence = ref(0)

  // ABO 选品
  const selectedProductId = ref(null)
  const selectedProduct = ref(null)
  const productImageUrl = ref('')

  // 成员3：背景生成结果
  const enhancedBgUrl = ref('')
  const bgStyle = ref('')

  // 成员4：海报合成配置
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
      category.value = product.category || category.value
      categoryEn.value = product.category_en || product.product_type || categoryEn.value
      // 注意：不把库内原图当作抠图结果；需先走 matte process-url
    }
    if (posterCopy) {
      setPosterConfig(posterCopy)
    }
  }

  function setBackgroundResult(url, style) {
    enhancedBgUrl.value = url
    bgStyle.value = style
  }

  function setPosterConfig(config) {
    posterConfig.value = { ...posterConfig.value, ...config }
  }

  return {
    mattedUrl, category, categoryEn, confidence,
    selectedProductId, selectedProduct, productImageUrl,
    enhancedBgUrl, bgStyle,
    posterConfig,
    setMatteResult, setSelectedProduct, setBackgroundResult, setPosterConfig,
  }
})
