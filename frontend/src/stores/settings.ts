import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<Settings | null>(null)
  const isLoading = ref(false)

  const fetchSettings = async () => {
    isLoading.value = true
    try {
      const response = await api.settings.get()
      settings.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch settings:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const updateSettings = async (data: SettingsUpdateParams) => {
    try {
      const response = await api.settings.update(data)
      settings.value = { ...settings.value, ...response.data }
      return response.data
    } catch (error) {
      console.error('Failed to update settings:', error)
      return null
    }
  }

  return {
    settings,
    isLoading,
    fetchSettings,
    updateSettings
  }
})

export interface Settings {
  id: number
  user_id: number
  preferred_topics: string[]
  preferred_formats: string[]
  llm_provider?: string
  llm_model?: string
  image_style?: string
  platform_settings?: PlatformSettings
  created_at: string
  updated_at: string
}

export interface PlatformSettings {
  xiaohongshu?: {
    auto_generate_images: boolean
    image_count: number
    default_tags: string[]
  }
  wechat?: {
    auto_publish: boolean
    default_category: string
  }
}

export interface SettingsUpdateParams {
  preferred_topics?: string[]
  preferred_formats?: string[]
  llm_provider?: string
  llm_model?: string
  image_style?: string
  platform_settings?: Partial<PlatformSettings>
}
