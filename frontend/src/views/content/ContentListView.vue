<template>
  <div class="content-list">
    <PageHeader title="内容管理" :actions="pageActions" />
    
    <Card>
      <!-- 筛选条件 -->
      <div class="filter-bar">
        <el-form :inline="true">
          <el-form-item label="状态">
            <el-select v-model="queryParams.status" placeholder="请选择状态" clearable>
              <el-option label="全部" value="" />
              <el-option label="草稿" value="draft" />
              <el-option label="审核中" value="reviewing" />
              <el-option label="已通过" value="approved" />
              <el-option label="已发布" value="published" />
            </el-select>
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="queryParams.content_type" placeholder="请选择类型" clearable>
              <el-option label="全部" value="" />
              <el-option label="文章" value="article" />
              <el-option label="图片" value="image" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input v-model="queryParams.keyword" placeholder="标题/内容" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchData">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 内容列表 -->
      <el-table
        v-loading="loading"
        :data="contentList"
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="title" label="内容标题" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="viewContent(row.id)">
              {{ row.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="topic_title" label="关联选题" min-width="150" />
        <el-table-column prop="content_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.content_type === 'article' ? 'primary' : 'success'">
              {{ row.content_type === 'article' ? '文章' : '图片' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="word_count" label="字数" width="80" />
        <el-table-column prop="created_by_name" label="创建人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewContent(row.id)">查看</el-button>
            <el-button v-if="row.status === 'draft'" type="primary" link @click="editContent(row.id)">编辑</el-button>
            <el-button v-if="row.status === 'approved'" type="success" link @click="reviewContent(row.id)">审核</el-button>
            <el-button type="danger" link @click="deleteContent(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import StatusBadge from '@components/StatusBadge.vue'
import { contentApi } from '@services/api'

const router = useRouter()

const loading = ref(false)
const contentList = ref([])
const pagination = ref({
  total: 0,
  page: 1,
  pageSize: 10
})

const queryParams = reactive({
  status: '',
  content_type: '',
  keyword: ''
})

const pageActions = [
  { label: '创建内容', type: 'primary', icon: 'Plus', key: 'create' },
  { label: '批量生成', type: 'success', icon: 'LightBulb', key: 'batch-generate' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
      ...queryParams
    }
    const result: any = await contentApi.list(params)
    if (result?.data) {
      contentList.value = result.data.list
      pagination.value = result.data.pagination
    }
  } catch (error) {
    console.error('Failed to fetch contents:', error)
  } finally {
    loading.value = false
  }
}

const handleSortChange = (sort: any) => {
  // TODO: 实现排序逻辑
}

const resetFilter = () => {
  queryParams.status = ''
  queryParams.content_type = ''
  queryParams.keyword = ''
  fetchData()
}

const viewContent = (id: number) => {
  router.push(`/content/${id}`)
}

const editContent = (id: number) => {
  router.push(`/content/${id}/edit`)
}

const reviewContent = (id: number) => {
  router.push(`/content/${id}/review`)
}

const deleteContent = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个内容吗？', '警告', {
      type: 'warning'
    })
    await contentApi.delete(id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete content:', error)
    }
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.content-list {
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
