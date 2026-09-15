<template>
  <div class="dashboard">
    <PageHeader title="仪表盘" />
    
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #3370FF;">
              <el-icon :size="32" color="#ffffff"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalTopics }}</div>
              <div class="stat-label">总选题数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #00B365;">
              <el-icon :size="32" color="#ffffff"><Edit /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalContents }}</div>
              <div class="stat-label">内容总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #FF7D00;">
              <el-icon :size="32" color="#ffffff"><Picture /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalImages }}</div>
              <div class="stat-label">图片总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #F53F3F;">
              <el-icon :size="32" color="#ffffff"><Share /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.publishedCount }}</div>
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
          <div class="activity-list">
            <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
              <div class="activity-icon" :class="`activity-${activity.type}`">
                <el-icon :size="20">
                  <component :is="getActivityIcon(activity.type)" />
                </el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-time">{{ activity.time }}</div>
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

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@components/Card.vue'
import PageHeader from '@components/PageHeader.vue'

const router = useRouter()

const stats = ref({
  totalTopics: 48,
  totalContents: 126,
  totalImages: 342,
  publishedCount: 89
})

const recentActivities = ref([
  { id: 1, type: 'content', title: '发布了新内容：AI 编程入门指南', time: '2小时前' },
  { id: 2, type: 'topic', title: '生成了新选题：大模型应用案例', time: '5小时前' },
  { id: 3, type: 'image', title: '生成了 3 张配图', time: '1天前' },
  { id: 4, type: 'publish', title: '发布到小红书：Python 自动化脚本', time: '2天前' }
])

const quickActions = ref([
  { key: 'new-topic', label: '生成选题', icon: 'LightBulb' },
  { key: 'new-content', label: '创建内容', icon: 'Edit' },
  { key: 'generate-images', label: '生成图片', icon: 'Picture' },
  { key: 'publish', label: '立即发布', icon: 'Share' }
])

const getActivityIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    content: 'Edit',
    topic: 'Document',
    image: 'Picture',
    publish: 'Share'
  }
  return iconMap[type] || 'Bell'
}

const handleAction = (action: any) => {
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
</script>

<style scoped>
.stat-card {
  margin-bottom: 20px;
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
  transition: background 0.2s;
}

.activity-item:hover {
  background: #F2F3F5;
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
