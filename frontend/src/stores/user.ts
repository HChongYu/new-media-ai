import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isLoading = ref(false)

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  const setUser = (userData: User | null) => {
    user.value = userData
  }

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearUser = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  const login = async (username: string, password: string) => {
    isLoading.value = true
    try {
      // TODO: 调用登录API
      const response = await api.auth.login({ username, password })
      setToken(response.data.token)
      setUser(response.data.user)
      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    } finally {
      isLoading.value = false
    }
  }

  const logout = () => {
    clearUser()
  }

  return {
    user,
    token,
    isLoading,
    isAuthenticated,
    setUser,
    setToken,
    clearUser,
    login,
    logout
  }
})

export interface User {
  id: number
  username: string
  email: string
  avatar?: string
  role: 'admin' | 'editor' | 'viewer'
  created_at: string
}
