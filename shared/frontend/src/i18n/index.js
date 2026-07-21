import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import en from './locales/en'
import ja from './locales/ja'
import ko from './locales/ko'
import es from './locales/es'

const savedLang = localStorage.getItem('lang') || 'zh-CN'

const i18n = createI18n({
  legacy: false,           // 使用 Composition API 模式
  locale: savedLang,
  fallbackLocale: 'zh-CN',
  globalInjection: true,
  messages: {
    'zh-CN': zhCN,
    'en': en,
    'ja': ja,
    'ko': ko,
    'es': es,
  },
})

export default i18n
