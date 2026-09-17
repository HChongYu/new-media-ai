<template>
  <div class="dashboard">
    <PageHeader title="仪表盘" />

    <!-- 加载失败：错误提示 + 重试，区别于“无数据” -->
    <el-card v-if="loadError" class="error-card">
      <el-result
        icon="error"
        title="仪表盘数据加载失败"
        :sub-title="errorMessage"
      >
        <template #extra>
          <el-button type="primary" @click="loadDashboard">重新加载</el-button>
        </template>
      </el-result>
    </el-card>

    <template v-else>
      <div v-loading="loading">
        <el-row :gutter="20">
          <!-- 统计卡片：点击跳转对应列表页 -->
          <el-col :span="6">
            <el-card class="stat-card" @click="router.push('/topics')">
              <div class="stat-content">
                <div class="stat-icon" style="background: #3370FF;">
                  <el-icon :size="32" color="#ffffff"><Document /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.total_topics }}</div>
                  <div class="stat-label">总选题数</div>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="6">
            <el-card class="stat-card" @click="router.push('/content')">
              <div class="stat-content">
                <div class="stat-icon" style="background: #00B365;">
                  <el-icon :size="32" color="#ffffff"><Edit /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.total_contents }}</div>
                  <div class="stat-label">内容总数</div>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="6">
            <el-card class="stat-card" @click="router.push('/images')">
              <div class="stat-content">
                <div class="stat-icon" style="background: #FF7D00;">
                  <el-icon :size="32" color="#ffffff"><Picture /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.total_images }}</div>
                  <div class="stat-label">图片总数</div>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="6">
            <el-card class="stat-card" @click="router.push('/publish')">
              <div class="stat-content">
                <div class="stat-icon" style="background: #F53F3F;">
                  <el-icon :size="32" color="#ffffff"><Share /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.published_count }}</div>
                  <div class="stat-label">已发布内容</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20" style="margin-top: 20px;">
          <!-- 最近活动 -->
          <el-col :span="16">
            <Card title="最近活动">
              <EmptyState
                v-if="!loading && stats.recent_activities.length === 0"
                text="暂无最近活动"
              />
              <div v-else class="activity-list">
                <div
                  v-for="activity in stats.recent_activities"
                  :key="`${activity.type}-${activity.ref_id}`"
                  class="activity-item"
                  @click="handleActivityClick(activity)"
                >
                  <div class="activity-icon" :class="`activity-${activity.type}`">
                    <el-icon :size="20">
                      <component :is="getActivityIcon(activity.type)" />
                    </el-icon>
                  </div>
                  <div class="activity-content">
                    <div class="activity-title">{{ activity.title }}</div>
                    <div class="activity-time">{{ formatActivityTime(activity.time) }}</div>
                  </div>
                </div>
              </div>
            </Card>
          </el-col>

          <!-- 快速操作 -->
          <el-col :span="8">
            <Card title="快速操作">
              <div class="quick-actions">
                <el-button
                  v-for="action in quickActions"
                  :key="action.key"
                  type="primary"
                  plain
                  style="width: 100%; margin-bottom: 12px;"
                  @click="handleAction(action)"
                >
                  <el-icon :size="16" style="margin-right: 8px;">
                    <component :is="action.icon" />
                  </el-icon>
                  {{ action.label }}
                </el-button>
              </div>
            </Card>
          </el-col>
        </el-row>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import Card from '@components/Card.vue'
import PageHeader from '@components/PageHeader.vue'
import EmptyState from '@components/EmptyState.vue'
import { dashboardApi } from '@services/api'
import type { DashboardStats, DashboardActivity, ActivityType } from '@services/api'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const router = useRouter()

const loading = ref(false)
const loadError = ref(false)
const errorMessage = ref('')

const stats = ref<DashboardStats>({
  total_topics: 0,
  total_contents: 0,
  total_images: 0,
  published_count: 0,
  recent_activities: []
})

const loadDashboard = async () => {
  loading.value = true
  loadError.value = false
  try {
    const result: any = await dashboardApi.stats()
    if (result?.data) {
      stats.value = result.data
    } else {
      throw new Error('返回数据格式异常，请稍后重试')
    }
  } catch (e: any) {
    loadError.value = true
    errorMessage.value = e?.message || '请检查网络连接或后端服务状态'
  } finally {
    loading.value = false
  }
}

const quickActions = [
  { key: 'new-topic', label: '生成选题', icon: 'LightBulb' },
  { key: 'new-content', label: '创建内容', icon: 'Edit' },
  { key: 'generate-images', label: '生成图片', icon: 'Picture' },
  { key: 'publish', label: '立即发布', icon: 'Share' }
]

const getActivityIcon = (type: ActivityType) => {
  const iconMap: Record<string, string> = {
    content: 'Edit',
    topic: 'Document',
    image: 'Picture',
    publish: 'Share'
  }
  return iconMap[type] || 'Bell'
}

const formatActivityTime = (time: string) => dayjs(time).fromNow()

// 最近活动：按活动类型跳转；图片/发布记录无独立详情页，回退到对应列表页
const handleActivityClick = (activity: DashboardActivity) => {
  switch (activity.type) {
    case 'topic':
      router.push(`/topic/detail/${activity.ref_id}`)
      break
    case 'content':
      router.push(`/content/detail/${activity.ref_id}`)
      break
    case 'image':
      router.push('/images')
      break
    case 'publish':
      router.push('/publish')
      break
  }
}

const handleAction = (action: { key: string }) => {
  switch (action.key) {
    case 'new-topic':
      router.push('/topics')
      break
    case 'new-content':
      router.push('/content/create')
      break
    case 'generate-images':
      router.push('/images')
      break
    case 'publish':
      router.push('/publish')
      break
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.stat-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(31, 35, 41, 0.12);
}

.error-card {
  margin-top: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1F2329;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #8F959E;
  margin-top: 2px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #F5F6F7;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}

.activity-item:hover {
  background: #E8EAED;
  transform: translateX(2px);
}

.activity-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.activity-icon.activity-content {
  background: #EFF4FF;
  color: #3370FF;
}

.activity-icon.activity-topic {
  background: #FFF7E8;
  color: #FF7D00;
}

.activity-icon.activity-image {
  background: #FFECE8;
  color: #F53F3F;
}

.activity-icon.activity-publish {
  background: #E8FFEA;
  color: #00B365;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: 13px;
  color: #1F2329;
  margin-bottom: 2px;
}

.activity-time {
  font-size: 12px;
  color: #8F959E;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
