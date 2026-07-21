import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 全局应用状态（成员2/3/4协作共享）
 * 成员2 设置 mattedUrl 和 category
 * 成员3 读取 category，设置 enhancedBgUrl
 * 成员4 读取 mattedUrl 和 enhancedBgUrl 进行海报合成
 */
export const useAppStore = defineStore('app', () => {
  // 成员2：抠图结果
  const mattedUrl = ref('')
  const category = ref('')
  const categoryEn = ref('')
  const confidence = ref(0)

  // 成员3：背景生成结果
  const enhancedBgUrl = ref('')
  const bgStyle = ref('')

  // 成员4：海报合成配置
  const posterConfig = ref({
    templateId: null,
    title: '',
    discount: '',
    price: '',
  })

  function setMatteResult(url, cat, catEn, conf) {
    mattedUrl.value = url
    category.value = cat
    categoryEn.value = catEn
    confidence.value = conf
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
    enhancedBgUrl, bgStyle,
    posterConfig,
    setMatteResult, setBackgroundResult, setPosterConfig,
  }
})
