<template>
  <div class="publish-history">
    <PageHeader title="发布记录" />
    
    <Card>
      <!-- 筛选条件 -->
      <div class="filter-bar">
        <el-form :inline="true">
          <el-form-item label="平台">
            <el-select v-model="queryParams.platform" placeholder="请选择平台" clearable>
              <el-option label="全部" value="" />
              <el-option label="小红书" value="xiaohongshu" />
              <el-option label="微信公众号" value="wechat" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="queryParams.status" placeholder="请选择状态" clearable>
              <el-option label="全部" value="" />
              <el-option label="待发布" value="pending" />
              <el-option label="已发布" value="published" />
              <el-option label="发布失败" value="failed" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchData">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 发布记录列表 -->
      <el-table
        v-loading="loading"
        :data="publishList"
        style="width: 100%"
      >
        <el-table-column prop="content_title" label="内容标题" min-width="200" />
        <el-table-column prop="platform" label="发布平台" width="120">
          <template #default="{ row }">
            <el-tag :type="row.platform === 'xiaohongshu' ? 'primary' : 'success'">
              {{ row.platform === 'xiaohongshu' ? '小红书' : '微信公众号' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="post_url" label="发布链接" min-width="200">
          <template #default="{ row }">
            <el-link v-if="row.post_url" :href="row.post_url" target="_blank" type="primary">
              查看原文
            </el-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="published_at" label="发布时间" width="160">
          <template #default="{ row }">
            {{ row.published_at ? formatDate(row.published_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.post_url" type="primary" link @click="viewPost(row.post_url)">
              查看
            </el-button>
            <el-button v-if="row.status === 'failed'" type="warning" link @click="retryPublish(row)">
              重试
            </el-button>
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
import { ElMessage } from 'element-plus'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import StatusBadge from '@components/StatusBadge.vue'
import { usePublishStore } from '@stores/publish'

const publishStore = usePublishStore()

const loading = ref(false)
const publishList = ref([])
const pagination = ref({
  total: 0,
  page: 1,
  pageSize: 10
})

const queryParams = reactive({
  platform: '',
  status: ''
})

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.value.page,
      pageSize: pagination.value.pageSize
    }
    
    if (queryParams.platform) params.platform = queryParams.platform
    if (queryParams.status) params.status = queryParams.status
    
    const result = await publishStore.fetchPublishHistory(params)
    if (result) {
      publishList.value = result.list
      pagination.value = result.pagination
    }
  } catch (error) {
    console.error('Failed to fetch publish history:', error)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  queryParams.platform = ''
  queryParams.status = ''
  fetchData()
}

const viewPost = (url: string) => {
  window.open(url, '_blank')
}

const retryPublish = async (record: any) => {
  try {
    await publishStore.publishToPlatform(record.content_id, record.platform)
    ElMessage.success('重新发布成功')
    fetchData()
  } catch (error) {
    console.error('Failed to retry publish:', error)
    ElMessage.error('重新发布失败')
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return '-'
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
.publish-history {
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
