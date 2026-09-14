<template>
  <div class="topic-list">
    <PageHeader title="选题管理" :actions="pageActions" />
    
    <Card>
      <!-- 筛选条件 -->
      <div class="filter-bar">
        <el-form :inline="true">
          <el-form-item label="状态">
            <el-select v-model="queryParams.status" placeholder="请选择状态" clearable>
              <el-option label="全部" value="" />
              <el-option label="草稿" value="draft" />
              <el-option label="待审核" value="pending" />
              <el-option label="已通过" value="approved" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input v-model="queryParams.keyword" placeholder="选题标题" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchData">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 选题列表 -->
      <el-table
        v-loading="loading"
        :data="topicList"
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="title" label="选题标题" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="viewTopic(row.id)">
              {{ row.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="content_count" label="内容数" width="80" />
        <el-table-column prop="created_by_name" label="创建人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewTopic(row.id)">查看</el-button>
            <el-button type="primary" link @click="editTopic(row.id)">编辑</el-button>
            <el-button type="danger" link @click="deleteTopic(row.id)">删除</el-button>
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
import { topicApi } from '@services/api'

const router = useRouter()

const loading = ref(false)
const topicList = ref([])
const pagination = ref({
  total: 0,
  page: 1,
  pageSize: 10
})

const queryParams = reactive({
  status: '',
  keyword: ''
})

const pageActions = [
  { label: '生成选题', type: 'primary', icon: 'LightBulb', key: 'generate' },
  { label: '新建选题', type: 'success', icon: 'Plus', key: 'create' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
      ...queryParams
    }
    const result: any = await topicApi.list(params)
    if (result?.data) {
      topicList.value = result.data.list
      pagination.value = result.data.pagination
    }
  } catch (error) {
    console.error('Failed to fetch topics:', error)
  } finally {
    console.log('[DEBUG] fetchData - 最后执行')
    loading.value = false
  }
}

const handleSortChange = (sort: any) => {
  // TODO: 实现排序逻辑
}

const resetFilter = () => {
  queryParams.status = ''
  queryParams.keyword = ''
  fetchData()
}

const viewTopic = (id: number) => {
  router.push(`/topics/${id}`)
}

const editTopic = (id: number) => {
  router.push(`/topics/${id}/edit`)
}

const deleteTopic = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个选题吗？', '警告', {
      type: 'warning'
    })
    await topicApi.delete(id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete topic:', error)
    }
  }
}

const formatDate = (dateString: string) => {
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
.topic-list {
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
