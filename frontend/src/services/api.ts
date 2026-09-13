import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@stores/user'

// 创建 axios 实例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    const token = userStore.token
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    const res = response.data
    
    // 统一错误处理
    if (res.code && res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    
    return res
  },
  (error) => {
    // 处理 HTTP 错误
    if (error.response) {
      const status = error.response.status
      
      switch (status) {
        case 401:
          ElMessage.error('未授权，请重新登录')
          // TODO: 跳转登录页
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

// API 方法封装
export const api = {
  // 认证相关
  auth: {
    login: (data: { username: string; password: string }) => service.post('/auth/login', data),
    logout: () => service.post('/auth/logout'),
    me: () => service.get('/auth/me')
  },
  
  // 选题相关
  topics: {
    list: (params?: any) => service.get('/topics', { params }),
    detail: (id: number) => service.get(`/topics/${id}`),
    generate: (data: any) => service.post('/topics/generate', data),
    create: (data: any) => service.post('/topics', data),
    update: (id: number, data: any) => service.put(`/topics/${id}`, data),
    delete: (id: number) => service.delete(`/topics/${id}`)
  },
  
  // 内容相关
  contents: {
    list: (params?: any) => service.get('/contents', { params }),
    detail: (id: number) => service.get(`/contents/${id}`),
    generate: (topicId: number, params?: any) => service.post(`/topics/${topicId}/content`, params),
    create: (data: any) => service.post('/contents', data),
    update: (id: number, data: any) => service.put(`/contents/${id}`, data),
    review: (id: number, data: any) => service.post(`/contents/${id}/review`, data),
    delete: (id: number) => service.delete(`/contents/${id}`)
  },
  
  // 图片相关
  images: {
    list: (params?: any) => service.get('/images', { params }),
    byContent: (contentId: number) => service.get(`/contents/${contentId}/images`),
    generate: (contentId: number, data: any) => service.post(`/contents/${contentId}/images/generate`, data),
    delete: (id: number) => service.delete(`/images/${id}`)
  },
  
  // 发布相关
  publish: {
    history: (params?: any) => service.get('/publish/history', { params }),
    create: (contentId: number, platform: 'xiaohongshu' | 'wechat') => 
      service.post(`/contents/${contentId}/publish/${platform}`),
    delete: (id: number) => service.delete(`/publish/${id}`)
  },
  
  // 设置相关
  settings: {
    get: () => service.get('/settings'),
    update: (data: any) => service.put('/settings', data)
  }
}

export default service
