<template>
  <div class="image-list">
    <PageHeader title="图片管理" :actions="pageActions" />
    
    <Card>
      <!-- 筛选条件 -->
      <div class="filter-bar">
        <el-form :inline="true">
          <el-form-item label="图片类型">
            <el-select v-model="queryParams.image_type" placeholder="请选择类型" clearable>
              <el-option label="全部" value="" />
              <el-option label="封面图" value="cover" />
              <el-option label="正文图" value="section" />
              <el-option label="摘要图" value="summary" />
            </el-select>
          </el-form-item>
          <el-form-item label="内容ID">
            <el-input v-model="queryParams.content_id" placeholder="内容ID" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchData">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 图片网格 -->
      <ImageGrid
        :images="imageList"
        show-download
        show-delete
        @view="viewImage"
        @delete="deleteImage"
      />
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import ImageGrid from '@components/ImageGrid.vue'
import { imageApi } from '@services/api'

const loading = ref(false)
const imageList = ref([])
const pagination = ref({
  total: 0,
  page: 1,
  pageSize: 20
})

const queryParams = reactive({
  image_type: '',
  content_id: ''
})

const pageActions = [
  { label: '批量生成', type: 'primary', icon: 'LightBulb', key: 'batch-generate' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.value.page,
      pageSize: pagination.value.pageSize
    }
    
    if (queryParams.image_type) params.image_type = queryParams.image_type
    if (queryParams.content_id) params.content_id = queryParams.content_id
    
    const result: any = await imageApi.list(params)
    if (result?.data) {
      imageList.value = result.data.list
      pagination.value = result.data.pagination
    }
  } catch (error) {
    console.error('Failed to fetch images:', error)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  queryParams.image_type = ''
  queryParams.content_id = ''
  fetchData()
}

const viewImage = (image: any) => {
  window.open(image.image_url, '_blank')
}

const deleteImage = async (image: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这张图片吗？', '警告', {
      type: 'warning'
    })
    await imageApi.delete(image.id)
    ElMessage.success('删除成功')
    imageList.value = imageList.value.filter(i => i.id !== image.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete image:', error)
    }
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.image-list {
  padding: 20px;
}

.filter-bar {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
