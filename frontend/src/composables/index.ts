import { ref, onMounted } from 'vue'

export function useLoading(callback: (...args: any[]) => Promise<any>) {
  const loading = ref(false)
  
  const execute = async (...args: any[]) => {
    loading.value = true
    try {
      const result = await callback(...args)
      return result
    } catch (error) {
      console.error('Execution error:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  return {
    loading,
    execute
  }
}

export function usePagination<T>(fetchFn: (page: number, pageSize: number) => Promise<any>) {
  const list = ref<T[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(10)
  const loading = ref(false)
  
  const fetchData = async (currentPage: number = page.value, currentPageSize: number = pageSize.value) => {
    loading.value = true
    try {
      const response = await fetchFn(currentPage, currentPageSize)
      list.value = response.list || []
      total.value = response.total || 0
      page.value = currentPage
      pageSize.value = currentPageSize
      return response
    } catch (error) {
      console.error('Fetch data error:', error)
      return null
    } finally {
      loading.value = false
    }
  }
  
  const handlePageChange = (newPage: number) => {
    fetchData(newPage, pageSize.value)
  }
  
  const handleSizeChange = (newSize: number) => {
    fetchData(1, newSize)
  }
  
  onMounted(() => {
    fetchData()
  })
  
  return {
    list,
    total,
    page,
    pageSize,
    loading,
    fetchData,
    handlePageChange,
    handleSizeChange
  }
}

export function useForm<T>(initialValues: T) {
  const form = ref<T>(initialValues)
  const rules = ref<Record<string, any>>({})
  const formRef = ref<any>(null)
  
  const setForm = (data: Partial<T>) => {
    form.value = { ...form.value, ...data }
  }
  
  const resetForm = () => {
    form.value = { ...initialValues }
    if (formRef.value) {
      formRef.value.resetFields()
    }
  }
  
  const validate = async () => {
    if (formRef.value) {
      try {
        await formRef.value.validate()
        return true
      } catch (error) {
        return false
      }
    }
    return true
  }
  
  return {
    form,
    rules,
    formRef,
    setForm,
    resetForm,
    validate
  }
}
