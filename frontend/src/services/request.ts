import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：从 localStorage 读取 token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    console.log('[DEBUG] 请求拦截器 - URL:', config.url, 'token:', token ? token.slice(0, 20) + '...' : '无')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一错误处理
request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code && res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // token 无效或过期，清除并跳转登录页
          // localStorage.removeItem('token')
          ElMessage.error('登录已过期，请重新登录')
          // 避免重复跳转
          // if (window.location.pathname !== '/login') {
          //   window.location.href = '/login'
          // }
          break
        case 403:
          ElMessage.error('禁止访问')
          break
        case 404:
          ElMessage.error('请求资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误')
          break
        default:
          ElMessage.error(`请求失败: ${error.message}`)
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      ElMessage.error(error.message)
    }
    return Promise.reject(error)
  }
)

export default request
