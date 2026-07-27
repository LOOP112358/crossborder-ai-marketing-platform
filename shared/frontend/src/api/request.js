import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器：附加 JWT token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一解包 + 错误处理
request.interceptors.response.use(
  (response) => {
    // 文件下载（Excel/PDF）直接返回 Blob
    if (response.config.responseType === 'blob' || response.data instanceof Blob) {
      return response.data
    }
    const res = response.data
    // 如果直接返回了数据（非标准格式），原样返回
    if (res.code === undefined) return res
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message))
    }
    return res.data
  },
  (error) => {
    let msg = error.message || '网络错误'
    const data = error.response?.data
    if (typeof data?.detail === 'string') msg = data.detail
    else if (Array.isArray(data?.detail)) msg = data.detail.map((d) => d.msg || d).join(', ')
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default request
