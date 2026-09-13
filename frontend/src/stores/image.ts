import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useImageStore = defineStore('image', () => {
  const images = ref<Image[]>([])
  const currentContentImages = ref<Image[]>([])
  const isLoading = ref(false)
  const pagination = ref({
    total: 0,
    page: 1,
    pageSize: 20
  })

  const fetchImages = async (params?: ImageQueryParams) => {
    isLoading.value = true
    try {
      const response = await api.images.list(params)
      images.value = response.data.list
      pagination.value = response.data.pagination
      return response.data
    } catch (error) {
      console.error('Failed to fetch images:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const fetchContentImages = async (contentId: number) => {
    isLoading.value = true
    try {
      const response = await api.images.byContent(contentId)
      currentContentImages.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch content images:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const generateImages = async (contentId: number, params?: ImageGenerateParams) => {
    isLoading.value = true
    try {
      const response = await api.images.generate(contentId, params)
      currentContentImages.value.push(...response.data)
      return response.data
    } catch (error) {
      console.error('Failed to generate images:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const deleteImage = async (id: number) => {
    try {
      await api.images.delete(id)
      images.value = images.value.filter(i => i.id !== id)
      currentContentImages.value = currentContentImages.value.filter(i => i.id !== id)
      return true
    } catch (error) {
      console.error('Failed to delete image:', error)
      return false
    }
  }

  return {
    images,
    currentContentImages,
    isLoading,
    pagination,
    fetchImages,
    fetchContentImages,
    generateImages,
    deleteImage
  }
})

export interface Image {
  id: number
  content_id: number
  image_url: string
  image_type: 'cover' | 'section' | 'summary'
  prompt: string
  generated_at: string
  width: number
  height: number
  size?: number
}

export interface ImageQueryParams {
  page?: number
  pageSize?: number
  content_id?: number
  image_type?: string
  start_date?: string
  end_date?: string
}

export interface ImageGenerateParams {
  image_type?: ('cover' | 'section' | 'summary')[]
  count?: number
  style?: 'minimalist' | 'professional' | 'creative' | 'elegant'
  width?: number
  height?: number
}
