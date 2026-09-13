import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useContentStore = defineStore('content', () => {
  const contents = ref<Content[]>([])
  const currentContent = ref<Content | null>(null)
  const isLoading = ref(false)
  const pagination = ref({
    total: 0,
    page: 1,
    pageSize: 10
  })

  const fetchContents = async (params?: ContentQueryParams) => {
    isLoading.value = true
    try {
      const response = await api.contents.list(params)
      contents.value = response.data.list
      pagination.value = response.data.pagination
      return response.data
    } catch (error) {
      console.error('Failed to fetch contents:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const fetchContentDetail = async (id: number) => {
    isLoading.value = true
    try {
      const response = await api.contents.detail(id)
      currentContent.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch content detail:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const generateContent = async (topicId: number, params?: ContentGenerateParams) => {
    isLoading.value = true
    try {
      const response = await api.contents.generate(topicId, params)
      contents.value.unshift(response.data)
      return response.data
    } catch (error) {
      console.error('Failed to generate content:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const createContent = async (data: ContentCreateParams) => {
    try {
      const response = await api.contents.create(data)
      contents.value.unshift(response.data)
      return response.data
    } catch (error) {
      console.error('Failed to create content:', error)
      return null
    }
  }

  const updateContent = async (id: number, data: ContentUpdateParams) => {
    try {
      const response = await api.contents.update(id, data)
      const index = contents.value.findIndex(c => c.id === id)
      if (index !== -1) {
        contents.value[index] = response.data
      }
      if (currentContent.value?.id === id) {
        currentContent.value = response.data
      }
      return response.data
    } catch (error) {
      console.error('Failed to update content:', error)
      return null
    }
  }

  const reviewContent = async (id: number, data: ContentReviewParams) => {
    try {
      const response = await api.contents.review(id, data)
      if (currentContent.value?.id === id) {
        currentContent.value = response.data
      }
      return response.data
    } catch (error) {
      console.error('Failed to review content:', error)
      return null
    }
  }

  const deleteContent = async (id: number) => {
    try {
      await api.contents.delete(id)
      contents.value = contents.value.filter(c => c.id !== id)
      if (currentContent.value?.id === id) {
        currentContent.value = null
      }
      return true
    } catch (error) {
      console.error('Failed to delete content:', error)
      return false
    }
  }

  return {
    contents,
    currentContent,
    isLoading,
    pagination,
    fetchContents,
    fetchContentDetail,
    generateContent,
    createContent,
    updateContent,
    reviewContent,
    deleteContent
  }
})

export interface Content {
  id: number
  topic_id: number
  topic_title?: string
  title: string
  content_text: string
  content_type: 'article' | 'image'
  word_count: number
  status: 'draft' | 'reviewing' | 'approved' | 'published'
  created_by: number
  created_by_name?: string
  reviewed_by?: number
  reviewed_by_name?: string
  created_at: string
  reviewed_at?: string
  published_at?: string
}

export interface ContentQueryParams {
  page?: number
  pageSize?: number
  status?: string
  content_type?: string
  keyword?: string
  start_date?: string
  end_date?: string
}

export interface ContentGenerateParams {
  platform?: 'xiaohongshu' | 'wechat'
  tone?: 'professional' | 'casual' | 'enthusiastic'
  length?: 'short' | 'medium' | 'long'
}

export interface ContentCreateParams {
  topic_id: number
  title: string
  content_text: string
  content_type?: 'article' | 'image'
  platform?: 'xiaohongshu' | 'wechat'
}

export interface ContentUpdateParams {
  title?: string
  content_text?: string
  status?: string
}

export interface ContentReviewParams {
  status: 'approved' | 'rejected'
  review_note?: string
}
