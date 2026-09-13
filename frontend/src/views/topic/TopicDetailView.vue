<template>
  <div class="topic-detail">
    <BackButton />
    <PageHeader :title="topic?.title || '选题详情'" :actions="pageActions" />
    
    <el-row :gutter="20">
      <!-- 主要信息 -->
      <el-col :span="16">
        <Card title="选题信息">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="选题标题">
              {{ topic?.title }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <StatusBadge :status="topic?.status || ''" />
            </el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">
              {{ topic?.description || '暂无描述' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建人">
              {{ topic?.created_by_name || '未知' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDate(topic?.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="审核时间">
              {{ topic?.approved_at ? formatDate(topic.approved_at) : '未审核' }}
            </el-descriptions-item>
          </el-descriptions>
        </Card>
        
        <Card title="关联内容" style="margin-top: 20px;">
          <el-table :data="topicContents" style="width: 100%">
            <el-table-column prop="title" label="内容标题" min-width="200" />
            <el-table-column prop="content_type" label="类型" width="100">
              <template #default="{ row }">
                {{ row.content_type === 'article' ? '文章' : '图片' }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <StatusBadge :status="row.status" />
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </Card>
      </el-col>
      
      <!-- 侧边栏 -->
      <el-col :span="8">
        <Card title="操作">
          <div class="action-buttons">
            <el-button
              v-for="action in sidebarActions"
              :key="action.key"
              :type="action.type"
              :icon="action.icon"
              style="width: 100%; margin-bottom: 12px;"
              @click="handleAction(action)"
            >
              {{ action.label }}
            </el-button>
          </div>
        </Card>
        
        <Card title="统计信息" style="margin-top: 20px;">
          <el-statistic title="内容数量" :value="topic?.content_count || 0" />
          <el-statistic
            title="图片数量"
            :value="topicImagesCount"
            style="margin-top: 20px;"
          />
        </Card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import BackButton from '@components/BackButton.vue'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import StatusBadge from '@components/StatusBadge.vue'
import { useTopicStore } from '@stores/topic'

const route = useRoute()
const router = useRouter()
const topicStore = useTopicStore()

const topicId = ref<number>(Number(route.params.id))
const topic = ref<any>(null)
const topicContents = ref([])
const topicImagesCount = ref(0)

const pageActions = [
  { label: '编辑选题', type: 'primary', icon: 'Edit', key: 'edit' },
  { label: '生成内容', type: 'success', icon: 'Plus', key: 'generate-content' }
]

const sidebarActions = [
  { label: '查看选题详情', type: 'info', icon: 'Info', key: 'detail' },
  { label: '导出选题', type: 'warning', icon: 'Download', key: 'export' }
]

const fetchData = async () => {
  try {
    const result = await topicStore.fetchTopicDetail(topicId.value)
    if (result) {
      topic.value = result
      topicContents.value = result.contents || []
      topicImagesCount.value = result.images_count || 0
    }
  } catch (error) {
    console.error('Failed to fetch topic detail:', error)
    ElMessage.error('获取选题详情失败')
  }
}

const handleAction = (action: any) => {
  switch (action.key) {
    case 'edit':
      router.push(`/topics/${topicId.value}/edit`)
      break
    case 'generate-content':
      router.push(`/content/create?topicId=${topicId.value}`)
      break
    case 'detail':
      ElMessage.info('查看选题详情')
      break
    case 'export':
      ElMessage.info('导出选题功能开发中')
      break
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.topic-detail {
  padding: 20px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
