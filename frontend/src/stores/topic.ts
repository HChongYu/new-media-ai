import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTopicStore = defineStore('topic', () => {
  const topics = ref<Topic[]>([])
  const currentTopic = ref<Topic | null>(null)
  const isLoading = ref(false)
  const pagination = ref({
    total: 0,
    page: 1,
    pageSize: 10
  })

  const fetchTopics = async (params?: TopicQueryParams) => {
    isLoading.value = true
    try {
      // TODO: 调用API获取选题列表
      const response = await api.topics.list(params)
      topics.value = response.data.list
      pagination.value = response.data.pagination
      return response.data
    } catch (error) {
      console.error('Failed to fetch topics:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const fetchTopicDetail = async (id: number) => {
    isLoading.value = true
    try {
      const response = await api.topics.detail(id)
      currentTopic.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch topic detail:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const generateTopics = async (params: TopicGenerateParams) => {
    isLoading.value = true
    try {
      const response = await api.topics.generate(params)
      return response.data
    } catch (error) {
      console.error('Failed to generate topics:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const createTopic = async (data: TopicCreateParams) => {
    try {
      const response = await api.topics.create(data)
      topics.value.unshift(response.data)
      return response.data
    } catch (error) {
      console.error('Failed to create topic:', error)
      return null
    }
  }

  const updateTopic = async (id: number, data: TopicUpdateParams) => {
    try {
      const response = await api.topics.update(id, data)
      const index = topics.value.findIndex(t => t.id === id)
      if (index !== -1) {
        topics.value[index] = response.data
      }
      if (currentTopic.value?.id === id) {
        currentTopic.value = response.data
      }
      return response.data
    } catch (error) {
      console.error('Failed to update topic:', error)
      return null
    }
  }

  const deleteTopic = async (id: number) => {
    try {
      await api.topics.delete(id)
      topics.value = topics.value.filter(t => t.id !== id)
      if (currentTopic.value?.id === id) {
        currentTopic.value = null
      }
      return true
    } catch (error) {
      console.error('Failed to delete topic:', error)
      return false
    }
  }

  return {
    topics,
    currentTopic,
    isLoading,
    pagination,
    fetchTopics,
    fetchTopicDetail,
    generateTopics,
    createTopic,
    updateTopic,
    deleteTopic
  }
})

export interface Topic {
  id: number
  title: string
  description: string
  status: 'draft' | 'pending' | 'approved' | 'rejected'
  content_count: number
  created_by: number
  created_by_name?: string
  created_at: string
  approved_at?: string
}

export interface TopicQueryParams {
  page?: number
  pageSize?: number
  status?: string
  keyword?: string
  start_date?: string
  end_date?: string
}

export interface TopicGenerateParams {
  keywords?: string[]
  category?: string
  target_audience?: string
  content_style?: string
  count?: number
}

export interface TopicCreateParams {
  title: string
  description: string
  category?: string
  tags?: string[]
}

export interface TopicUpdateParams {
  title?: string
  description?: string
  status?: string
  category?: string
  tags?: string[]
}
