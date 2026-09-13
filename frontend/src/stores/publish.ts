import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePublishStore = defineStore('publish', () => {
  const publishHistory = ref<PublishRecord[]>([])
  const isLoading = ref(false)
  const pagination = ref({
    total: 0,
    page: 1,
    pageSize: 10
  })

  const fetchPublishHistory = async (params?: PublishQueryParams) => {
    isLoading.value = true
    try {
      const response = await api.publish.history(params)
      publishHistory.value = response.data.list
      pagination.value = response.data.pagination
      return response.data
    } catch (error) {
      console.error('Failed to fetch publish history:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const publishToPlatform = async (contentId: number, platform: 'xiaohongshu' | 'wechat') => {
    try {
      const response = await api.publish.create(contentId, platform)
      publishHistory.value.unshift(response.data)
      return response.data
    } catch (error) {
      console.error(`Failed to publish to ${platform}:`, error)
      return null
    }
  }

  const unpublish = async (id: number) => {
    try {
      await api.publish.delete(id)
      publishHistory.value = publishHistory.value.filter(p => p.id !== id)
      return true
    } catch (error) {
      console.error('Failed to unpublish:', error)
      return false
    }
  }

  return {
    publishHistory,
    isLoading,
    pagination,
    fetchPublishHistory,
    publishToPlatform,
    unpublish
  }
})

export interface PublishRecord {
  id: number
  content_id: number
  content_title?: string
  platform: 'xiaohongshu' | 'wechat'
  post_url?: string
  status: 'pending' | 'published' | 'failed'
  published_at?: string
  error_message?: string
  created_at: string
}

export interface PublishQueryParams {
  page?: number
  pageSize?: number
  platform?: string
  status?: string
  start_date?: string
  end_date?: string
}
